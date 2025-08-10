from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Q
from .models import *

# ---------------------- #
# Filtros personalizados #
# ---------------------- #

class LineaProduccionFilter(admin.SimpleListFilter):
    title = 'Línea'
    parameter_name = 'linea'

    def lookups(self, request, model_admin):
        return [(str(lp.id), lp.nombre) for lp in LineaProduccion.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                Q(equipos__sector__linea_id=self.value()) |
                Q(motores__linea_id=self.value()) |
                Q(variadores__linea_id=self.value())
            ).distinct()
        return queryset


class SectorFilter(admin.SimpleListFilter):
    title = 'Sector'
    parameter_name = 'sector'

    def lookups(self, request, model_admin):
        sectores = Sector.objects.select_related('linea').all()
        return [(str(s.id), f"{s.linea.nombre} - {s.nombre}") for s in sectores]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                Q(equipos__sector_id=self.value()) |
                Q(motores__sector_id=self.value()) |
                Q(variadores__sector_id=self.value())
            ).distinct()
        return queryset

# ---------------------- #
# ModelAdmins            #
# ---------------------- #

class UserAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if obj.is_superuser:
            obj.role = 'admin'
        super().save_model(request, obj, form, change)


class LineaProduccionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)


class SectorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'linea')
    list_filter = ('linea',)
    search_fields = ('nombre', 'linea__nombre')


class EquipoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'sector', 'get_linea')
    list_filter = ('sector__linea', 'sector')
    search_fields = ('nombre', 'sector__nombre')

    def get_linea(self, obj):
        return obj.sector.linea.nombre
    get_linea.short_description = 'Línea'


class DepositoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ubicacion')
    search_fields = ('nombre', 'ubicacion')


class MotorAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'potencia', 'tipo', 'estado', 'ubicacion_tipo', 'linea', 'sector', 'equipo', 'deposito')
    list_filter = ('estado', 'ubicacion_tipo', 'linea', 'sector')
    search_fields = ('codigo', 'tipo')
    readonly_fields = ('creado_por',)


class VariadorAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'marca', 'modelo', 'potencia', 'estado', 'ubicacion_tipo', 'linea', 'sector', 'equipo', 'deposito')
    list_filter = ('estado', 'ubicacion_tipo', 'linea', 'sector')
    search_fields = ('codigo', 'marca', 'modelo')
    readonly_fields = ('creado_por',)


class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'especialidad', 'contacto', 'telefono', 'email')
    search_fields = ('nombre', 'especialidad')


class ReparacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'equipo_tipo', 'equipo_id', 'tipo', 'fecha_inicio', 'fecha_fin', 'proveedor')
    list_filter = ('tipo', 'proveedor')
    search_fields = ('descripcion',)


class OrdenMantenimientoAdmin(admin.ModelAdmin):
    list_display = (
        'titulo', 'tipo', 'prioridad', 'estado',
        'fecha_creacion', 'fecha_cierre', 'creado_por',
        'ubicacion_info', 'ver_ordenes_mobile'
    )
    list_filter = (
        'tipo',
        'prioridad',
        'estado',
        LineaProduccionFilter,
        SectorFilter,
        ('equipos', admin.RelatedOnlyFieldListFilter),
        ('motores', admin.RelatedOnlyFieldListFilter),
        ('variadores', admin.RelatedOnlyFieldListFilter),
    )
    search_fields = (
        'titulo', 'descripcion',
        'equipos__nombre', 'motores__codigo', 'variadores__codigo',
        'equipos__sector__linea__nombre', 'equipos__sector__nombre'
    )
    readonly_fields = ('fecha_creacion', 'creado_por', 'ubicacion_info_detallada')

    fieldsets = (
        ('Información Básica', {
            'fields': ('titulo', 'descripcion', 'tipo', 'prioridad', 'estado')
        }),
        ('Asignación', {
            'fields': ('operario_asignado', 'creado_por', 'fecha_creacion', 'fecha_cierre')
        }),
        ('Tiempos y Checklist', {
            'fields': ('tiempo_estimado', 'tiempo_real', 'checklist')
        }),
        ('Equipos Asociados', {
            'fields': ('equipos', 'motores', 'variadores')
        }),
        ('Información de Ubicación', {
            'fields': ('ubicacion_info_detallada',)
        }),
    )

    def ubicacion_info(self, obj):
        items = []
        if obj.equipos.exists():
            items.append(f"{obj.equipos.count()} equipo(s)")
        if obj.motores.exists():
            items.append(f"{obj.motores.count()} motor(es)")
        if obj.variadores.exists():
            items.append(f"{obj.variadores.count()} variador(es)")
        return ", ".join(items) if items else "Sin equipos"
    ubicacion_info.short_description = "Equipos Asociados"

    def ubicacion_info_detallada(self, obj):
        info = []
        for equipo in obj.equipos.all()[:5]:
            info.append(f"Equipo: {equipo.nombre} (Sector: {equipo.sector}, Línea: {equipo.sector.linea})")
        for motor in obj.motores.all()[:5]:
            location = "En línea" if motor.ubicacion_tipo == 'linea' else "En depósito" if motor.ubicacion_tipo == 'deposito' else "En taller"
            info.append(f"Motor: {motor.codigo} - {location} (Sector: {motor.sector}, Línea: {motor.linea})")
        for variador in obj.variadores.all()[:5]:
            location = "En línea" if variador.ubicacion_tipo == 'linea' else "En depósito" if variador.ubicacion_tipo == 'deposito' else "En taller"
            info.append(f"Variador: {variador.codigo} - {location} (Sector: {variador.sector}, Línea: {variador.linea})")
        return format_html("<br>".join(info)) if info else "No hay equipos asociados"
    ubicacion_info_detallada.short_description = "Detalle de Ubicaciones"

    def ver_ordenes_mobile(self, obj):
        return format_html('<a href="/mobile/mis-ordenes/" target="_blank">Ver en mobile</a>')
    ver_ordenes_mobile.short_description = "Vista Mobile"

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)


class HistorialMantenimientoAdmin(admin.ModelAdmin):
    list_display = ('equipo_tipo', 'equipo_id', 'tipo_evento', 'fecha', 'usuario')
    list_filter = ('equipo_tipo', 'tipo_evento')
    search_fields = ('descripcion',)


class EventoAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'descripcion', 'fecha', 'usuario')
    list_filter = ('tipo',)
    search_fields = ('descripcion',)


class RutaInspeccionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo_tipo', 'activo_id', 'frecuencia_dias', 'creado_por', 'created_at')
    search_fields = ('nombre', 'activo_tipo', 'activo_id')
    list_filter = ('activo_tipo', 'creado_por')


class VariableInspeccionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ruta', 'unidad', 'valor_referencia', 'tolerancia', 'created_at')
    search_fields = ('nombre', 'ruta__nombre')
    list_filter = ('ruta',)


class InspeccionEjecucionAdmin(admin.ModelAdmin):
    list_display = ('ruta', 'tecnico', 'fecha')
    list_filter = ('ruta', 'tecnico')
    search_fields = ('ruta__nombre', 'tecnico__username')


class ResultadoInspeccionAdmin(admin.ModelAdmin):
    list_display = ('ejecucion', 'variable', 'valor_medido', 'fecha')
    search_fields = ('variable__nombre', 'ejecucion__ruta__nombre')
    list_filter = ('variable',)
