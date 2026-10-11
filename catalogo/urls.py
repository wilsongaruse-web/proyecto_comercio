from django.urls import path,include
from . import views
from rest_framework import routers
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
	

app_name = 'catalogo'

router=routers.DefaultRouter()
router.register(r'catalogo',views.CatalogoViewSet)
urlpatterns = [
    path('', views.catalogo, name='catalogo'),
    path('registro/', views.registro_cliente, name='registro'),
    path('ingresar/', views.login_cliente, name='login'),
    path('salir/', views.logout_cliente, name='logout'),
    path('checkout/', views.checkout, name='checkout'),
    path('pedido/<int:venta_id>/', views.pedido_confirmado, name='pedido_confirmado'),
    path('api/', include(router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger/', SpectacularSwaggerView.as_view(url_name='catalogo:schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='catalogo:schema'), name='redoc'),
]