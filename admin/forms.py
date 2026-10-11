from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.forms import formset_factory
from django.utils import timezone

from catalogo.models import AtencionCliente, Producto, Venta


class AdminUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=False, label="Correo electrónico")
    is_staff = forms.BooleanField(
        required=False,
        initial=True,
        label="Puede acceder al panel administrativo",
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label="Roles",
        help_text="Los permisos de cada rol se gestionan desde los grupos de Django.",
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "email", "is_staff", "groups")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.is_staff = self.cleaned_data["is_staff"]
        user.is_superuser = False
        if commit:
            user.save()
            self.save_m2m()
        return user


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            "nombre",
            "precio",
            "stock",
            "imagen",
            "oferta",
            "precio_oferta",
            "limite_oferta",
            "oferta_restante",
            "categoria",
        ]
        labels = {
            "nombre": "Nombre",
            "precio": "Precio",
            "stock": "Stock",
            "imagen": "Imagen",
            "oferta": "¿Tiene oferta?",
            "precio_oferta": "Precio en oferta",
            "limite_oferta": "Límite de oferta",
            "oferta_restante": "Oferta restante",
            "categoria": "Categoría",
        }
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "precio": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "stock": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "imagen": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "categoria": forms.TextInput(attrs={"class": "form-control"}),
            "precio_oferta": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "limite_oferta": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "oferta_restante": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("oferta") and not cleaned_data.get("precio_oferta"):
            self.add_error("precio_oferta", "Si el producto tiene oferta, debe indicar un precio de oferta.")
        return cleaned_data


class VentaRegistroForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ["nombre_cliente", "correo_cliente", "fecha"]
        labels = {
            "nombre_cliente": "Nombre del cliente",
            "correo_cliente": "Correo electrónico",
            "fecha": "Fecha y hora de la venta",
        }
        widgets = {
            "nombre_cliente": forms.TextInput(attrs={"class": "form-control"}),
            "correo_cliente": forms.EmailInput(attrs={"class": "form-control"}),
            "fecha": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fecha"].initial = timezone.localtime().replace(second=0, microsecond=0)


class VentaLineaForm(forms.Form):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.order_by("nombre"),
        label="Producto",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    cantidad = forms.IntegerField(
        min_value=1,
        label="Cantidad",
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
    )


VentaLineaFormSet = formset_factory(VentaLineaForm, extra=2)


class AtencionRegistroForm(forms.ModelForm):
    class Meta:
        model = AtencionCliente
        fields = ["nombre_cliente", "correo_cliente", "asunto", "fecha_apertura", "primera_respuesta"]
        labels = {
            "nombre_cliente": "Nombre del cliente",
            "correo_cliente": "Correo electrónico",
            "asunto": "Asunto",
            "fecha_apertura": "Fecha y hora de apertura",
            "primera_respuesta": "Fecha y hora de primera respuesta (opcional)",
        }
        widgets = {
            "nombre_cliente": forms.TextInput(attrs={"class": "form-control"}),
            "correo_cliente": forms.EmailInput(attrs={"class": "form-control"}),
            "asunto": forms.TextInput(attrs={"class": "form-control"}),
            "fecha_apertura": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "primera_respuesta": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        now = timezone.localtime().replace(second=0, microsecond=0)
        self.fields["fecha_apertura"].initial = now

    def clean(self):
        cleaned_data = super().clean()
        opened_at = cleaned_data.get("fecha_apertura")
        answered_at = cleaned_data.get("primera_respuesta")
        if opened_at and answered_at and answered_at < opened_at:
            self.add_error("primera_respuesta", "La respuesta no puede ser anterior a la apertura.")
        return cleaned_data


class ReporteFiltroForm(forms.Form):
    desde = forms.DateField(
        label="Desde",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    hasta = forms.DateField(
        label="Hasta",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        desde = cleaned_data.get("desde")
        hasta = cleaned_data.get("hasta")
        if desde and hasta and desde > hasta:
            self.add_error("hasta", "La fecha final debe ser igual o posterior a la inicial.")
        return cleaned_data
