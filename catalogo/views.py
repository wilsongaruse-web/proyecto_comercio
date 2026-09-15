from django.shortcuts import render

from .models import Producto
from rest_framework import viewsets
from .serializer import CatalogoSerializer


def catalogo(request):
    productos = Producto.objects.all().order_by('-id')
    ofertas = productos.filter(
        oferta=True,
        precio_oferta__isnull=False,
        oferta_restante__gt=0,
    ).order_by('nombre')
    return render(
        request,
        'catalogo/catalogo.html',
        {'productos': productos, 'ofertas': ofertas},
    )

class CatalogoViewSet(viewsets.ModelViewSet):
    queryset=Producto.objects.all()
    serializer_class=CatalogoSerializer