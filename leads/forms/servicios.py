"""Formulario del catálogo de servicios y su banda de precios."""

from django import forms
from ..models import Servicios


class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicios
        fields = ['nombre_servicio', 'precio_minimo', 'precio_ideal', 'precio_maximo', 'estado']
        labels = {
            'nombre_servicio': 'Nombre del producto',
            'precio_minimo': 'Valor mínimo',
            'precio_ideal': 'Valor ideal',
            'precio_maximo': 'Valor máximo',
            'estado': 'Estado',
        }
        widgets = {
            'nombre_servicio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Reparación básica'}),
            'precio_minimo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'precio_ideal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'precio_maximo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estado': forms.Select(choices=[('ACTIVO', 'Activo'), ('INACTIVO', 'Inactivo')], attrs={'class': 'form-select'}),
        }

    def clean(self):
        cd = super().clean()
        mn, ideal, mx = cd.get('precio_minimo'), cd.get('precio_ideal'), cd.get('precio_maximo')
        if mn is not None and mx is not None and mn > mx:
            self.add_error('precio_maximo', 'El máximo no puede ser menor que el mínimo.')
        if ideal is not None and mn is not None and mx is not None and (ideal < mn or ideal > mx):
            self.add_error('precio_ideal', 'El valor ideal debe estar entre el mínimo y el máximo.')
        return cd
