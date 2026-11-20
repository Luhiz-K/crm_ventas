"""Formulario de datos personales del paso 1 del wizard."""

from django import forms
from ..models import Persona


class WizardPersonaForm(forms.ModelForm):
    """Datos personales del cliente (SIN documento/tipo/teléfono: esos son la llave,
    se validan en la captura y quedan bloqueados)."""
    telefono_adicional_1 = forms.CharField(label='Teléfono adicional 1', required=False,
                                            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'}))
    telefono_adicional_2 = forms.CharField(label='Teléfono adicional 2', required=False,
                                            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'}))
    telefono_adicional_3 = forms.CharField(label='Teléfono adicional 3', required=False,
                                            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'}))

    class Meta:
        model = Persona
        fields = ['nombres', 'apellidos', 'fecha_expedicion_persona', 'fecha_nacimiento_persona',
                  'genero_persona', 'correo_persona', 'direccion_persona', 'complemento_persona',
                  'barrio_persona', 'id_ciudad']
        labels = {
            'nombres': 'Nombres', 'apellidos': 'Apellidos',
            'fecha_expedicion_persona': 'Fecha de expedición', 'fecha_nacimiento_persona': 'Fecha de nacimiento',
            'genero_persona': 'Género', 'correo_persona': 'Correo',
            'direccion_persona': 'Dirección', 'complemento_persona': 'Complemento de dirección',
            'barrio_persona': 'Barrio', 'id_ciudad': 'Ciudad',
        }
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_expedicion_persona': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_nacimiento_persona': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'genero_persona': forms.Select(choices=[('', '---'), ('M', 'Masculino'), ('F', 'Femenino')], attrs={'class': 'form-select'}),
            'correo_persona': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion_persona': forms.TextInput(attrs={'class': 'form-control'}),
            'complemento_persona': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apto, torre, etc.'}),
            'barrio_persona': forms.TextInput(attrs={'class': 'form-control'}),
            'id_ciudad': forms.Select(attrs={'class': 'form-select'}),
        }
