from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
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


class AdminUsersTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.superuser = User.objects.create_superuser(
            username="admin1",
            email="admin1@example.com",
            password="123456segura",
        )
        self.staff_user = User.objects.create_user(
            username="encargado",
            password="123456segura",
            is_staff=True,
        )
        self.group = Group.objects.create(name="Gestion de productos")

    def test_superuser_can_create_staff_user_with_role(self):
        self.client.login(username="admin1", password="123456segura")
        response = self.client.post(
            reverse("gestion_admin:usuario_nuevo"),
            {
                "username": "nuevo_admin",
                "email": "nuevo@example.com",
                "password1": "UnaClaveSegura123!",
                "password2": "UnaClaveSegura123!",
                "is_staff": "on",
                "groups": [self.group.pk],
            },
        )

        self.assertRedirects(response, reverse("gestion_admin:admin_panel"))
        user = get_user_model().objects.get(username="nuevo_admin")
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(list(user.groups.all()), [self.group])

    def test_staff_user_cannot_create_administrator(self):
        self.client.login(username="encargado", password="123456segura")
        response = self.client.get(reverse("gestion_admin:usuario_nuevo"), follow=True)

        self.assertEqual(response.redirect_chain[-1][0], reverse("gestion_admin:admin_panel"))
        self.assertEqual(get_user_model().objects.filter(username="nuevo_admin").count(), 0)

    def test_admin_can_log_out(self):
        self.client.login(username="admin1", password="123456segura")
        response = self.client.get(reverse("gestion_admin:logout"))

        self.assertRedirects(response, reverse("gestion_admin:login"))
        panel_response = self.client.get(reverse("gestion_admin:admin_panel"))
        self.assertRedirects(
            panel_response,
            f"{reverse('gestion_admin:login')}?next={reverse('gestion_admin:admin_panel')}",
        )
