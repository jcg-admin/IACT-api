"""
Migration 0004 — FASE 2: campos de administración en User.

Agrega campos requeridos por UC_USR_01, UC_USR_03 y UC_USR_04:
  - state += ELIMINATED (UC_USR_04)
  - created_by_admin_id (UC_USR_01 PASO 10)
  - last_modified_at, last_modified_by_admin_id (UC_USR_03 PASO 8)
  - eliminated_at, eliminated_by_admin_id (UC_USR_04 CA-01)
  - state_changed_at (UC_USR_03 PASO 8)

Hallazgo F2-H-002: ELIMINATED ausente en User.state.
Hallazgo F2-H-003: cinco campos de auditoría de ciclo de vida inexistentes.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_fase1_password_history'),
    ]

    operations = [
        # 1. Agregar ELIMINATED a state choices (solo cambio de choices en Python
        #    el ALTER COLUMN no es necesario en SQLite/PostgreSQL si max_length suficiente)
        migrations.AlterField(
            model_name='user',
            name='state',
            field=models.CharField(
                choices=[
                    ('ACTIVE',     'Activo'),
                    ('INACTIVE',   'Inactivo'),
                    ('BLOCKED',    'Bloqueado'),
                    ('ELIMINATED', 'Eliminado'),
                ],
                db_index=True,
                default='ACTIVE',
                max_length=10,
                verbose_name='Estado',
                help_text='Estado canónico. ELIMINATED = baja lógica (BR-009).',
            ),
        ),
        # 2. Trazabilidad de creación (UC_USR_01 PASO 10)
        migrations.AddField(
            model_name='user',
            name='created_by_admin',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='users_created',
                to=settings.AUTH_USER_MODEL,
                null=True,
                blank=True,
                verbose_name='Creado por admin',
                help_text='Admin que creó la cuenta. UC_USR_01 PASO 10.',
            ),
        ),
        # 3. Trazabilidad de modificación (UC_USR_03)
        migrations.AddField(
            model_name='user',
            name='last_modified_at',
            field=models.DateTimeField(
                null=True,
                blank=True,
                verbose_name='Última modificación',
                help_text='UC_USR_03 PASO 8: actualizado en cada PATCH.',
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='last_modified_by_admin',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='users_modified',
                to=settings.AUTH_USER_MODEL,
                null=True,
                blank=True,
                verbose_name='Modificado por admin',
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='state_changed_at',
            field=models.DateTimeField(
                null=True,
                blank=True,
                verbose_name='Estado cambiado en',
                help_text='UC_USR_03: solo si state cambia.',
            ),
        ),
        # 4. Trazabilidad de eliminación (UC_USR_04)
        migrations.AddField(
            model_name='user',
            name='eliminated_at',
            field=models.DateTimeField(
                null=True,
                blank=True,
                verbose_name='Eliminado en',
                help_text='UC_USR_04 CA-01.',
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='eliminated_by_admin',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='users_eliminated',
                to=settings.AUTH_USER_MODEL,
                null=True,
                blank=True,
                verbose_name='Eliminado por admin',
            ),
        ),
    ]
