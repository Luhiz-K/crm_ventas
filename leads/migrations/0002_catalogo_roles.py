# leads/migrations/0002_catalogo_roles.py
from django.db import migrations

ROLES = [
    ("Asesor",          "Realiza la venta y crea los leads. Ve únicamente los suyos."),
    ("Líder",           "Monitorea a su equipo y puede crear leads. No edita datos sensibles."),
    ("Gerente",         "Responsable de una sede: ve y edita las ventas de su sede."),
    ("Gerente General", "Superusuario: crea roles y usuarios, y otorga o quita privilegios."),
    ("Customer",        "Valida documentación y contrato; puede editar la información de todos."),
    ("Jurídico",        "Sube y envía documentación a las entidades; puede editar la de todos."),
    ("Cliente",         "Usuario de la app: ve su caso, sube documentos, firma y paga."),
]

def cargar_roles(apps, schema_editor):
    Rol = apps.get_model('leads', 'Rol')
    # Estandarizamos los que ya existen (sin romper el vínculo de MariA)
    Rol.objects.filter(nombre_rol='Admin').update(nombre_rol='Gerente General')
    Rol.objects.filter(nombre_rol='Agente').update(nombre_rol='Asesor')
    # Garantizamos que existan los 7 roles con su descripción
    for nombre, desc in ROLES:
        Rol.objects.update_or_create(nombre_rol=nombre, defaults={'descripcion_rol': desc})

class Migration(migrations.Migration):
    dependencies = [('leads', '0001_initial')]
    operations = [migrations.RunPython(cargar_roles)]
