from collections import defaultdict

from django.db import transaction

from .models import DetalleVenta, Producto, Venta


class StockInsuficiente(Exception):
    def __init__(self, productos):
        self.productos = productos
        super().__init__(", ".join(productos))


class ProductoNoDisponible(Exception):
    pass


@transaction.atomic
def crear_venta(*, usuario, nombre_cliente, correo_cliente="", telefono_cliente="", fecha=None, items):
    cantidades = defaultdict(int)
    for producto_id, cantidad in items:
        if int(cantidad) < 1:
            raise ValueError("La cantidad debe ser mayor que cero.")
        cantidades[int(producto_id)] += int(cantidad)
    if not cantidades:
        raise ValueError("La venta debe incluir al menos un producto.")

    productos = {
        producto.pk: producto
        for producto in Producto.objects.select_for_update().filter(pk__in=cantidades)
    }
    if len(productos) != len(cantidades):
        raise ProductoNoDisponible("Uno de los productos ya no está disponible.")

    insuficientes = [
        productos[producto_id].nombre
        for producto_id, cantidad in cantidades.items()
        if productos[producto_id].stock < cantidad
    ]
    if insuficientes:
        raise StockInsuficiente(insuficientes)

    venta = Venta.objects.create(
        usuario=usuario,
        nombre_cliente=nombre_cliente,
        correo_cliente=correo_cliente,
        telefono_cliente=telefono_cliente,
        **({"fecha": fecha} if fecha else {}),
    )
    for producto_id, cantidad in cantidades.items():
        producto = productos[producto_id]
        unidades_oferta = 0
        if producto.oferta and producto.precio_oferta and producto.oferta_restante:
            unidades_oferta = min(cantidad, producto.oferta_restante)
            DetalleVenta.objects.create(
                venta=venta,
                producto=producto,
                nombre_producto=producto.nombre,
                cantidad=unidades_oferta,
                precio_unitario=producto.precio_oferta,
            )
        unidades_precio_regular = cantidad - unidades_oferta
        if unidades_precio_regular:
            DetalleVenta.objects.create(
                venta=venta,
                producto=producto,
                nombre_producto=producto.nombre,
                cantidad=unidades_precio_regular,
                precio_unitario=producto.precio,
            )
        producto.stock -= cantidad
        update_fields = ["stock"]
        if producto.oferta and producto.oferta_restante is not None:
            producto.oferta_restante = max(0, producto.oferta_restante - cantidad)
            update_fields.append("oferta_restante")
        producto.save(update_fields=update_fields)

    return venta