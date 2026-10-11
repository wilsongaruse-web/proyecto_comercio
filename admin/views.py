from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import ExtractHour, TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from catalogo.models import AtencionCliente, DetalleVenta, Producto, Venta

from .forms import (
    AdminUserCreationForm,
    AtencionRegistroForm,
    ProductoForm,
    ReporteFiltroForm,
    VentaLineaFormSet,
    VentaRegistroForm,
)
from catalogo.services import ProductoNoDisponible, StockInsuficiente, crear_venta


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


def admin_logout(request):
    logout(request)
    return redirect("gestion_admin:login")



@admin_required
def admin_panel(request):
    return render(request, "admin/admin_panel.html")


@admin_required
def usuario_nuevo(request):
    if not request.user.is_superuser:
        messages.error(request, "Solo un superusuario puede crear administradores.")
        return redirect("gestion_admin:admin_panel")

    if request.method == "POST":
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Usuario '{user.username}' creado correctamente.")
            return redirect("gestion_admin:admin_panel")
    else:
        form = AdminUserCreationForm()

    return render(request, "admin/usuario_form.html", {"form": form})





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


def _period_bounds(desde, hasta):
    zone = timezone.get_current_timezone()
    inicio = timezone.make_aware(datetime.combine(desde, time.min), zone)
    fin = timezone.make_aware(datetime.combine(hasta + timedelta(days=1), time.min), zone)
    return inicio, fin


def _report_data(desde, hasta):
    inicio, fin = _period_bounds(desde, hasta)
    ventas = Venta.objects.filter(fecha__gte=inicio, fecha__lt=fin)
    detalles = DetalleVenta.objects.filter(venta__fecha__gte=inicio, venta__fecha__lt=fin)
    importe = ExpressionWrapper(
        F("cantidad") * F("precio_unitario"),
        output_field=DecimalField(max_digits=20, decimal_places=2),
    )
    resumen = detalles.aggregate(ingresos=Sum(importe), unidades=Sum("cantidad"))

    ventas_por_mes = list(
        detalles.annotate(periodo=TruncMonth("venta__fecha"))
        .values("periodo")
        .annotate(ventas=Count("venta_id", distinct=True), ingresos=Sum(importe))
        .order_by("periodo")
    )
    ventas_por_hora = list(
        detalles.annotate(hora=ExtractHour("venta__fecha"))
        .values("hora")
        .annotate(ventas=Count("venta_id", distinct=True), ingresos=Sum(importe))
        .order_by("hora")
    )
    productos_vendidos = list(
        detalles.values("nombre_producto")
        .annotate(unidades=Sum("cantidad"), ingresos=Sum(importe))
        .order_by("-unidades", "nombre_producto")
    )

    clientes = {}
    for venta in Venta.objects.filter(fecha__lt=fin).values(
        "usuario_id", "correo_cliente", "nombre_cliente", "fecha"
    ):
        email = venta["correo_cliente"].strip().lower()
        nombre = venta["nombre_cliente"].strip()
        clave = f"usuario:{venta['usuario_id']}" if venta["usuario_id"] else (f"email:{email}" if email else f"nombre:{nombre.lower()}")
        fecha_venta = timezone.localtime(venta["fecha"]).date()
        if clave not in clientes:
            clientes[clave] = {"nombre": nombre, "ultima_compra": fecha_venta, "pedidos": 1}
        else:
            clientes[clave]["pedidos"] += 1
            clientes[clave]["ultima_compra"] = max(clientes[clave]["ultima_compra"], fecha_venta)

    segmentos = {"0-30 días": 0, "31-90 días": 0, "Más de 90 días": 0}
    for cliente in clientes.values():
        dias = (hasta - cliente["ultima_compra"]).days
        segmento = "0-30 días" if dias <= 30 else "31-90 días" if dias <= 90 else "Más de 90 días"
        cliente["segmento"] = segmento
        segmentos[segmento] += 1
    clientes_recientes = sorted(clientes.values(), key=lambda cliente: cliente["ultima_compra"], reverse=True)

    productos_stock = {producto.pk: producto for producto in Producto.objects.all()}
    ventas_por_producto = defaultdict(int)
    for fila in detalles.values("producto_id", "nombre_producto").annotate(unidades=Sum("cantidad")):
        ventas_por_producto[fila["producto_id"]] += fila["unidades"]
    puede_estimar_rotacion = hasta == timezone.localdate()
    rotacion = []
    for producto in productos_stock.values():
        unidades = ventas_por_producto.get(producto.pk, 0)
        stock_cierre = producto.stock
        stock_apertura_estimado = stock_cierre + unidades
        promedio_estimado = (stock_apertura_estimado + stock_cierre) / 2
        rotacion.append({
            "nombre": producto.nombre,
            "unidades": unidades,
            "stock_actual": stock_cierre,
            "rotacion": (
                unidades / promedio_estimado if promedio_estimado else None
            ) if puede_estimar_rotacion else None,
        })
    rotacion.sort(key=lambda fila: fila["unidades"], reverse=True)

    atenciones = AtencionCliente.objects.filter(fecha_apertura__gte=inicio, fecha_apertura__lt=fin)
    tiempos_respuesta = [
        (respuesta - apertura).total_seconds()
        for apertura, respuesta in atenciones.exclude(primera_respuesta__isnull=True)
        .values_list("fecha_apertura", "primera_respuesta")
    ]
    promedio_respuesta = (
        sum(tiempos_respuesta) / len(tiempos_respuesta) / 60 if tiempos_respuesta else None
    )

    return {
        "desde": desde,
        "hasta": hasta,
        "numero_ventas": ventas.count(),
        "ingresos": resumen["ingresos"] or Decimal("0.00"),
        "unidades_vendidas": resumen["unidades"] or 0,
        "ventas_por_mes": ventas_por_mes,
        "ventas_por_hora": ventas_por_hora,
        "productos_vendidos": productos_vendidos,
        "segmentos": segmentos,
        "clientes_recientes": clientes_recientes,
        "inventario_riesgo": Producto.objects.filter(stock__lte=5).order_by("stock", "nombre"),
        "rotacion": rotacion,
        "rotacion_disponible": puede_estimar_rotacion,
        "promedio_respuesta": promedio_respuesta,
        "atenciones_pendientes": atenciones.filter(primera_respuesta__isnull=True).count(),
        "atenciones_respondidas": len(tiempos_respuesta),
    }


