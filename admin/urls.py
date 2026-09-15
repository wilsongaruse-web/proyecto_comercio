from django.urls import path

from . import views

app_name = "admin"

urlpatterns = [
    path("", views.admin_panel, name="admin_panel"),
    path("login/", views.admin_login, name="login"),
    path("logout/", views.admin_logout, name="logout"),
    path("usuarios/nuevo/", views.usuario_nuevo, name="usuario_nuevo"),
    path("productos/", views.productos_admin, name="productos_admin"),
    path("productos/nuevo/", views.producto_nuevo, name="producto_nuevo"),
    path("productos/<int:producto_id>/editar/", views.producto_editar, name="producto_editar"),
    path("productos/<int:producto_id>/eliminar/", views.producto_eliminar, name="producto_eliminar"),
    path("ofertas/", views.ofertas_admin, name="ofertas_admin"),
    
]
