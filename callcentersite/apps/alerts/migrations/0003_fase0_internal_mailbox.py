"""
Migration 0003 — FASE 0: InternalMailbox y MailboxMessage.

Crea los modelos del buzón interno de cada usuario.

Fuente: modelo-dominio-iact.rst § 4.1 (BC Auth), CNST-001, BR-004.
Hallazgo F0-H-005: InternalMailbox no existía — prerequisito de
UC_USR_01 CA-01, UC_AUTH_01 FA-01, UC_AUTH_03 CA-01, UC_ALR_05.
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='InternalMailbox',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_read_at', models.DateTimeField(blank=True, null=True, verbose_name='Última lectura')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creado')),
                ('owner', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='mailbox',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Propietario',
                )),
            ],
            options={
                'verbose_name': 'Buzón interno',
                'verbose_name_plural': 'Buzones internos',
                'db_table': 'alerts_internal_mailbox',
            },
        ),
        migrations.CreateModel(
            name='MailboxMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=200, verbose_name='Asunto')),
                ('body', models.TextField(verbose_name='Contenido')),
                ('priority', models.CharField(
                    choices=[('info', 'Informativo'), ('warning', 'Advertencia'),
                             ('error', 'Error'), ('critical', 'Crítico')],
                    default='info',
                    max_length=10,
                    verbose_name='Prioridad',
                )),
                ('state', models.CharField(
                    choices=[('UNREAD', 'Sin leer'), ('READ', 'Leído'), ('DELETED', 'Eliminado')],
                    default='UNREAD',
                    max_length=10,
                    verbose_name='Estado',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creado')),
                ('read_at', models.DateTimeField(blank=True, null=True, verbose_name='Leído en')),
                ('mailbox', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='messages',
                    to='alerts.internalmailbox',
                    verbose_name='Buzón',
                )),
                ('sender', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='mailbox_messages_sent',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Remitente',
                )),
            ],
            options={
                'verbose_name': 'Mensaje de buzón',
                'verbose_name_plural': 'Mensajes de buzón',
                'db_table': 'alerts_mailbox_message',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='mailboxmessage',
            index=models.Index(fields=['mailbox', 'state'], name='idx_mbmsg_mailbox_state'),
        ),
        migrations.AddIndex(
            model_name='mailboxmessage',
            index=models.Index(fields=['-created_at'], name='idx_mbmsg_created'),
        ),
    ]