def _report_filter(request):
    hoy = timezone.localdate()
    inicial = {"desde": hoy.replace(day=1), "hasta": hoy}
    form = ReporteFiltroForm(request.GET or None, initial=inicial)
    if form.is_valid():
        return form, form.cleaned_data["desde"], form.cleaned_data["hasta"]
    return form, inicial["desde"], inicial["hasta"]


@admin_required
def reportes_admin(request):
    form, desde, hasta = _report_filter(request)
    datos = _report_data(desde, hasta)
    return render(request, "admin/reportes.html", {"form": form, **datos})


@admin_required
def reportes_admin_pdf(request):
    form, desde, hasta = _report_filter(request)
    if not form.is_valid() and request.GET:
        messages.error(request, "Revisa las fechas del reporte antes de descargarlo.")
        return redirect("gestion_admin:reportes_admin")

    datos = _report_data(desde, hasta)
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=0.5 * inch, leftMargin=0.5 * inch)
    styles = getSampleStyleSheet()
    content = [
        Paragraph("Reporte de Empanadas ED", styles["Title"]),
        Paragraph(f"Período: {desde:%d/%m/%Y} al {hasta:%d/%m/%Y}", styles["Normal"]),
        Spacer(1, 14),
        Paragraph(
            f"Ventas: {datos['numero_ventas']} | Ingresos: ${datos['ingresos']:,.2f} | "
            f"Unidades: {datos['unidades_vendidas']}", styles["Heading2"]
        ),
    ]

    def add_table(title, headings, rows):
        content.append(Paragraph(title, styles["Heading2"]))
        table = Table([headings, *rows], repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#873b2d")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cccccc")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        content.extend([table, Spacer(1, 12)])

    add_table("Ventas por mes", ["Mes", "Pedidos", "Ingresos"], [
        [fila["periodo"].strftime("%m/%Y"), fila["ventas"], f"${fila['ingresos'] or 0:,.2f}"]
        for fila in datos["ventas_por_mes"]
    ] or [["Sin ventas", 0, "$0.00"]])
    add_table("Ventas por hora", ["Hora", "Pedidos", "Ingresos"], [
        [f"{fila['hora']:02d}:00", fila["ventas"], f"${fila['ingresos'] or 0:,.2f}"]
        for fila in datos["ventas_por_hora"]
    ] or [["Sin ventas", 0, "$0.00"]])
    add_table("Productos vendidos", ["Producto", "Unidades", "Ingresos"], [
        [fila["nombre_producto"], fila["unidades"], f"${fila['ingresos'] or 0:,.2f}"]
        for fila in datos["productos_vendidos"]
    ] or [["Sin ventas", 0, "$0.00"]])
    add_table("Clientes por última compra", ["Segmento", "Clientes"], [
        [nombre, cantidad] for nombre, cantidad in datos["segmentos"].items()
    ])
    add_table("Última compra por cliente", ["Cliente", "Última compra", "Pedidos", "Segmento"], [
        [cliente["nombre"], cliente["ultima_compra"].strftime("%d/%m/%Y"), cliente["pedidos"], cliente["segmento"]]
        for cliente in datos["clientes_recientes"]
    ] or [["Sin clientes", "-", 0, "-"]])
    add_table("Inventario en riesgo (stock <= 5)", ["Producto", "Stock"], [
        [producto.nombre, producto.stock] for producto in datos["inventario_riesgo"]
    ] or [["Sin productos en riesgo", "-"]])
    add_table("Rotación estimada", ["Producto", "Unidades", "Stock actual", "Rotación"], [
        [fila["nombre"], fila["unidades"], fila["stock_actual"],
         f"{fila['rotacion']:.2f}x" if fila["rotacion"] is not None else "N/D"]
        for fila in datos["rotacion"]
    ] or [["Sin productos", "-", "-", "N/D"]])
    promedio = datos["promedio_respuesta"]
    respuesta = f"{promedio:.1f} minutos" if promedio is not None else "Sin respuestas registradas"
    content.append(Paragraph(
        f"Atención al cliente: promedio de primera respuesta {respuesta}; "
        f"pendientes: {datos['atenciones_pendientes']}; respondidas: {datos['atenciones_respondidas']}",
        styles["Normal"],
    ))
    content.append(Spacer(1, 8))
    content.append(Paragraph(
        "La rotación se estima como unidades vendidas / inventario promedio estimado "
        "(stock actual más ventas, suponiendo que no hubo reposiciones ni ajustes). "
        "Solo se muestra para períodos que terminan hoy; los períodos históricos aparecen como N/D "
        "porque aún no hay historial de movimientos de inventario.",
        styles["Italic"],
    ))
    document.build(content)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="reporte_{desde:%Y%m%d}_{hasta:%Y%m%d}.pdf"'
    return response


@admin_required
def venta_nueva(request):
    form = VentaRegistroForm(request.POST or None)
    lineas = VentaLineaFormSet(request.POST or None, prefix="lineas")
    if request.method == "POST" and form.is_valid() and lineas.is_valid():
        productos = defaultdict(int)
        for linea in lineas:
            if linea.cleaned_data:
                producto = linea.cleaned_data.get("producto")
                if producto:
                    productos[producto.pk] += linea.cleaned_data["cantidad"]
        if not productos:
            messages.error(request, "Agrega al menos un producto a la venta.")
        else:
            correo = form.cleaned_data["correo_cliente"]
            usuario = get_user_model().objects.filter(email__iexact=correo).first() if correo else None
            try:
                venta = crear_venta(
                    usuario=usuario,
                    nombre_cliente=form.cleaned_data["nombre_cliente"],
                    correo_cliente=correo,
                    fecha=form.cleaned_data["fecha"],
                    items=productos.items(),
                )
            except StockInsuficiente as error:
                messages.error(request, "Stock insuficiente: " + ", ".join(error.productos))
            except ProductoNoDisponible as error:
                messages.error(request, str(error))
            else:
                messages.success(request, f"Venta #{venta.pk} registrada y existencias actualizadas.")
                return redirect("gestion_admin:reportes_admin")

    return render(request, "admin/venta_form.html", {"form": form, "lineas": lineas})


@admin_required
def atencion_nueva(request):
    form = AtencionRegistroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Registro de atención guardado.")
        return redirect("gestion_admin:reportes_admin")
    return render(request, "admin/atencion_form.html", {"form": form})
