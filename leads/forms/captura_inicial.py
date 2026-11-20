"""Formulario de captura inicial del lead (teléfono y documento)."""

from django import forms


class CapturaTelefonoForm(forms.Form):
    LONGITUD = 10
    TIPO_DOC_CHOICES = [
        ('', 'Tipo de documento...'),
        ('CC', 'Cédula de Ciudadanía'),
        ('CE', 'Cédula de Extranjería'),
        ('SSN', 'Social Security Number'),
        ('ITIN', 'ITIN Number'),
    ]

    numero_marcado = forms.CharField(
        max_length=10, min_length=10, label='Número de teléfono',
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Ej. 3001234567', 'autofocus': 'autofocus'}))
    tipo_documento = forms.ChoiceField(
        choices=TIPO_DOC_CHOICES, label='Tipo de documento',
        widget=forms.Select(attrs={'class': 'form-select'}))
    numero_documento = forms.CharField(
        label='Número de documento',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Documento del cliente'}))
    observacion = forms.CharField(
        required=False, label='Observación inicial',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notas de la llamada (opcional)'}))

    def clean_numero_marcado(self):
        numero = (self.cleaned_data.get('numero_marcado') or '').strip()
        if not numero.isdigit():
            raise forms.ValidationError('El teléfono solo debe contener dígitos.')
        if len(numero) != self.LONGITUD:
            raise forms.ValidationError(f'El número debe tener exactamente {self.LONGITUD} dígitos.')
        return numero

    def clean_numero_documento(self):
        doc = (self.cleaned_data.get('numero_documento') or '').strip()
        if not doc:
            raise forms.ValidationError('El documento es obligatorio.')
        return doc
