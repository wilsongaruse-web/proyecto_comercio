from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalogo.models import AtencionCliente, DetalleVenta, Producto, Venta


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


class ReportesAdminTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(
            username="reportes_admin",
            password="clave-segura-123",
            is_staff=True,
        )
        self.producto = Producto.objects.create(
            nombre="Empanada de pollo",
            precio=2500,
            stock=10,
        )
        self.client.login(username="reportes_admin", password="clave-segura-123")

    def test_registro_de_venta_guarda_detalles_y_descuenta_stock(self):
        fecha = timezone.localtime().strftime("%Y-%m-%dT%H:%M")
        response = self.client.post(
            reverse("gestion_admin:venta_nueva"),
            {
                "nombre_cliente": "Ana Pérez",
                "correo_cliente": "ana@example.com",
                "fecha": fecha,
                "lineas-TOTAL_FORMS": "2",
                "lineas-INITIAL_FORMS": "0",
                "lineas-0-producto": str(self.producto.pk),
                "lineas-0-cantidad": "2",
                "lineas-1-producto": str(self.producto.pk),
                "lineas-1-cantidad": "1",
            },
        )

        self.assertRedirects(response, reverse("gestion_admin:reportes_admin"))
        venta = Venta.objects.get(nombre_cliente="Ana Pérez")
        detalle = venta.detalles.get()
        self.assertEqual(detalle.cantidad, 3)
        self.assertEqual(detalle.precio_unitario, 2500)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 7)

    def test_venta_con_stock_insuficiente_no_se_guarda(self):
        response = self.client.post(
            reverse("gestion_admin:venta_nueva"),
            {
                "nombre_cliente": "Ana Pérez",
                "correo_cliente": "",
                "fecha": timezone.localtime().strftime("%Y-%m-%dT%H:%M"),
                "lineas-TOTAL_FORMS": "1",
                "lineas-INITIAL_FORMS": "0",
                "lineas-0-producto": str(self.producto.pk),
                "lineas-0-cantidad": "11",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Venta.objects.count(), 0)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 10)

    def test_reporte_muestra_metricas_y_descarga_pdf(self):
        ahora = timezone.now()
        venta = Venta.objects.create(
            nombre_cliente="Luis Gómez",
            correo_cliente="luis@example.com",
            fecha=ahora,
        )
        DetalleVenta.objects.create(
            venta=venta,
            producto=self.producto,
            nombre_producto=self.producto.nombre,
            cantidad=2,
            precio_unitario=2500,
        )
        AtencionCliente.objects.create(
            nombre_cliente="Luis Gómez",
            asunto="Consulta de pedido",
            fecha_apertura=ahora - timezone.timedelta(hours=2),
            primera_respuesta=ahora - timezone.timedelta(hours=1),
        )
        hoy = timezone.localdate().isoformat()
        filtros = {"desde": hoy, "hasta": hoy}

        response = self.client.get(reverse("gestion_admin:reportes_admin"), filtros)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["numero_ventas"], 1)
        self.assertEqual(response.context["unidades_vendidas"], 2)
        self.assertEqual(response.context["promedio_respuesta"], 60)
        self.assertContains(response, "Empanada de pollo")

        pdf_response = self.client.get(reverse("gestion_admin:reportes_admin_pdf"), filtros)
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")
        self.assertTrue(pdf_response.content.startswith(b"%PDF"))

    def test_rotacion_historica_no_se_calcula_con_stock_actual(self):
        ayer = timezone.localdate() - timezone.timedelta(days=1)
        response = self.client.get(
            reverse("gestion_admin:reportes_admin"),
            {"desde": ayer.isoformat(), "hasta": ayer.isoformat()},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["rotacion"][0]["rotacion"])
