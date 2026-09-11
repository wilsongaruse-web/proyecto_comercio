from django.urls import path,include
from . import views
from rest_framework import routers	

app_name = 'catalogo'

router=routers.DefaultRouter()
router.register(r'catalogo',views.CatalogoViewSet)
urlpatterns = [
    path('', views.catalogo, name='catalogo'),
    path('api/', include(router.urls)),
]