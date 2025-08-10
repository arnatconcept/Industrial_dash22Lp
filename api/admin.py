from .admin_site import AutoTaskAdminSite
from .models import *
from .admin_config import *

# Crear la instancia del admin personalizado
custom_admin_site = AutoTaskAdminSite(name='autotask_admin')

# Registrar todos los modelos con sus ModelAdmins
custom_admin_site.register(User, UserAdmin)
custom_admin_site.register(LineaProduccion, LineaProduccionAdmin)
custom_admin_site.register(Sector, SectorAdmin)
custom_admin_site.register(Equipo, EquipoAdmin)
custom_admin_site.register(Deposito, DepositoAdmin)
custom_admin_site.register(Motor, MotorAdmin)
custom_admin_site.register(Variador, VariadorAdmin)
custom_admin_site.register(Proveedor, ProveedorAdmin)
custom_admin_site.register(Reparacion, ReparacionAdmin)
custom_admin_site.register(OrdenMantenimiento, OrdenMantenimientoAdmin)
custom_admin_site.register(HistorialMantenimiento, HistorialMantenimientoAdmin)
custom_admin_site.register(Evento, EventoAdmin)
custom_admin_site.register(RutaInspeccion, RutaInspeccionAdmin)
custom_admin_site.register(VariableInspeccion, VariableInspeccionAdmin)
custom_admin_site.register(InspeccionEjecucion, InspeccionEjecucionAdmin)
custom_admin_site.register(ResultadoInspeccion, ResultadoInspeccionAdmin)
