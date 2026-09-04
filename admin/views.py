from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import get_object_or_404, redirect, render

from catalogo.models import Producto

from .forms import ProductoForm


def admin_required(view_func):
    @login_required(login_url="/panel-admin/login/")
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect("/")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("gestion_admin:admin_panel")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_staff:
                login(request, user)
                return redirect("gestion_admin:admin_panel")
            messages.error(request, "Este usuario no tiene permisos de administrador.")
    else:
        form = AuthenticationForm()

    return render(request, "admin/login.html", {"form": form, "titulo": "Login administrativo"})



@admin_required
def admin_panel(request):
    return render(request, "admin/admin_panel.html")





@admin_required
def productos_admin(request):
    productos = Producto.objects.all().order_by("nombre")
    return render(request, "admin/producto_list.html", {"productos": productos})



@admin_required
def producto_nuevo(request):
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto creado correctamente.")
            return redirect("gestion_admin:productos_admin")
    else:
        form = ProductoForm()

    return render(request, "admin/productos.form.html", {"form": form, "titulo": "Nuevo producto"})




@admin_required
def producto_editar(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto actualizado correctamente.")
            return redirect("gestion_admin:productos_admin")
    else:
        form = ProductoForm(instance=producto)

    return render(request, "admin/productos.form.html", {"form": form, "titulo": "Editar producto", "producto": producto})



@admin_required
def producto_eliminar(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    if request.method == "POST":
        nombre = producto.nombre
        producto.delete()
        messages.success(request, f"Producto '{nombre}' eliminado correctamente.")
        return redirect("gestion_admin:productos_admin")

    return render(request, "admin/productos_confirmar_delete.html", {"producto": producto})


@admin_required
def ofertas_admin(request):
    productos = Producto.objects.all().order_by("nombre")
    selected_id = request.GET.get("producto_id") or request.POST.get("producto_id")
    selected = get_object_or_404(Producto, pk=selected_id) if selected_id else None
    max_ofertas = Producto.objects.filter(oferta=True).count()

    if request.method == "POST":
        producto_id = request.POST.get("producto_id")
        if not producto_id:
            messages.error(request, "Debes seleccionar un producto para gestionar su oferta.")
            return render(
                request,
                "admin/ofertas.html",
                {
                    "productos": productos,
                    "selected": selected,
                    "selected_id": selected_id,
                    "max_ofertas": max_ofertas,
                },
            )
    
        producto = get_object_or_404(Producto, pk=producto_id)
        activar_oferta = request.POST.get("oferta") == "on"
        precio_oferta = request.POST.get("precio_oferta")
        limite_oferta = request.POST.get("limite_oferta")

        if activar_oferta:
            if not precio_oferta:
                messages.error(request, "Debes ingresar un precio para la oferta.")
            elif not limite_oferta or int(limite_oferta) < 1:
                messages.error(request, "El límite de oferta debe ser mayor a cero.")
            else:
                producto.oferta = True
                producto.precio_oferta = Decimal(precio_oferta)
                producto.limite_oferta = int(limite_oferta)
                producto.oferta_restante = int(limite_oferta)
                producto.save()
                messages.success(request, f"Oferta guardada para '{producto.nombre}'.")
                return redirect("gestion_admin:ofertas_admin")
        else:
            producto.oferta = False
            producto.precio_oferta = None
            producto.limite_oferta = None
            producto.oferta_restante = None
            producto.save()
            messages.success(request, f"Oferta desactivada para '{producto.nombre}'.")
            return redirect("gestion_admin:ofertas_admin")

        selected = producto
        selected_id = producto.pk

    context = {
        "productos": productos,
        "selected": selected,
        "selected_id": selected_id,
        "max_ofertas": max_ofertas,
    }
    return render(request, "admin/ofertas.html", context)
