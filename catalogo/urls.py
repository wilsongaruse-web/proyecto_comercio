from django.urls import path,include
from . import views
from rest_framework import routers
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
	

app_name = 'catalogo'

router=routers.DefaultRouter()
router.register(r'catalogo',views.CatalogoViewSet)
urlpatterns = [
    path('', views.catalogo, name='catalogo'),
    path('api/', include(router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger/', SpectacularSwaggerView.as_view(url_name='catalogo:schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='catalogo:schema'), name='redoc'),
]