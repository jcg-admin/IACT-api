"""
Migration 0004 — FASE 2: BlacklistedToken.

Crea el modelo BlacklistedToken que UC_AUTH_02 (logout) requiere
para invalidar tokens JWT tras el cierre de sesión.

Fuente: uc-auth-02/datos-involucrados.rst § 7.4.2
  - jti: JWT ID (claim 'jti'), UNIQUE
  - token_type: 'ACCESS' | 'REFRESH'
  - expires_at: cuando expira el token original
  - blacklisted_at: cuando se añadió al blacklist

Hallazgo F2-H-001: BlacklistedToken no existía en ningún archivo.
UC_AUTH_02 pasos 6-8 son imposibles sin él.
"""
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0003_fase1_session'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlacklistedToken',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True, serialize=False,
                )),
                ('jti', models.CharField(
                    max_length=255,
                    unique=True,
                    verbose_name='JWT ID (jti)',
                    help_text='Claim jti del token. UNIQUE para detección O(1).',
                )),
                ('token_type', models.CharField(
                    max_length=10,
                    choices=[('ACCESS', 'Access token'), ('REFRESH', 'Refresh token')],
                    verbose_name='Tipo de token',
                )),
                ('expires_at', models.DateTimeField(
                    verbose_name='Expira en',
                    help_text='Fecha de expiración original del token.',
                    db_index=True,
                )),
                ('blacklisted_at', models.DateTimeField(
                    auto_now_add=True,
                    verbose_name='Blacklisteado en',
                )),
                ('user', models.ForeignKey(
                    on_delete=models.CASCADE,
                    related_name='blacklisted_tokens',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Usuario',
                    null=True,
                    blank=True,
                )),
            ],
            options={
                'verbose_name': 'Token blacklisteado',
                'verbose_name_plural': 'Tokens blacklisteados',
                'db_table': 'authentication_blacklisted_token',
                'ordering': ['-blacklisted_at'],
            },
        ),
        migrations.AddIndex(
            model_name='blacklistedtoken',
            index=models.Index(
                fields=['jti'],
                name='idx_blacklist_jti',
            ),
        ),
        migrations.AddIndex(
            model_name='blacklistedtoken',
            index=models.Index(
                fields=['expires_at'],
                name='idx_blacklist_expires',
            ),
        ),
    ]
