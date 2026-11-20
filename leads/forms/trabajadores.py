"""Formulario de alta y edición de trabajadores."""

from django import forms
from ..models import Sede, Cargo
from ..utils import CARGOS_SISTEMA


class SedeChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.nombre_sede


class CargoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.nombre_cargo


class TrabajadorForm(forms.Form):
    """Crea (o edita) a la PERSONA y al TRABAJADOR en un solo formulario."""
    nombres = forms.CharField(label='Nombres', widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellidos = forms.CharField(label='Apellidos', widget=forms.TextInput(attrs={'class': 'form-control'}))
    numero_documento = forms.CharField(label='Documento', widget=forms.TextInput(attrs={'class': 'form-control'}))
    correo = forms.CharField(label='Correo', required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    telefono = forms.CharField(label='Teléfono', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    id_cargo = CargoChoiceField(queryset=Cargo.objects.filter(nombre_cargo__in=CARGOS_SISTEMA),
                                label='Cargo', required=False,
                                widget=forms.Select(attrs={'class': 'form-select'}))
    id_sede = SedeChoiceField(queryset=Sede.objects.all(), label='Sede', required=False,
                              widget=forms.Select(attrs={'class': 'form-select'}))
