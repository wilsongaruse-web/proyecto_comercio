import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Producto, Venta


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


class CompraClienteTests(TestCase):
	def setUp(self):
		User = get_user_model()
		self.cliente = User.objects.create_user(
			username="cliente",
			email="cliente@example.com",
			first_name="Carla",
			password="UnaClaveSegura123!",
		)
		self.producto = Producto.objects.create(
			nombre="Empanada de carne",
			precio=4500,
			stock=6,
		)
		self.client.login(username="cliente", password="UnaClaveSegura123!")

	def test_checkout_requiere_iniciar_sesion(self):
		self.client.logout()
		response = self.client.get(reverse("catalogo:checkout"))

		self.assertEqual(response.status_code, 302)
		self.assertIn(reverse("catalogo:login"), response["Location"])
		self.assertIn("next=", response["Location"])

	def test_registro_de_cliente_inicia_sesion_y_conserva_destino(self):
		response = self.client.post(
			reverse("catalogo:registro"),
			{
				"username": "nueva_cliente",
				"first_name": "Nueva",
				"last_name": "Compradora",
				"email": "nueva@example.com",
				"password1": "Clave-Compra!928374",
				"password2": "Clave-Compra!928374",
				"next": reverse("catalogo:checkout"),
			},
		)

		self.assertRedirects(response, reverse("catalogo:checkout"))
		self.assertTrue(response.wsgi_request.user.is_authenticated)

	def test_compra_guarda_pedido_descuenta_stock_y_prepara_whatsapp(self):
		response = self.client.post(
			reverse("catalogo:checkout"),
			{
				"telefono": "+57 300 444 5566",
				"carrito": json.dumps([{"id": self.producto.pk, "cantidad": 2}]),
			},
		)

		venta = Venta.objects.get(usuario=self.cliente)
		self.assertRedirects(response, reverse("catalogo:pedido_confirmado", args=[venta.pk]))
		self.assertEqual(venta.telefono_cliente, "+57 300 444 5566")
		self.assertEqual(venta.detalles.get().cantidad, 2)
		self.producto.refresh_from_db()
		self.assertEqual(self.producto.stock, 4)

		confirmation = self.client.get(response.url)
		self.assertContains(confirmation, f"wa.me/573001112233")
		self.assertContains(confirmation, "Pedido #")
		self.assertContains(confirmation, "Puls")

	def test_stock_insuficiente_no_crea_pedido(self):
		response = self.client.post(
			reverse("catalogo:checkout"),
			{
				"telefono": "+57 300 444 5566",
				"carrito": json.dumps([{"id": self.producto.pk, "cantidad": 7}]),
			},
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(Venta.objects.count(), 0)
		self.producto.refresh_from_db()
		self.assertEqual(self.producto.stock, 6)

	def test_login_de_cliente_funciona(self):
		self.client.logout()
		response = self.client.post(
			reverse("catalogo:login"),
			{"username": "cliente", "password": "UnaClaveSegura123!"},
		)

		self.assertRedirects(response, reverse("catalogo:catalogo"))
		self.assertTrue(response.wsgi_request.user.is_authenticated)

	def test_paginas_de_cuenta_y_checkout_renderizan(self):
		self.client.logout()
		login_response = self.client.get(reverse("catalogo:login"))
		self.assertEqual(login_response.status_code, 200)
		self.assertContains(login_response, "Nombre de usuario")
		self.assertContains(login_response, "Contraseña")
		registro = self.client.get(reverse("catalogo:registro"))
		self.assertEqual(registro.status_code, 200)
		self.assertContains(registro, "Nombre de usuario")

		self.client.login(username="cliente", password="UnaClaveSegura123!")
		checkout = self.client.get(reverse("catalogo:checkout"))
		self.assertEqual(checkout.status_code, 200)
		self.assertContains(checkout, "Teléfono de contacto")

# Create your tests here.
