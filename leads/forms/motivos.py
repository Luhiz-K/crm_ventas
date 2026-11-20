"""Formulario del catálogo de motivos de contrato."""

from django import forms
from ..models import MotivoContrato


class MotivoContratoForm(forms.ModelForm):
    class Meta:
        model = MotivoContrato
        fields = ['motivo_contrato']
        labels = {'motivo_contrato': 'Motivo de contrato'}
        widgets = {
            'motivo_contrato': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Comprar casa'}),
        }
