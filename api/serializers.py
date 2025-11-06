from rest_framework import serializers
from .models import ReunionDiaria, IncidenciaReunion, PlanificacionReunion, AccionReunion
from .models import *
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

class TurnoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Turno
        fields = '__all__'

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Agregar claims personalizados
        token['username'] = user.username
        token['role'] = user.role
        token['email'] = user.email

        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Agregar datos adicionales a la respuesta
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'role': self.user.role,
        }
        return data

@method_decorator(csrf_exempt, name='dispatch')
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    class Meta:
        model = User
        model = User
        fields = ['id', 'username', 'password', 'role', 'first_name', 'last_name', 'email', 'is_active']    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data.get('password'),
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=validated_data.get('role', 'tecnico')
        )
        return user

class LineaProduccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineaProduccion
        fields = '__all__'

class SectorSerializer(serializers.ModelSerializer):
    linea_nombre = serializers.CharField(source='linea.nombre', read_only=True)
    class Meta:
        model = Sector
        fields = '__all__'

class EquipoSerializer(serializers.ModelSerializer):
    sector_nombre = serializers.CharField(source='sector.nombre', read_only=True)
    linea_nombre = serializers.CharField(source='sector.linea.nombre', read_only=True)
    class Meta:
        model = Equipo
        fields = '__all__'

class DepositoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposito
        fields = '__all__'




class MotorSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    ubicacion_tipo_display = serializers.CharField(source='get_ubicacion_tipo_display', read_only=True)
    creado_por_nombre = serializers.CharField(source='creado_por.username', read_only=True)
    imagen_url = serializers.SerializerMethodField()
    plano_url = serializers.SerializerMethodField()
    equipo_nombre = serializers.CharField(source='equipo.nombre', read_only=True)
    sector_nombre = serializers.CharField(source='equipo.sector.nombre', read_only=True)
    linea_nombre = serializers.CharField(source='equipo.sector.linea.nombre', read_only=True)
    deposito_nombre = serializers.CharField(source='deposito.nombre', read_only=True)

    def get_imagen_url(self, obj):
        if obj.imagen:
            return self.context['request'].build_absolute_uri(obj.imagen.url)
        return None

    def get_plano_url(self, obj):
        if obj.ref_plano:
            return self.context['request'].build_absolute_uri(obj.ref_plano.url)
        return None

    def validate(self, data):
        """
        Llama a clean() para aplicar la validación de UbicacionBase.
        """
        # Si estás actualizando, pásale la instancia actual
        instance = Motor(**data)
        instance.clean()
        return data

    class Meta:
        model = Motor
        fields = '__all__'
        extra_kwargs = {'creado_por': {'read_only': True}}


class VariadorSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    ubicacion_tipo_display = serializers.CharField(source='get_ubicacion_tipo_display', read_only=True)
    creado_por_nombre = serializers.CharField(source='creado_por.username', read_only=True)
    imagen_url = serializers.SerializerMethodField()
    manual_url = serializers.SerializerMethodField()

    def get_imagen_url(self, obj):
        if obj.imagen:
            return self.context['request'].build_absolute_uri(obj.imagen.url)
        return None

    def get_manual_url(self, obj):
        if obj.manual:
            return self.context['request'].build_absolute_uri(obj.manual.url)
        return None

    class Meta:
        model = Variador
        fields = '__all__'
        extra_kwargs = {'creado_por': {'read_only': True}}

class OrdenMantenimientoSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
    creado_por_nombre = serializers.CharField(source='creado_por.username', read_only=True)
    operario_asignado_nombre = serializers.CharField(source='operario_asignado.username', read_only=True)
    

    equipos = serializers.PrimaryKeyRelatedField(
        queryset=Equipo.objects.all(), many=True, required=False
    )
    motores = serializers.PrimaryKeyRelatedField(
        queryset=Motor.objects.all(), many=True, required=False
    )
    variadores = serializers.PrimaryKeyRelatedField(
        queryset=Variador.objects.all(), many=True, required=False
    )

    equipos_info = EquipoSerializer(source='equipos', many=True, read_only=True)
    motores_info = MotorSerializer(source='motores', many=True, read_only=True)
    variadores_info = VariadorSerializer(source='variadores', many=True, read_only=True)

    linea_info = serializers.SerializerMethodField()
    sector_info = serializers.SerializerMethodField()

    def get_linea_info(self, obj):
        # Obtener línea del primer equipo asociado (prioridad: Equipo > Motor > Variador)
        if obj.equipos.exists():
            equipo = obj.equipos.first()
            return {
                'id': equipo.sector.linea.id,
                'nombre': equipo.sector.linea.nombre
            }
        elif obj.motores.exists():
            motor = obj.motores.first()
            if motor.linea:
                return {
                    'id': motor.linea.id,
                    'nombre': motor.linea.nombre
                }
        elif obj.variadores.exists():
            variador = obj.variadores.first()
            if variador.linea:
                return {
                    'id': variador.linea.id,
                    'nombre': variador.linea.nombre
                }
        return None

    def get_sector_info(self, obj):
        # Obtener sector del primer equipo asociado
        if obj.equipos.exists():
            equipo = obj.equipos.first()
            return {
                'id': equipo.sector.id,
                'nombre': equipo.sector.nombre,
                'linea_id': equipo.sector.linea.id,
                'linea_nombre': equipo.sector.linea.nombre
            }
        elif obj.motores.exists():
            motor = obj.motores.first()
            if motor.sector:
                return {
                    'id': motor.sector.id,
                    'nombre': motor.sector.nombre,
                    'linea_id': motor.sector.linea.id,
                    'linea_nombre': motor.sector.linea.nombre
                }
        elif obj.variadores.exists():
            variador = obj.variadores.first()
            if variador.sector:
                return {
                    'id': variador.sector.id,
                    'nombre': variador.sector.nombre,
                    'linea_id': variador.sector.linea.id,
                    'linea_nombre': variador.sector.linea.nombre
                }
        return None

    class Meta:
        model = OrdenMantenimiento
        fields = '__all__'
        extra_kwargs = {'creado_por': {'read_only': True}}

class PLCSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    ubicacion_nombre = serializers.CharField(source='ubicacion.nombre', read_only=True)
    diagrama_url = serializers.SerializerMethodField()

    def get_diagrama_url(self, obj):
        if obj.diagrama:
            return self.context['request'].build_absolute_uri(obj.diagrama.url)
        return None

    class Meta:
        model = PLC
        fields = '__all__'
        extra_kwargs = {'creado_por': {'read_only': True}}

class PLCEntradaSalidaSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    plc_nombre = serializers.CharField(source='plc.nombre', read_only=True)

    class Meta:
        model = PLCEntradaSalida
        fields = '__all__'
        read_only_fields = ['fecha_actualizacion', 'historico']

class PLCLogSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
    entrada_salida_etiqueta = serializers.CharField(source='entrada_salida.etiqueta', read_only=True)

    class Meta:
        model = PLCLog
        fields = '__all__'
        read_only_fields = ['fecha']


class HistorialCambioOrdenSerializer(serializers.ModelSerializer):
    orden_id = serializers.IntegerField(write_only=True)  # Eliminado source='orden'
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
    
    class Meta:
        model = HistorialCambioOrden
        fields = [
            'id', 'orden_id', 'usuario', 'fecha_cambio', 'tipo_cambio',
            'campo_afectado', 'valor_anterior', 'valor_nuevo',
            'equipo_tipo', 'equipo_id', 'imagen_url', 'usuario_nombre'
        ]
        read_only_fields = ('fecha_cambio', 'usuario')

    def create(self, validated_data):
        # Mapeo manual de orden_id a orden
        orden_id = validated_data.pop('orden_id')
        validated_data['orden'] = OrdenMantenimiento.objects.get(id=orden_id)
        return super().create(validated_data)

