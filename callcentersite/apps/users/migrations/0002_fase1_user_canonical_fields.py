"""
Migration 0002 — FASE 1: Campos canónicos del modelo User.

Agrega los campos requeridos por el modelo de dominio
(modelo-dominio-iact.rst § 4.1) y los UCs de FASE 1:

- state: ACTIVE/INACTIVE/BLOCKED (BR-009 baja lógica)
- first_login: bool (UC_AUTH_01 FA-01, UC_AUTH_04)
- password_expires_at: datetime nullable (UC_AUTH_01 FA-02)
- last_login_at: datetime nullable (UC_AUTH_01 paso 14)

Hallazgo F1-H-001: estos campos no existían en el modelo User.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='state',
            field=models.CharField(
                choices=[
                    ('ACTIVE',   'Activo'),
                    ('INACTIVE', 'Inactivo'),
                    ('BLOCKED',  'Bloqueado'),
                ],
                db_index=True,
                default='ACTIVE',
                help_text='Estado canónico del usuario.',
                max_length=10,
                verbose_name='Estado',
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='first_login',
            field=models.BooleanField(
                default=True,
                help_text='True al crear la cuenta. Fuerza cambio de contraseña.',
                verbose_name='Primer login',
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='password_expires_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Aviso de expiración próxima.',
                verbose_name='Contraseña expira',
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='last_login_at',
            field=models.DateTimeField(
                blank=True,
                db_index=True,
                null=True,
                help_text='Actualizado en cada login exitoso.',
                verbose_name='Último login',
            ),
        ),
    ]
