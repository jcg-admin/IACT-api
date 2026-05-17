"""
Migration 0003 — FASE 1: Session canónica.

Crea el modelo Session con estado, close_reason, expires_at y client_info.

Hallazgo F1-H-002: SessionLog tenía estructura incompleta para UC_AUTH_01.
Se crea Session separada con todos los campos del modelo de dominio.

Fuente: modelo-dominio-iact.rst § 4.1, UC_AUTH_01 CAs 01-03.
"""
import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Session',
            fields=[
                ('session_id', models.UUIDField(
                    default=uuid.uuid4, editable=False,
                    primary_key=True, serialize=False,
                    verbose_name='Session ID',
                )),
                ('state', models.CharField(
                    choices=[
                        ('ACTIVE', 'Activa'),
                        ('CLOSED', 'Cerrada'),
                        ('EXPIRED', 'Expirada'),
                    ],
                    db_index=True, default='ACTIVE',
                    max_length=10, verbose_name='Estado',
                )),
                ('started_at', models.DateTimeField(
                    auto_now_add=True, verbose_name='Iniciada',
                )),
                ('last_activity_at', models.DateTimeField(
                    auto_now_add=True, verbose_name='Última actividad',
                )),
                ('expires_at', models.DateTimeField(
                    db_index=True, verbose_name='Expira',
                )),
                ('client_info', models.JSONField(
                    blank=True, default=dict, verbose_name='Info cliente',
                )),
                ('close_reason', models.CharField(
                    blank=True, default='', max_length=30,
                    verbose_name='Razón de cierre',
                )),
                ('closed_at', models.DateTimeField(
                    blank=True, null=True, verbose_name='Cerrada en',
                )),
                ('ip_address', models.GenericIPAddressField(
                    blank=True, null=True, verbose_name='IP',
                )),
                ('scope', models.CharField(
                    default='full', max_length=20, verbose_name='Scope',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='sessions',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Usuario',
                )),
            ],
            options={
                'verbose_name': 'Sesión',
                'verbose_name_plural': 'Sesiones',
                'db_table': 'authentication_session',
                'ordering': ['-started_at'],
            },
        ),
        migrations.AddIndex(
            model_name='session',
            index=models.Index(
                fields=['user', 'state'],
                name='idx_session_user_state',
            ),
        ),
        migrations.AddIndex(
            model_name='session',
            index=models.Index(
                fields=['state', 'expires_at'],
                name='idx_session_state_exp',
            ),
        ),
    ]
