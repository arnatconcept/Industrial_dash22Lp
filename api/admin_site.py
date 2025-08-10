from django.contrib.admin import AdminSite

class AutoTaskAdminSite(AdminSite):
    # Textos de marca que verás en el admin
    site_header = "Autotask — Panel de Mantenimiento"
    site_title = "Autotask Admin"
    index_title = "Gestión centralizada de equipos y órdenes"
