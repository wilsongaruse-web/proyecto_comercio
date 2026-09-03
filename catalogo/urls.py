from django.urls import path
from . import views

app_name = 'catalogo'

urlpatterns = [
    path('', views.catalogo, name='catalogo'),
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('eliminar/<int:item_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
]