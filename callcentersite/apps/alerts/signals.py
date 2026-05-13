"""
apps/alerts/signals.py

Señales Django para el módulo de Alertas.

F0-T4: Signal que crea InternalMailbox automáticamente al crear un User.

Fuente: modelo-dominio-iact.rst § 4.1 — User 1:1 InternalMailbox.
CNST-001: el buzón es la única vía de comunicación interna.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_mailbox(sender, instance, created, **kwargs):
    """
    Crea InternalMailbox cuando se crea un nuevo User.

    Por qué post_save y no pre_save: la FK de InternalMailbox → User
    requiere que el User ya tenga pk asignado.

    Por qué created=True check: actualizar un User no debe crear un
    nuevo buzón si ya existe.
    """
    if created:
        from apps.alerts.models import InternalMailbox
        InternalMailbox.objects.get_or_create(owner=instance)
