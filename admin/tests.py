from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalogo.models import Producto


class AdminOfertasTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(
            username="admin",
            password="123456",
            is_staff=True,
            is_superuser=True,
        )
        self.producto = Producto.objects.create(
            nombre="Empanada de queso",
            precio=1200,
            stock=10,
            oferta=False,
            precio_oferta=None,
            limite_oferta=None,
            oferta_restante=None,
        )

    def test_ofertas_admin_page_loads(self):
        self.client.login(username="admin", password="123456")
        response = self.client.get(reverse("gestion_admin:ofertas_admin"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gestionar Ofertas")
        self.assertContains(response, "Empanada de queso")
