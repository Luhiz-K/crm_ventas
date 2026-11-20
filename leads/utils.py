"""Funciones auxiliares compartidas por las vistas (sesión, enmascarado, etc.)."""

import unicodedata

from .models import Ciudad, Sede, Trabajador, Usuario

# Cargos del sistema, estandarizados para coincidir 1:1 por nombre con los roles.
CARGOS_SISTEMA = ['Asesor', 'Líder', 'Gerente', 'Gerente General', 'Customer', 'Jurídico']


def es_sistema_operativo():
    """True solo si existen los requisitos mínimos para operar un lead."""
    return Ciudad.objects.exists() and Sede.objects.exists() and Trabajador.objects.exists()


def trabajador_actual(request):
    """Devuelve el Trabajador de la persona del usuario logueado (o None)."""
    try:
        u = Usuario.objects.get(id_usuario=request.session.get('id_usuario'))
    except Usuario.DoesNotExist:
        return None
    return Trabajador.objects.filter(id_persona=u.id_persona).first()


def enmascarar(nombre_completo):
    """'Juan Perez' -> 'Ju** Pe**' (deja 2 letras visibles por palabra)."""
    partes = [p for p in nombre_completo.split() if p]
    return ' '.join(p[:2] + '*' * max(len(p) - 2, 2) for p in partes)


def _sin_tildes(texto):
    """Normaliza a minúsculas y elimina tildes y diacríticos."""
    base = unicodedata.normalize('NFKD', texto or '')
    return base.encode('ascii', 'ignore').decode('ascii').lower().strip()


def generar_username(nombres, apellidos):
    """Genera un nombre de usuario único a partir del nombre completo.

    Toma 2 letras del primer nombre, 2 del segundo (si existe) y 4 del primer
    apellido. Si el resultado ya está en uso, añade un sufijo numérico.
    """
    n = _sin_tildes(nombres).split()
    a = _sin_tildes(apellidos).split()
    base = (
        (n[0][:2] if n else '')
        + (n[1][:2] if len(n) > 1 else '')
        + (a[0][:4] if a else '')
    ) or 'usuario'
    username, i = base, 1
    while Usuario.objects.filter(username=username).exists():
        i += 1
        username = f"{base}{i}"
    return username