class HistorialMantenimientoSerializer(serializers.ModelSerializer):
    tipo_evento_display = serializers.CharField(source='get_tipo_evento_display', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = HistorialMantenimiento
        fields = '__all__'

class BusquedaGlobalSerializer(serializers.Serializer):
    termino = serializers.CharField(max_length=100)

class ProveedorSerializer(serializers.ModelSerializer):
    reparaciones = serializers.SerializerMethodField()
    especialidad_display = serializers.CharField(source='get_especialidad_display', read_only=True)
    
    class Meta:
        model = Proveedor
        fields = [
            'id',
            'nombre',
            'especialidad',
            'especialidad_display',
            'contacto',
            'telefono',
            'email',
            'reparaciones',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_reparaciones(self, obj):
        reparaciones = obj.reparacion_set.all().values(
            'id',
            'equipo_tipo',
            'equipo_id',
            'tipo',
            'fecha_inicio',
            'fecha_fin'
        )
        return reparaciones
    
class ReparacionSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    proveedor_info = serializers.SerializerMethodField()
    equipo_info = serializers.SerializerMethodField()
    documento_url = serializers.SerializerMethodField()
    duracion_dias = serializers.SerializerMethodField()
    creado_por_nombre = serializers.CharField(source='creado_por.username', read_only=True)
    
    class Meta:
        model = Reparacion
        fields = [
            'id',
            'equipo_tipo',
            'equipo_id',
            'equipo_info',
            'tipo',
            'tipo_display',
            'fecha_inicio',
            'fecha_fin',
            'duracion_dias',
            'descripcion',
            'costo',
            'proveedor',
            'proveedor_info',
            'documento',
            'documento_url',
            'creado_por',
            'creado_por_nombre',
            'created_at',
            'updated_at'
        ]
        extra_kwargs = {
            'creado_por': {'read_only': True},
            'documento': {'required': False}
        }

    def get_proveedor_info(self, obj):
        if obj.proveedor:
            return {
                'id': obj.proveedor.id,
                'nombre': obj.proveedor.nombre,
                'especialidad': obj.proveedor.get_especialidad_display()
            }
        return None

    def get_equipo_info(self, obj):
        try:
            if obj.equipo_tipo == 'motor':
                equipo = Motor.objects.get(pk=obj.equipo_id)
                return {
                    'codigo': equipo.codigo,
                    'tipo': equipo.tipo,
                    'ubicacion': equipo.get_ubicacion_tipo_display()
                }
            elif obj.equipo_tipo == 'variador':
                equipo = Variador.objects.get(pk=obj.equipo_id)
                return {
                    'codigo': equipo.codigo,
                    'modelo': f"{equipo.marca} {equipo.modelo}",
                    'ubicacion': equipo.get_ubicacion_tipo_display()
                }
        except:
            return None
        return None

    def get_documento_url(self, obj):
        if obj.documento:
            return self.context['request'].build_absolute_uri(obj.documento.url)
        return None

    def get_duracion_dias(self, obj):
        if obj.fecha_inicio and obj.fecha_fin:
            return (obj.fecha_fin - obj.fecha_inicio).days
        return None

    def validate(self, data):
        if data.get('fecha_fin') and data['fecha_fin'] < data['fecha_inicio']:
            raise serializers.ValidationError("La fecha de fin no puede ser anterior a la de inicio")
        
        if data['tipo'] == 'preventivo' and not data.get('proveedor'):
            raise serializers.ValidationError("Las reparaciones preventivas requieren proveedor")
            
        return data
    
class OrdenMantenimientoSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
    creado_por_nombre = serializers.CharField(source='creado_por.username', read_only=True)
    operario_asignado_nombre = serializers.CharField(source='operario_asignado.username', read_only=True)
    

    equipos = serializers.PrimaryKeyRelatedField(
        queryset=Equipo.objects.all(), many=True, required=False
    )
    motores = serializers.PrimaryKeyRelatedField(
        queryset=Motor.objects.all(), many=True, required=False
    )
    variadores = serializers.PrimaryKeyRelatedField(
        queryset=Variador.objects.all(), many=True, required=False
    )

    equipos_info = EquipoSerializer(source='equipos', many=True, read_only=True)
    motores_info = MotorSerializer(source='motores', many=True, read_only=True)
    variadores_info = VariadorSerializer(source='variadores', many=True, read_only=True)

    linea_info = serializers.SerializerMethodField()
    sector_info = serializers.SerializerMethodField()

    def get_linea_info(self, obj):
        # Obtener línea del primer equipo asociado (prioridad: Equipo > Motor > Variador)
        if obj.equipos.exists():
            equipo = obj.equipos.first()
            return {
                'id': equipo.sector.linea.id,
                'nombre': equipo.sector.linea.nombre
            }
        elif obj.motores.exists():
            motor = obj.motores.first()
            if motor.linea:
                return {
                    'id': motor.linea.id,
                    'nombre': motor.linea.nombre
                }
        elif obj.variadores.exists():
            variador = obj.variadores.first()
            if variador.linea:
                return {
                    'id': variador.linea.id,
                    'nombre': variador.linea.nombre
                }
        return None

    def get_sector_info(self, obj):
        # Obtener sector del primer equipo asociado
        if obj.equipos.exists():
            equipo = obj.equipos.first()
            return {
                'id': equipo.sector.id,
                'nombre': equipo.sector.nombre,
                'linea_id': equipo.sector.linea.id,
                'linea_nombre': equipo.sector.linea.nombre
            }
        elif obj.motores.exists():
            motor = obj.motores.first()
            if motor.sector:
                return {
                    'id': motor.sector.id,
                    'nombre': motor.sector.nombre,
                    'linea_id': motor.sector.linea.id,
                    'linea_nombre': motor.sector.linea.nombre
                }
        elif obj.variadores.exists():
            variador = obj.variadores.first()
            if variador.sector:
                return {
                    'id': variador.sector.id,
                    'nombre': variador.sector.nombre,
                    'linea_id': variador.sector.linea.id,
                    'linea_nombre': variador.sector.linea.nombre
                }
        return None

    class Meta:
        model = OrdenMantenimiento
        fields = '__all__'
        extra_kwargs = {'creado_por': {'read_only': True}}
    
class EventoSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    usuario_info = serializers.SerializerMethodField()
    objeto_info = serializers.SerializerMethodField()
    fecha_formateada = serializers.SerializerMethodField()
    
    class Meta:
        model = Evento
        fields = [
            'id',
            'tipo',
            'tipo_display',
            'descripcion',
            'fecha',
            'fecha_formateada',
            'usuario',
            'usuario_info',
            'objeto_id',
            'objeto_info'
        ]
        read_only_fields = ['fecha', 'usuario']

    def get_usuario_info(self, obj):
        return {
            'id': obj.usuario.id,
            'username': obj.usuario.username,
            'nombre_completo': f"{obj.usuario.first_name} {obj.usuario.last_name}",
            'rol': obj.usuario.get_role_display()
        }

    def get_objeto_info(self, obj):
        try:
            if obj.tipo == 'motor':
                motor = Motor.objects.get(pk=obj.objeto_id)
                return {
                    'codigo': motor.codigo,
                    'tipo': motor.tipo,
                    'estado': motor.get_estado_display()
                }
            elif obj.tipo == 'variador':
                variador = Variador.objects.get(pk=obj.objeto_id)
                return {
                    'codigo': variador.codigo,
                    'modelo': f"{variador.marca} {variador.modelo}",
                    'estado': variador.get_estado_display()
                }
            elif obj.tipo == 'orden':
                orden = OrdenMantenimiento.objects.get(pk=obj.objeto_id)
                return {
                    'titulo': orden.titulo,
                    'estado': orden.get_estado_display(),
                    'prioridad': orden.get_prioridad_display()
                }
            elif obj.tipo == 'reparacion':
                reparacion = Reparacion.objects.get(pk=obj.objeto_id)
                return {
                    'tipo': reparacion.get_tipo_display(),
                    'equipo': f"{reparacion.equipo_tipo} #{reparacion.equipo_id}",
                    'fecha': reparacion.fecha_inicio
                }
        except:
            return None
        return None

    def get_fecha_formateada(self, obj):
        return obj.fecha.strftime("%d/%m/%Y %H:%M")

    def create(self, validated_data):
        # Asignar automáticamente el usuario actual
        validated_data['usuario'] = self.context['request'].user
        return super().create(validated_data)
    
class VariableInspeccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariableInspeccion
        fields = '__all__'
        read_only_fields = ['created_at']



class ResultadoInspeccionSerializer(serializers.ModelSerializer):
    variable_info = VariableInspeccionSerializer(source='variable', read_only=True)
    ejecucion_id = serializers.PrimaryKeyRelatedField(
        queryset=InspeccionEjecucion.objects.all(),
        source='ejecucion',  # Se asigna al campo real del modelo
        write_only=True
    )
    fecha_formateada = serializers.SerializerMethodField()

    class Meta:
        model = ResultadoInspeccion
        fields = [
            'id',
            'ejecucion_id',        # Incluido en el JSON que recibe
            'ejecucion',           # Para lectura (puede omitirse si no lo usás)
            'variable',
            'variable_info',
            'valor_medido',
            'fecha',
            'fecha_formateada'
        ]
        read_only_fields = ['fecha', 'ejecucion']  # Marcar solo como lectura si es necesario
    def get_fecha_formateada(self, obj):
        return obj.fecha.strftime("%d/%m/%Y %H:%M")
class ResultadoInspeccionSerializer(serializers.ModelSerializer):
    variable_info = VariableInspeccionSerializer(source='variable', read_only=True)
    ejecucion_id = serializers.PrimaryKeyRelatedField(
        queryset=InspeccionEjecucion.objects.all(),
        source='ejecucion',
        write_only=True
    )
    fecha_formateada = serializers.SerializerMethodField()
    tecnico_info = serializers.SerializerMethodField()
    ejecucion_fecha = serializers.SerializerMethodField()

    class Meta:
        model = ResultadoInspeccion
        fields = [
            'id',
            'ejecucion_id',
            'ejecucion',        # Para lectura interna
            'variable',
            'variable_info',
            'valor_medido',
            'fecha',
            'fecha_formateada',
            'tecnico_info',     # 👈 Nuevo campo
            'ejecucion_fecha'   # 👈 Nuevo campo
        ]
        read_only_fields = ['fecha', 'ejecucion']

    def get_fecha_formateada(self, obj):
        return obj.fecha.strftime("%d/%m/%Y %H:%M")

    def get_tecnico_info(self, obj):
        tecnico = obj.ejecucion.tecnico
        if tecnico:
            return {
                'id': tecnico.id,
                'username': tecnico.username,
                'nombre': f"{tecnico.first_name} {tecnico.last_name}"
            }
        return None

    def get_ejecucion_fecha(self, obj):
        return obj.ejecucion.fecha.strftime("%d/%m/%Y %H:%M") if obj.ejecucion.fecha else None



class InspeccionEjecucionSerializer(serializers.ModelSerializer):
    ruta_info = serializers.SerializerMethodField()
    tecnico_info = serializers.SerializerMethodField()
    resultados = ResultadoInspeccionSerializer(many=True, read_only=True)

    class Meta:
        model = InspeccionEjecucion
        fields = [
            'id',
            'ruta',
            'ruta_info',
            'tecnico',
            'tecnico_info',
            'fecha',
            'observaciones',
            'resultados'
        ]
        read_only_fields = ['fecha', 'tecnico']

    def get_ruta_info(self, obj):
        return {
            'id': obj.ruta.id,
            'nombre': obj.ruta.nombre,
            'activo_tipo': obj.ruta.activo_tipo,
            'activo_id': obj.ruta.activo_id
        }

    def get_tecnico_info(self, obj):
        if obj.tecnico:
            return {
                'id': obj.tecnico.id,
                'username': obj.tecnico.username,
                'nombre': f"{obj.tecnico.first_name} {obj.tecnico.last_name}"
            }
        return None

    def create(self, validated_data):
        # Setea el técnico automáticamente
        validated_data['tecnico'] = self.context['request'].user
        return super().create(validated_data)


class RutaInspeccionSerializer(serializers.ModelSerializer):
    variables = VariableInspeccionSerializer(many=True, read_only=True)
    creado_por_nombre = serializers.CharField(source='creado_por.username', read_only=True)

    class Meta:
        model = RutaInspeccion
        fields = [
            'id',
            'nombre',
            'descripcion',
            'activo_tipo',
            'activo_id',
            'frecuencia_dias',
            'creado_por',
            'creado_por_nombre',
            'created_at',
            'variables'
        ]
        read_only_fields = ['creado_por', 'created_at']

    def create(self, validated_data):
        validated_data['creado_por'] = self.context['request'].user
        return super().create(validated_data)

class KpiInspeccionesResponseSerializer(serializers.Serializer):
    rutas_totales = serializers.IntegerField()
    ejecuciones_7d = serializers.IntegerField()
    tiempo_promedio = serializers.FloatField()


class NotificacionAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificacionApp
        fields = [
            'id', 'titulo', 'mensaje', 'tipo', 'prioridad', 
            'leida', 'fecha_creacion', 'fecha_lectura',
            'data_adicional', 'relacion_id', 'relacion_tipo'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_lectura']


class DispositivoRequestSerializer(serializers.Serializer):
    token_fcm = serializers.CharField(max_length=255)
    plataforma = serializers.CharField(max_length=20)
    version_app = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_plataforma(self, value):
        if value not in ['android', 'ios']:
            raise serializers.ValidationError("Plataforma debe ser 'android' o 'ios'")
        return value


class ReunionDiariaSerializer(serializers.ModelSerializer):
    creada_por_nombre = serializers.CharField(source='creada_por.get_full_name', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    incidencias_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ReunionDiaria
        fields = '__all__'
        read_only_fields = ('creada_por', 'creada_en')
    
    def get_incidencias_count(self, obj):
        return obj.incidencias.count()


class IncidenciaReunionSerializer(serializers.ModelSerializer):
    reunion_fecha = serializers.DateField(source='reunion.fecha', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
    reportada_por_nombre = serializers.CharField(source='reportada_por.get_full_name', read_only=True)
    equipo_nombre = serializers.CharField(source='equipo_relacionado.nombre', read_only=True)
    orden_mantenimiento_titulo = serializers.CharField(source='orden_mantenimiento.titulo', read_only=True)
    acciones_count = serializers.SerializerMethodField()
    
    class Meta:
        model = IncidenciaReunion
        fields = '__all__'
        read_only_fields = ('reportada_por', 'creada_en')
    
    def get_acciones_count(self, obj):
        return obj.acciones.count()


class PlanificacionReunionSerializer(serializers.ModelSerializer):
    reunion_fecha = serializers.DateField(source='reunion.fecha', read_only=True)
    responsable_nombre = serializers.CharField(source='responsable.get_full_name', read_only=True)
    equipo_nombre = serializers.CharField(source='equipo_relacionado.nombre', read_only=True)
    orden_mantenimiento_titulo = serializers.CharField(source='orden_mantenimiento.titulo', read_only=True)
    
    class Meta:
        model = PlanificacionReunion
        fields = '__all__'
        read_only_fields = ('creada_en',)


class AccionReunionSerializer(serializers.ModelSerializer):
    incidencia_descripcion = serializers.CharField(source='incidencia.descripcion', read_only=True)
    asignada_a_nombre = serializers.CharField(source='asignada_a.get_full_name', read_only=True)
    orden_mantenimiento_titulo = serializers.CharField(source='orden_mantenimiento.titulo', read_only=True)
    
    class Meta:
        model = AccionReunion
        fields = '__all__'
        read_only_fields = ('creada_en',)


# For nested representations
class IncidenciaReunionNestedSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
    reportada_por_nombre = serializers.CharField(source='reportada_por.get_full_name', read_only=True)
    equipo_nombre = serializers.CharField(source='equipo_relacionado.nombre', read_only=True)
    acciones = AccionReunionSerializer(many=True, read_only=True)
    
    class Meta:
        model = IncidenciaReunion
        exclude = ('reunion',)


class ReunionDiariaDetailSerializer(ReunionDiariaSerializer):
    incidencias = IncidenciaReunionNestedSerializer(many=True, read_only=True)
    planificaciones = PlanificacionReunionSerializer(many=True, read_only=True)


class ProduccionTurnoSerializer(serializers.ModelSerializer):
    turno_nombre = serializers.CharField(source='turno.nombre', read_only=True)
    linea_nombre = serializers.CharField(source='linea.nombre', read_only=True)
    
    class Meta:
        model = ProduccionTurno
        fields = '__all__'
        read_only_fields = ('creado_por', 'fecha_creacion', 'fecha_actualizacion', 'eficiencia')

class FallaTurnoSerializer(serializers.ModelSerializer):
    turno_nombre = serializers.CharField(source='turno.nombre', read_only=True)
    linea_nombre = serializers.CharField(source='linea.nombre', read_only=True)
    equipo_nombre = serializers.CharField(source='equipo.nombre', read_only=True, allow_null=True)
    
    class Meta:
        model = FallaTurno
        fields = '__all__'
        read_only_fields = ('creado_por', 'fecha_creacion', 'fecha_actualizacion')

class ParadaTurnoSerializer(serializers.ModelSerializer):
    turno_nombre = serializers.CharField(source='turno.nombre', read_only=True)
    linea_nombre = serializers.CharField(source='linea.nombre', read_only=True)
    equipo_nombre = serializers.CharField(source='equipo.nombre', read_only=True, allow_null=True)
    
    class Meta:
        model = ParadaTurno
        fields = '__all__'
        read_only_fields = ('creado_por', 'fecha_creacion', 'fecha_actualizacion')

class NodeRedLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NodeRedLog
        fields = '__all__'
        read_only_fields = ('fecha_recepcion',)

class ProduccionSerializer(serializers.ModelSerializer):
    linea_nombre = serializers.CharField(source='linea.nombre', read_only=True)
    turno_nombre = serializers.CharField(source='turno.nombre', read_only=True)
    supervisor_username = serializers.CharField(source='supervisor.username', read_only=True)

    class Meta:
        model = Produccion
        fields = [
            'id', 'fecha', 'turno', 'turno_nombre', 'linea', 'linea_nombre', 
            'supervisor', 'supervisor_username', 'producto', 'bandejas',
            'fabricacion_toneladas', 'fabricacion_scrap', 'apilado_vagones',
            'apilado_toneladas', 'coccion_vagones', 'coccion_toneladas',
            'desapilado_primera', 'desapilado_segunda', 'desapilado_toneladas',
            'meta_produccion', 'eficiencia', 'fecha_creacion', 'fuente_dato'
        ]


class ProduccionTiempoRealSerializer(serializers.ModelSerializer):
    linea_nombre = serializers.CharField(source='linea.nombre', read_only=True)
    turno_nombre = serializers.CharField(source='turno.nombre', read_only=True)
    supervisor_username = serializers.CharField(source='supervisor.username', read_only=True)
    hora = serializers.SerializerMethodField()  # Campo adicional para hora

    class Meta:
        model = ProduccionTiempoReal
        fields = [
            'id', 'timestamp', 'fecha', 'hora', 'turno', 'turno_nombre', 
            'linea', 'linea_nombre', 'supervisor', 'supervisor_username', 
            'producto', 'bandejas', 'fabricacion_toneladas', 'fabricacion_scrap',
            'apilado_vagones', 'apilado_toneladas', 'coccion_vagones', 
            'coccion_toneladas', 'desapilado_primera', 'desapilado_segunda',
            'desapilado_toneladas', 'meta_produccion', 'eficiencia', 
            'fecha_creacion', 'fuente_dato', 'es_cierre_turno'
        ]

    def get_hora(self, obj):
        return obj.timestamp.time() if obj.timestamp else None

class NodeRedProduccionSerializer(serializers.Serializer):
    fecha = serializers.DateField()
    turno_id = serializers.IntegerField()
    linea_id = serializers.IntegerField()
    cantidad = serializers.IntegerField(min_value=0)
    unidad = serializers.CharField(required=False, default="unidades")
    meta_produccion = serializers.IntegerField(min_value=0, required=False, allow_null=True)

class NodeRedFallaSerializer(serializers.Serializer):
    fecha = serializers.DateField()
    turno_id = serializers.IntegerField()
    linea_id = serializers.IntegerField()
    equipo_id = serializers.IntegerField(required=False, allow_null=True)
    tipo = serializers.CharField()
    gravedad = serializers.CharField(required=False, default="moderada")
    cantidad = serializers.IntegerField(min_value=0)
    duracion_minutos = serializers.IntegerField(min_value=0, default=0)
    descripcion = serializers.CharField(required=False, allow_blank=True)
    accion_correctiva = serializers.CharField(required=False, allow_blank=True, default="")

class NodeRedParadaSerializer(serializers.Serializer):
    fecha = serializers.DateField()
    turno_id = serializers.IntegerField()
    linea_id = serializers.IntegerField()
    equipo_id = serializers.IntegerField(required=False, allow_null=True)
    motivo = serializers.CharField()
    tipo = serializers.CharField(required=False, default="no_programada")
    duracion_minutos = serializers.IntegerField(min_value=0)
    descripcion = serializers.CharField(required=False, allow_blank=True)
