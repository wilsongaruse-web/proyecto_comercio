from django.test import TestCase

from .models import Producto


class CatalogoOfertaTests(TestCase):
	def test_catalogo_muestra_ofertas_activas_en_contexto(self):
		activa = Producto.objects.create(
			nombre="Empanada en oferta",
			precio=100,
			precio_oferta=80,
			stock=5,
			oferta=True,
			oferta_restante=2,
		)
		Producto.objects.create(
			nombre="Oferta agotada",
			precio=100,
			precio_oferta=80,
			stock=0,
			oferta=True,
			oferta_restante=0,
		)

		response = self.client.get("/catalogo/")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(list(response.context["ofertas"]), [activa])
		self.assertContains(response, "¡Hay productos en oferta!")
		self.assertContains(response, "Empanada en oferta")
		self.assertContains(response, "Oferta agotada")

# Create your tests here.
