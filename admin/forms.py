from django import forms

from catalogo.models import Producto


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
