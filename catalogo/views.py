from django.shortcuts import render

from .models import Producto, CarritoItem


def catalogo(request):
    productos = Producto.objects.all().order_by('-id')
    return render(request, 'catalogo/catalogo.html', {'productos': productos})

def ver_carrito(request):
    items = CarritoItem.objects.all()
    total = sum(item.subtotal() for item in items)
    return render(request, 'catalogo/cart.html', {'items': items, 'total': total})

def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    cantidad_ingresada = int(request.POST.get('cantidad', 1))
    
    item, creado = CarritoItem.objects.get_or_create(producto=producto)
    if creado:
        item.cantidad = cantidad_ingresada
    else:
        item.cantidad += cantidad_ingresada
        
    item.save()
    return redirect('ver_carrito')

def eliminar_del_carrito(request, item_id):
    item = get_object_or_404(CarritoItem, id=item_id)
    item.delete()
    return redirect('ver_carrito')