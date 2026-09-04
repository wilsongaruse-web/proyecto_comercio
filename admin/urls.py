from django.urls import path

#app registro
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

###################################
app_name = "admin"

urlpatterns = [
    path("", views.admin_panel, name="admin_panel"),
    path("login/", views.admin_login, name="login"),
    path("productos/", views.productos_admin, name="productos_admin"),
    path("productos/nuevo/", views.producto_nuevo, name="producto_nuevo"),
    path("productos/<int:producto_id>/editar/", views.producto_editar, name="producto_editar"),
    path("productos/<int:producto_id>/eliminar/", views.producto_eliminar, name="producto_eliminar"),
    path('admin/', admin.site.urls),
    # ... otras rutas
    
    
]
