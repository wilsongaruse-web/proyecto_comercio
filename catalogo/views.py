from django.shortcuts import render, redirect, get_object_or_404
from .models import Producto, CarritoItem
from django.contrib import messages
from django.http import JsonResponse


def catalogo(request):
    productos = Producto.objects.all().order_by('-id')
    items_carrito = CarritoItem.objects.all()
    total_items = items_carrito.count()
    cantidades_en_carrito = {item.producto_id: item.cantidad for item in items_carrito}

    for producto in productos:
        producto.en_carrito = cantidades_en_carrito.get(producto.id, 0)
        producto.disponible_restante = producto.stock - producto.en_carrito

    return render(request, 'catalogo/catalogo.html', {'productos': productos, 'total_items': total_items})


def ver_carrito(request):
    items = CarritoItem.objects.all()
    total = sum(item.subtotal() for item in items)
    return render(request, 'catalogo/cart.html', {'items': items, 'total': total})


def agregar_al_carrito(request, producto_id):
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id=producto_id)
        cantidad_ingresada = int(request.POST.get('cantidad', 1))

        if producto.stock <= 0:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Producto agotado'}, status=400)
            messages.error(request, f"El producto '{producto.nombre}' se encuentra agotado.")
            return redirect('catalogo:catalogo')

        item = CarritoItem.objects.filter(producto=producto).first()

        if item:
            nueva_cantidad = item.cantidad + cantidad_ingresada
        else:
            item = CarritoItem(producto=producto, cantidad=0)
            nueva_cantidad = cantidad_ingresada

        if nueva_cantidad > producto.stock:
            # Si es una petición AJAX, solo retornamos el JSON sin crear un mensaje persistente en la sesión
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Stock superado'}, status=400)
            messages.warning(request, f"No hay más stock disponible para '{producto.nombre}'.")
        else:
            item.cantidad = nueva_cantidad
            item.save()

            nuevo_total_carrito = CarritoItem.objects.count()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'ok',
                    'nombre': producto.nombre,
                    'stock_restante': producto.stock - item.cantidad,
                    'total_items': nuevo_total_carrito
                })

            # Solo creamos el mensaje flash si la recarga de la página es tradicional (SIN AJAX)
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