"""Autenticación web por sesión (login y logout)."""

from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password
from ..models import Usuario


def login_web(request):
    # Con sesión activa, omite el formulario y va al panel.
    if request.session.get('id_usuario'):
        return redirect('panel_control')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        try:
            usuario = Usuario.objects.select_related('id_rol', 'id_persona').get(username=username)

            # Usuario desactivado.
            if usuario.estado_usuario and usuario.estado_usuario.lower() != 'activo':
                error = 'Tu usuario está inactivo. Contacta al administrador.'

            # Verifica la contraseña contra el hash almacenado.
            elif check_password(password, usuario.password_hash):
                # Credenciales válidas: inicia la sesión.
                request.session.cycle_key()  # Nueva llave de sesión (evita fijación).
                request.session['id_usuario'] = usuario.id_usuario
                request.session['rol'] = usuario.id_rol.nombre_rol
                request.session['nombre'] = usuario.id_persona.nombres
                return redirect('panel_control')

            else:
                error = 'Usuario o contraseña incorrectos.'

        except Usuario.DoesNotExist:
            # Mensaje genérico a propósito: no revela si el usuario existe.
            error = 'Usuario o contraseña incorrectos.'

    return render(request, 'leads/login.html', {'error': error})


def logout_web(request):
    request.session.flush()  # Elimina la sesión del lado del servidor.
    return redirect('login')
