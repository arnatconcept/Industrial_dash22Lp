# notificaciones_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import NotificacionApp, DispositivoApp
from .serializers import NotificacionAppSerializer, DispositivoRequestSerializer
from .notification_service import NotificationService

class NotificacionesViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificacionAppSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotificacionApp.objects.filter(
            usuario_id=self.request.user.id
        ).order_by('-fecha_creacion')

    @action(detail=False, methods=['get'])
    def no_leidas(self, request):
        notificaciones = self.get_queryset().filter(leida=False)
        serializer = self.get_serializer(notificaciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def conteo_no_leidas(self, request):
        """Retorna el conteo de notificaciones no leídas para el usuario actual"""
        conteo = NotificacionApp.objects.filter(
            usuario_id=request.user.id,
            leida=False
        ).count()
        
        return Response({
            'conteo': conteo,
            'usuario_id': request.user.id,
            'usuario_nombre': request.user.get_full_name() or request.user.username
        })

    @action(detail=True, methods=['post'])
    def marcar_leida(self, request, pk=None):
        notificacion = self.get_object()
        if notificacion.usuario_id != request.user.id:
            return Response(
                {'error': 'No tiene permisos para esta notificación'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        notificacion.leida = True
        notificacion.fecha_lectura = timezone.now()
        notificacion.save()
        
        return Response({'status': 'success'})

    @action(detail=False, methods=['post'])
    def marcar_todas_leidas(self, request):
        NotificacionApp.objects.filter(
            usuario_id=request.user.id,
            leida=False
        ).update(
            leida=True,
            fecha_lectura=timezone.now()
        )
        
        return Response({'status': 'success'})

from rest_framework.views import APIView

class DispositivoView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = DispositivoRequestSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            # Crear o actualizar dispositivo
            dispositivo, created = DispositivoApp.objects.update_or_create(
                token_fcm=data['token_fcm'],
                defaults={
                    'usuario_id': request.user.id,
                    'usuario_nombre': request.user.get_full_name() or request.user.username,
                    'plataforma': data['plataforma'],
                    'version_app': data.get('version_app', ''),
                    'esta_activo': True
                }
            )
            
            return Response({
                'status': 'success',
                'dispositivo_id': dispositivo.id,
                'action': 'created' if created else 'updated'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)