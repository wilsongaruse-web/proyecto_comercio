from django.db import models
from django.conf import settings
from django.utils import timezone


class Producto(models.Model):
    nombre = models.CharField(max_length=160)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    oferta = models.BooleanField(default=False)
    precio_oferta = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    limite_oferta = models.PositiveIntegerField(null=True, blank=True)
    oferta_restante = models.PositiveIntegerField(null=True, blank=True)
    categoria = models.CharField(max_length=80, default='general')

    def __str__(self):
        return self.nombre

    def precio_actual(self):
        if self.oferta and self.precio_oferta and self.oferta_restante:
            return self.precio_oferta
        return self.precio


class Venta(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventas",
    )
    nombre_cliente = models.CharField(max_length=160)
    correo_cliente = models.EmailField(blank=True)
    telefono_cliente = models.CharField(max_length=30, blank=True)
    fecha = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"Venta #{self.pk} - {self.nombre_cliente}"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(
        Producto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="detalles_venta",
    )
    nombre_producto = models.CharField(max_length=160)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.nombre_producto}"


class AtencionCliente(models.Model):
    nombre_cliente = models.CharField(max_length=160)
    correo_cliente = models.EmailField(blank=True)
    asunto = models.CharField(max_length=200)
    fecha_apertura = models.DateTimeField(default=timezone.now, db_index=True)
    primera_respuesta = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha_apertura"]
        verbose_name = "atención al cliente"
        verbose_name_plural = "atenciones al cliente"

    def __str__(self):
        return f"{self.asunto} - {self.nombre_cliente}"
