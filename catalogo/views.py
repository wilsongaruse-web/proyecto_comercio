import json
import re
from decimal import Decimal
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from rest_framework import viewsets

from .forms import IngresoClienteForm, PedidoCheckoutForm, RegistroClienteForm
from .models import Producto, Venta
from .services import ProductoNoDisponible, StockInsuficiente, crear_venta
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


def _cliente_destino(request, fallback):
    destino = request.POST.get("next") or request.GET.get("next")
    if destino and url_has_allowed_host_and_scheme(
        destino,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return destino
    return fallback


def registro_cliente(request):
    if request.user.is_authenticated:
        return redirect("catalogo:checkout")
    form = RegistroClienteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        usuario = form.save()
        login(request, usuario)
        return redirect(_cliente_destino(request, reverse("catalogo:catalogo")))
    return render(request, "catalogo/registro.html", {"form": form})


def login_cliente(request):
    if request.user.is_authenticated:
        return redirect("catalogo:checkout")
    form = IngresoClienteForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect(_cliente_destino(request, reverse("catalogo:catalogo")))
    return render(
        request,
        "catalogo/login.html",
        {"form": form, "next": request.POST.get("next") or request.GET.get("next", "")},
    )


@login_required(login_url="/catalogo/ingresar/")
def logout_cliente(request):
    if request.method == "POST":
        logout(request)
    return redirect("catalogo:catalogo")


def _checkout_context(form):
    productos = [
        {
            "id": producto.pk,
            "nombre": producto.nombre,
            "precio": str(producto.precio_actual()),
            "stock": producto.stock,
        }
        for producto in Producto.objects.filter(stock__gt=0).order_by("nombre")
    ]
    return {"form": form, "productos_json": productos}


@login_required(login_url="/catalogo/ingresar/")
def checkout(request):
    form = PedidoCheckoutForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            contenido = json.loads(request.POST.get("carrito", ""))
            if not isinstance(contenido, list) or not contenido:
                raise ValueError("Tu carrito está vacío. Agrega productos antes de continuar.")
            items = []
            for linea in contenido:
                if not isinstance(linea, dict):
                    raise ValueError("El carrito enviado no es válido.")
                cantidad = int(linea.get("cantidad", 0))
                if cantidad > 1000:
                    raise ValueError("La cantidad solicitada no es válida.")
                items.append((int(linea.get("id")), cantidad))
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            messages.error(request, str(error) or "No se pudo validar el carrito.")
        else:
            nombre = request.user.get_full_name().strip() or request.user.get_username()
            try:
                venta = crear_venta(
                    usuario=request.user,
                    nombre_cliente=nombre,
                    correo_cliente=request.user.email,
                    telefono_cliente=form.cleaned_data["telefono"],
                    items=items,
                )
            except (StockInsuficiente, ProductoNoDisponible, ValueError) as error:
                texto = ", ".join(error.productos) if isinstance(error, StockInsuficiente) else str(error)
                messages.error(request, texto)
            else:
                return redirect("catalogo:pedido_confirmado", venta_id=venta.pk)

    return render(request, "catalogo/checkout.html", _checkout_context(form))


@login_required(login_url="/catalogo/ingresar/")
def pedido_confirmado(request, venta_id):
    venta = get_object_or_404(Venta, pk=venta_id, usuario=request.user)
    lineas = list(venta.detalles.all())
    total = sum((linea.cantidad * linea.precio_unitario for linea in lineas), Decimal("0.00"))
    for linea in lineas:
        linea.subtotal = linea.cantidad * linea.precio_unitario
    mensaje = "\n".join([
        f"Hola, realicé el pedido #{venta.pk} en Empanadas ED.",
        f"Cliente: {venta.nombre_cliente}",
        f"Teléfono: {venta.telefono_cliente}",
        "Productos:",
        *[f"- {linea.cantidad} x {linea.nombre_producto}: ${linea.cantidad * linea.precio_unitario:,.2f}" for linea in lineas],
        f"Total: ${total:,.2f}",
    ])
    telefono_negocio = re.sub(r"\D", "", settings.WHATSAPP_BUSINESS_PHONE)
    consulta = urlencode({"text": mensaje})
    whatsapp_url = f"https://wa.me/{telefono_negocio}?{consulta}"
    return render(
        request,
        "catalogo/pedido_confirmado.html",
        {"venta": venta, "lineas": lineas, "total": total, "whatsapp_url": whatsapp_url},
    )