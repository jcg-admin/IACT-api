from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('access', '0003_add_access_group_separation_rule_exceptional_permission'),
    ]

    operations = [
        migrations.CreateModel(
            name='MenuItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('display_label', models.CharField(max_length=100, verbose_name='Etiqueta')),
                ('icon', models.CharField(blank=True, default='', max_length=100, verbose_name='Icono')),
                ('route', models.CharField(blank=True, default='', max_length=200, verbose_name='Ruta')),
                ('order', models.PositiveSmallIntegerField(default=0, verbose_name='Orden')),
                ('status', models.CharField(
                    choices=[
                        ('DRAFT', 'Draft'),
                        ('ACTIVE', 'Active'),
                        ('DEPRECATED', 'Deprecated'),
                        ('ARCHIVED', 'Archived'),
                    ],
                    default='DRAFT',
                    max_length=20,
                    verbose_name='Estado',
                )),
                ('deprecated_at', models.DateTimeField(blank=True, null=True, verbose_name='Fecha deprecación')),
                ('archived_at', models.DateTimeField(blank=True, null=True, verbose_name='Fecha archivo')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('function', models.OneToOneField(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='menu_item',
                    to='access.function',
                    verbose_name='Función',
                )),
                ('parent', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='children',
                    to='access.menuitem',
                    verbose_name='Padre',
                )),
            ],
            options={
                'verbose_name': 'Item de menú',
                'verbose_name_plural': 'Items de menú',
                'db_table': 'access_menu_item',
                'ordering': ['order'],
            },
        ),
    ]
