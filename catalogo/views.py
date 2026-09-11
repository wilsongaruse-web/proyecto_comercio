from django.shortcuts import render

from .models import Producto
from rest_framework import viewsets
from .serializer import CatalogoSerializer


def catalogo(request):
    productos = Producto.objects.all().order_by('-id')
    return render(request, 'catalogo/catalogo.html', {'productos': productos})

class CatalogoViewSet(viewsets.ModelViewSet):
    queryset=Producto.objects.all()
    serializer_class=CatalogoSerializer