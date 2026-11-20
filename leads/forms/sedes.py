from django import forms
from ..models import Sede, Trabajador


class TrabajadorChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        cargo = obj.id_cargo.nombre_cargo if obj.id_cargo else 'Sin cargo'
        return f"{obj.id_persona.nombres} {obj.id_persona.apellidos} — {cargo}"


class SedeForm(forms.ModelForm):
    # El responsable es un TRABAJADOR (no una persona suelta); guardamos su persona en id_responsable.
    responsable_trab = TrabajadorChoiceField(
        queryset=Trabajador.objects.select_related('id_persona', 'id_cargo').all(),
        label='Responsable (gerente)', required=False,
        widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = Sede
        fields = ['nombre_sede', 'direccion_sede', 'correo_sede', 'telefono_sede']
        labels = {
            'nombre_sede': 'Nombre de la sede',
            'direccion_sede': 'Dirección',
            'correo_sede': 'Correo',
            'telefono_sede': 'Teléfono',
        }
        widgets = {
            'nombre_sede': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Sede Norte'}),
            'direccion_sede': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Calle 100 #15-20'}),
            'correo_sede': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ej. norte@deudoor.com'}),
            'telefono_sede': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 6012345678'}),
        }
