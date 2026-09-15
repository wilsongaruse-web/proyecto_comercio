from django.shortcuts import render, redirect, get_object_or_404
from .models import Producto, CarritoItem
from django.contrib import messages


def catalogo(request):
    productos = Producto.objects.all().order_by('-id')
    
    # Obtener todas las cantidades guardadas actualmente en el carrito
    items_carrito = CarritoItem.objects.all()
    cantidades_en_carrito = {item.producto_id: item.cantidad for item in items_carrito}

    # Calcular para cada producto cuánto le queda realmente disponible al usuario
    for producto in productos:
        producto.en_carrito = cantidades_en_carrito.get(producto.id, 0)
        producto.disponible_restante = producto.stock - producto.en_carrito

    return render(request, 'catalogo/catalogo.html', {'productos': productos})


def ver_carrito(request):
    items = CarritoItem.objects.all()
    total = sum(item.subtotal() for item in items)
    return render(request, 'catalogo/cart.html', {'items': items, 'total': total})


def agregar_al_carrito(request, producto_id):
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id=producto_id)
        cantidad_ingresada = int(request.POST.get('cantidad', 1))

        if producto.stock <= 0:
            messages.error(request, f"El producto '{producto.nombre}' se encuentra agotado.")
            return redirect('catalogo:catalogo')
        
        item, creado = CarritoItem.objects.get_or_create(producto=producto)

        cantidad_actual = 0 if creado else item.cantidad
        nueva_cantidad = cantidad_actual + cantidad_ingresada

        # Validación correcta del stock
        if nueva_cantidad > producto.stock:
            messages.warning(
                request, 
                f"No puedes agregar más unidades. El stock disponible de '{producto.nombre}' es de {producto.stock}."
            )
            # Si era nuevo y superó el stock, borramos el registro temporal
            if creado:
                item.delete()
        else:
            item.cantidad = nueva_cantidad
            item.save()
            messages.success(request, f"¡{producto.nombre} agregado al carrito!")

    return redirect('catalogo:catalogo')


def eliminar_del_carrito(request, item_id):
    item = get_object_or_404(CarritoItem, id=item_id)
    item.delete()
    return redirect('catalogo:ver_carrito')  


def aumentar_cantidad(request, item_id):
    item = get_object_or_404(CarritoItem, id=item_id)
    if item.cantidad < item.producto.stock:
        item.cantidad += 1
        item.save()
    else:
        messages.warning(request, f"No hay más stock disponible para '{item.producto.nombre}'.")
    return redirect('catalogo:ver_carrito')


def disminuir_cantidad(request, item_id):
    item = get_object_or_404(CarritoItem, id=item_id)
    if item.cantidad > 1:
        item.cantidad -= 1
        item.save()
    else:
        item.delete()
    return redirect('catalogo:ver_carrito')