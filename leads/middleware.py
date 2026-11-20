# leads/middleware.py
from django.shortcuts import redirect

# Rutas que NO exigen sesión: el propio login/logout, las APIs (usan su JWT),
# el admin de Django, y los archivos estáticos/subidos.
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
        # Django ejecuta esto UNA sola vez, al arrancar el servidor.
        self.get_response = get_response

    def __call__(self, request):
        # Esto corre en CADA petición, ANTES de llegar a la vista.
        ruta = request.path
        es_publica = ruta.startswith(PREFIJOS_PUBLICOS)
        hay_sesion = request.session.get('id_usuario') is not None

        # Sin sesión y pidiendo algo privado -> lo mandamos al login.
        if not es_publica and not hay_sesion:
            return redirect('login')

        # Con sesión (o ruta pública) -> que siga su camino normal.
        return self.get_response(request)
