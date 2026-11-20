"""Formulario del catálogo de burós de crédito."""

from django import forms
from ..models import Buro


class BuroForm(forms.ModelForm):
    class Meta:
        model = Buro
        fields = ['nombre_buro', 'estado']
        labels = {'nombre_buro': 'Nombre del buró', 'estado': 'Estado'}
        widgets = {
            'nombre_buro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Datacrédito'}),
            'estado': forms.Select(
                choices=[('ACTIVO', 'Activo'), ('INACTIVO', 'Inactivo')],
                attrs={'class': 'form-select'}),
        }
