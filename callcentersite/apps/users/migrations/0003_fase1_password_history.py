"""
Migration 0003 — FASE 1: PasswordHistory + password_changed_at.

PasswordHistory: historial de contraseñas para verificar reuso (UC_AUTH_04 PASO 9).
password_changed_at: timestamp del último cambio (UC_AUTH_04 PASO 10).

Hallazgo F1-H-008: ambos inexistentes — UC_AUTH_04 no podía implementarse.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_fase1_user_canonical_fields'),
    ]

    operations = [
        # password_changed_at en User (UC_AUTH_04 PASO 10)
        migrations.AddField(
            model_name='user',
            name='password_changed_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Contraseña cambiada en',
                help_text='UC_AUTH_04 PASO 10: actualizado al cambiar contraseña.',
            ),
        ),
        # PasswordHistory model (UC_AUTH_04 PASO 11)
        migrations.CreateModel(
            name='PasswordHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('password_hash', models.CharField(
                    max_length=128,
                    verbose_name='Hash de contraseña',
                    help_text='Hash bcrypt. Nunca en texto plano.',
                )),
                ('changed_at', models.DateTimeField(auto_now_add=True, verbose_name='Cambiada en')),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='password_history',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Usuario',
                )),
            ],
            options={
                'verbose_name': 'Historial de contraseña',
                'verbose_name_plural': 'Historial de contraseñas',
                'db_table': 'users_password_history',
                'ordering': ['-changed_at'],
            },
        ),
        migrations.AddIndex(
            model_name='passwordhistory',
            index=models.Index(
                fields=['user', '-changed_at'],
                name='idx_pwhistory_user_date',
            ),
        ),
    ]
