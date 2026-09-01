from django.db import models


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
