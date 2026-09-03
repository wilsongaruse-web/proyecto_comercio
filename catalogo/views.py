from django.shortcuts import render

from .models import Producto


def catalogo(request):
    productos = Producto.objects.all().order_by('-id')
    return render(request, 'catalogo/catalogo.html', {'productos': productos})
