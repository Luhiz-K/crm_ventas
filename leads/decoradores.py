# leads/decoradores.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def rol_requerido(*roles):
    """Permite la vista solo si el rol guardado en la sesion esta en `roles`.
    Si no, devuelve al panel con un aviso. El login ya lo exige el middleware;
    esto agrega la capa de ROL encima."""
    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if request.session.get('rol') not in roles:
                messages.error(request, 'No tienes permiso para acceder a esa sección.')
                return redirect('panel_control')
            return vista(request, *args, **kwargs)
        return envoltura
    return decorador
