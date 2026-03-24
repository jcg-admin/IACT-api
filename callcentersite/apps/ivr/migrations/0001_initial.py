# Generated 2026-03-21 — TblTempPruebaIvr (managed=False)

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='TblTempPruebaIvr',
            fields=[
                ('id',     models.AutoField(primary_key=True, serialize=False)),
                ('numero', models.CharField(max_length=10)),
            ],
            options={
                'verbose_name':        'Temp Prueba IVR',
                'verbose_name_plural': 'Temp Prueba IVR',
                'db_table': 'tbl_temp_prueba_ivr',
                'ordering': ['id'],
                'managed':  False,
            },
        ),
    ]
