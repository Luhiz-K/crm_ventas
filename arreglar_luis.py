# arreglar_luis.py
# Corrige el enredo: el usuario 'luis' quedo enlazado a 'pepito perez',
# porque el documento 1030565674 ya existia y get_or_create REUTILIZO esa
# persona en vez de crear una nueva. Aqui le damos su propia persona a Luis.

from leads.models import Persona, Trabajador, Usuario

# 1) Buscamos un documento LIBRE para Luis (si 1030565674 esta ocupado, le sumamos 9s)
doc = '1030565674'
while Persona.objects.filter(numero_documento_persona=doc).exists():
    doc += '9'

# 2) Creamos la persona REAL de Luis
luis = Persona.objects.create(
    nombres='Luis Carlos',
    apellidos='Sanabria',
    numero_documento_persona=doc,
)

# 3) El usuario 'luis' y su trabajador apuntaban a la persona equivocada (pepito).
u = Usuario.objects.get(username='luis')
persona_mala = u.id_persona            # pepito perez

u.id_persona = luis                    # reapuntamos el USUARIO a Luis
u.save()

t = Trabajador.objects.filter(id_persona=persona_mala).first()
if t:
    t.id_persona = luis                # el TRABAJADOR tambien pasa a Luis
    t.save()

print('--------------------------------------------')
print('Documento usado para Luis :', doc)
print('Antes, usuario luis era   :', persona_mala.nombres, persona_mala.apellidos)
print('Ahora, usuario luis es    :', u.id_persona.nombres, u.id_persona.apellidos)
print('pepito perez vuelve a ser solo cliente (ya no es trabajador).')
print('LISTO.')
print('--------------------------------------------')
