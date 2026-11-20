"""Middleware de control de sesión.

Exige una sesión activa para acceder a las rutas privadas del sitio. Las rutas
públicas (login/logout, APIs con JWT, admin, estáticos y media) quedan exentas.
"""

from django.shortcuts import redirect

# Prefijos de ruta que no requieren sesión de usuario.
PREFIJOS_PUBLICOS = (
    '/leads/login/',
    '/leads/logout/',
    '/leads/api/',
    '/admin/',
    '/media/',
    '/static/',
)


class SesionRequeridaMiddleware:
    def __init__(self, get_response):
        # Inicialización única al arrancar el servidor.
        self.get_response = get_response

    def __call__(self, request):
        # Se ejecuta en cada petición, antes de resolver la vista.
        ruta = request.path
        es_publica = ruta.startswith(PREFIJOS_PUBLICOS)
        hay_sesion = request.session.get('id_usuario') is not None

        # Petición privada sin sesión: redirige al login.
        if not es_publica and not hay_sesion:
            return redirect('login')

        # Ruta pública o sesión válida: continúa el flujo normal.
        return self.get_response(request)
