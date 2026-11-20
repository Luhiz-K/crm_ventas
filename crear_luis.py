# crear_luis.py
# Script de un solo uso: crea el usuario de prueba "Luis" con rol Asesor.
# Ejecutar con:
#   python manage.py shell -c "exec(open('crear_luis.py', encoding='utf-8').read())"

from django.db import connection
from django.contrib.auth.hashers import make_password
from leads.models import Persona, Trabajador, Usuario, Sede, Cargo, Rol

# 1) Arreglamos los contadores (secuencias) por si quedaron desincronizados,
#    igual que hicimos con 'rol'. Asi el INSERT no choca con un id ya existente.
with connection.cursor() as cur:
    for tabla, col in [('persona', 'id_persona'),
                       ('trabajador', 'id_trabajador'),
                       ('usuario', 'id_usuario')]:
        cur.execute(
            f"SELECT setval(pg_get_serial_sequence('{tabla}', '{col}'), "
            f"COALESCE((SELECT MAX({col}) FROM {tabla}), 1))"
        )

# 2) Datos de referencia
sede = Sede.objects.first()                       # usamos la primera sede disponible
cargo = Cargo.objects.get(nombre_cargo='Asesor')  # cargo (puesto) = Asesor
rol = Rol.objects.get(nombre_rol='Asesor')        # rol  (acceso) = Asesor

# 3) Persona (el ser humano Luis)
persona, nueva_p = Persona.objects.get_or_create(
    numero_documento_persona='1030565674',
    defaults={'nombres': 'Luis Carlos', 'apellidos': 'Sanabria'},
)

# 4) Trabajador (Luis como empleado de una sede)
trab, nuevo_t = Trabajador.objects.get_or_create(
    id_persona=persona,
    defaults={'id_sede': sede, 'id_cargo': cargo},
)

# 5) Usuario (sus credenciales de acceso)
usuario, nuevo_u = Usuario.objects.get_or_create(
    username='luis',
    defaults={
        'id_persona': persona,
        'id_rol': rol,
        'password_hash': make_password('Deudoor2026'),
        'estado_usuario': 'Activo',
    },
)

print('--------------------------------------------')
print('Sede asignada :', sede.nombre_sede if sede else 'NINGUNA')
print('Persona       :', persona.nombres, persona.apellidos, '| creada ahora:', nueva_p)
print('Trabajador id :', trab.id_trabajador, '| creado ahora:', nuevo_t)
print('Usuario       :', usuario.username, '| rol:', rol.nombre_rol, '| creado ahora:', nuevo_u)
print('LISTO -> entra con  luis / Deudoor2026')
print('--------------------------------------------')
