# crear_base_prueba.py — PROTOCOLO DE CREACION
# Crea 2 usuarios de prueba + un catalogo de ciudades de Colombia.
# Ejecutar:  python manage.py shell -c "exec(open('crear_base_prueba.py', encoding='utf-8').read())"

from django.contrib.auth.hashers import make_password
from leads.models import Persona, Trabajador, Usuario, Rol, Cargo, Telefonos, Ciudad

# --- 1. Catalogo de ciudades de Colombia (capitales de departamento + principales) ---
CIUDADES = [
    'Bogotá', 'Medellín', 'Cali', 'Barranquilla', 'Cartagena', 'Cúcuta', 'Bucaramanga',
    'Pereira', 'Santa Marta', 'Ibagué', 'Manizales', 'Villavicencio', 'Neiva', 'Pasto',
    'Armenia', 'Montería', 'Sincelejo', 'Popayán', 'Valledupar', 'Tunja', 'Riohacha',
    'Florencia', 'Yopal', 'Quibdó', 'Mocoa', 'Arauca', 'San José del Guaviare',
    'Leticia', 'Inírida', 'Mitú', 'Puerto Carreño', 'Soacha', 'Soledad', 'Bello',
    'Palmira', 'Buenaventura', 'Dosquebradas', 'Girardot',
]
for nombre in CIUDADES:
    Ciudad.objects.get_or_create(ciudad=nombre)

# --- 2. Cargos basicos (por si acaso) ---
for cargo in ['Asesor', 'Coach', 'Gerente Sede', 'Calidad', 'Gerente General']:
    Cargo.objects.get_or_create(nombre_cargo=cargo, defaults={'descripcion_cargo': f'Cargo {cargo}'})


# --- 3. Creacion de un usuario-trabajador ---
def crear_usuario(nombres, apellidos, documento, correo, telefono, rol_nombre, cargo_nombre, username, clave):
    persona, _ = Persona.objects.get_or_create(
        numero_documento_persona=documento,
        defaults={'nombres': nombres, 'apellidos': apellidos, 'correo_persona': correo}
    )
    cargo = Cargo.objects.filter(nombre_cargo=cargo_nombre).first()
    Trabajador.objects.get_or_create(id_persona=persona, defaults={'id_cargo': cargo})  # sin sede todavia
    Telefonos.objects.get_or_create(
        numero_telefono=telefono, tipo_telefono='Principal',
        defaults={'id_persona': persona}
    )
    rol = Rol.objects.get(nombre_rol=rol_nombre)
    Usuario.objects.get_or_create(
        username=username,
        defaults={'id_persona': persona, 'id_rol': rol,
                  'password_hash': make_password(clave), 'estado_usuario': 'Activo'}
    )
    print(f'  Usuario "{username}" ({rol_nombre}) listo.')


print('Creando usuarios de prueba...')
crear_usuario('Maria Isabel', 'Toro Parra', '1030568955', 'maria.toro@gmail.com', '3134326232',
              'Gerente General', 'Gerente General', 'maria', 'Deudoor2026')
crear_usuario('Luis Carlos', 'Sanabria Acevedo', '1030565674', 'recolectorwow@gmail.com', '3155552575',
              'Asesor', 'Asesor', 'luis', 'Deudoor2026')

print(f'LISTO. Ciudades: {Ciudad.objects.count()} | Usuarios: {Usuario.objects.count()}')
print('Entra con  maria / Deudoor2026   o   luis / Deudoor2026')
