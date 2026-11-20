from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0005_buro_reportegrafico_id_buro_usuarioreporte_id_buro'),
    ]

    operations = [
        # 1. Renombra el modelo (no toca los datos)
        migrations.RenameModel(
            old_name='FechasPago',
            new_name='CuotaEstado',
        ),
        # 2. Renombra la tabla fisica (ALTER TABLE ... RENAME TO), conserva filas
        migrations.AlterModelTable(
            name='cuotaestado',
            table='cuotas_estados',
        ),
        # 3. Quita las columnas que ahora viven en pagos_realizados
        migrations.RemoveField(
            model_name='cuotaestado',
            name='valor_pagado',
        ),
        migrations.RemoveField(
            model_name='cuotaestado',
            name='fecha_pagado',
        ),
        # 4. Crea la tabla nueva de pagos reales
        migrations.CreateModel(
            name='PagoRealizado',
            fields=[
                ('id_pago', models.AutoField(primary_key=True, serialize=False)),
                ('valor_pago', models.DecimalField(decimal_places=2, max_digits=15)),
                ('fecha_pago', models.DateField()),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('id_cuota', models.ForeignKey(db_column='id_cuota', on_delete=django.db.models.deletion.CASCADE, to='leads.cuotaestado')),
                ('id_trabajador', models.ForeignKey(blank=True, db_column='id_trabajador', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='leads.trabajador')),
            ],
            options={
                'db_table': 'pagos_realizados',
            },
        ),
    ]
