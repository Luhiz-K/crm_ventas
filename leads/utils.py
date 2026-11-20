"""Funciones auxiliares compartidas por las vistas (sesión, enmascarado, etc.)."""

from .models import Ciudad, Sede, Trabajador, Usuario


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
