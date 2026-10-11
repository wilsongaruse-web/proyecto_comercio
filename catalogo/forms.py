from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm


class RegistroClienteForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email"}),
    )
    first_name = forms.CharField(
        max_length=150,
        label="Nombre",
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "given-name"}),
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        label="Apellido",
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "family-name"}),
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "first_name", "last_name", "email")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "autocomplete": "username"}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        user_model = get_user_model()
        if user_model.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo electrónico.")
        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Nombre de usuario"
        self.fields["username"].widget.attrs.update({"class": "form-control", "autocomplete": "username"})
        self.fields["password1"].label = "Contraseña"
        self.fields["password1"].help_text = "Usa al menos 8 caracteres y evita claves comunes o fáciles de adivinar."
        self.fields["password2"].label = "Confirmar contraseña"
        self.fields["password2"].help_text = "Escribe de nuevo la misma contraseña."
        self.fields["password1"].widget.attrs.update({"class": "form-control", "autocomplete": "new-password"})
        self.fields["password2"].widget.attrs.update({"class": "form-control", "autocomplete": "new-password"})


class PedidoCheckoutForm(forms.Form):
    telefono = forms.CharField(
        min_length=7,
        max_length=30,
        label="Teléfono de contacto",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "autocomplete": "tel",
            "placeholder": "+57 300 000 0000",
        }),
    )

    def clean_telefono(self):
        telefono = self.cleaned_data["telefono"].strip()
        digits = "".join(character for character in telefono if character.isdigit())
        if len(digits) < 7:
            raise forms.ValidationError("Ingresa un teléfono válido para coordinar tu pedido.")
        return telefono


class IngresoClienteForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Nombre de usuario"
        self.fields["username"].widget.attrs.update({"class": "form-control", "autocomplete": "username"})
        self.fields["password"].label = "Contraseña"
        self.fields["password"].widget.attrs.update({"class": "form-control", "autocomplete": "current-password"})