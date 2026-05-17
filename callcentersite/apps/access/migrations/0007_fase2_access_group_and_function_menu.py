"""
Migration 0007 — FASE 2: AccessGroup.is_predefined + Function menu fields.

AccessGroup.is_predefined (F2-H-005):
  UC_PERM_05 CA-07: los AGRs predefinidos no pueden modificarse ni retirarse.
  Los 10 AGRs del catálogo v5.4.0 son predefinidos; los que crea UC_PERM_05 no.

Function menu fields (F2-H-004):
  UC_PERM_08 necesita metadata de navegación en cada Function para construir
  el menú dinámico. Sin estos campos, MenuBuilder no puede funcionar.
  Fuente: uc-perm-08/datos-involucrados.rst § 7.3

UserFunctionAssignment unique_together removido (F2-H-006):
  CA-21 de UC_ACC_01 requiere crear un NUEVO Assignment tras revocación,
  preservando el REVOKED como historial. El unique_together (user, function)
  lo bloquea. Se reemplaza por un índice parcial (solo sobre ACTIVE).
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('access', '0006_fase0_sql_functions_postgresql'),
    ]

    operations = [
        # 1. AccessGroup.is_predefined (F2-H-005)
        migrations.AddField(
            model_name='accessgroup',
            name='is_predefined',
            field=models.BooleanField(
                default=False,
                verbose_name='Predefinido',
                help_text=(
                    'True para los 10 AGRs del catálogo v5.4.0. '
                    'UC_PERM_05 CA-07: los predefinidos son inmutables.'
                ),
                db_index=True,
            ),
        ),
        migrations.AlterField(
            model_name='accessgroup',
            name='is_active',
            field=models.BooleanField(
                default=True,
                verbose_name='Activo',
                help_text='BR-009: desactivar en lugar de eliminar.',
                db_index=True,
            ),
        ),
        migrations.AddField(
            model_name='accessgroup',
            name='retired_at',
            field=models.DateTimeField(
                null=True,
                blank=True,
                verbose_name='Retirado en',
                help_text='UC_PERM_05 CA-08: set cuando is_active=False.',
            ),
        ),
        migrations.AddField(
            model_name='accessgroup',
            name='retire_reason',
            field=models.CharField(
                max_length=500,
                blank=True,
                default='',
                verbose_name='Razón de retiro',
            ),
        ),
        # 2. Function — campos de menú (F2-H-004)
        migrations.AddField(
            model_name='function',
            name='menu_visible',
            field=models.BooleanField(
                default=False,
                verbose_name='Visible en menú',
                help_text='UC_PERM_08 CA-05: False → no aparece aunque el usuario tenga el permiso.',
            ),
        ),
        migrations.AddField(
            model_name='function',
            name='menu_domain',
            field=models.CharField(
                max_length=50,
                blank=True,
                default='',
                verbose_name='Dominio de menú',
                help_text='Ej: vistas, administracion. Nivel 1 del árbol.',
            ),
        ),
        migrations.AddField(
            model_name='function',
            name='menu_section',
            field=models.CharField(
                max_length=50,
                blank=True,
                default='',
                verbose_name='Sección de menú',
                help_text='Ej: dashboards, usuarios. Nivel 2 del árbol.',
            ),
        ),
        migrations.AddField(
            model_name='function',
            name='menu_action',
            field=models.CharField(
                max_length=50,
                blank=True,
                default='',
                verbose_name='Acción de menú',
                help_text='Ej: ver, exportar. Nivel 3 del árbol.',
            ),
        ),
        migrations.AddField(
            model_name='function',
            name='menu_label_es',
            field=models.CharField(
                max_length=100,
                blank=True,
                default='',
                verbose_name='Etiqueta (ES)',
            ),
        ),
        migrations.AddField(
            model_name='function',
            name='menu_label_en',
            field=models.CharField(
                max_length=100,
                blank=True,
                default='',
                verbose_name='Etiqueta (EN)',
            ),
        ),
        migrations.AddField(
            model_name='function',
            name='menu_icon',
            field=models.CharField(
                max_length=100,
                blank=True,
                default='',
                verbose_name='Icono de menú',
            ),
        ),
        migrations.AddField(
            model_name='function',
            name='menu_order',
            field=models.PositiveSmallIntegerField(
                default=0,
                verbose_name='Orden en menú',
            ),
        ),
        # 3. UserFunctionAssignment — remover unique_together (F2-H-006)
        #    CA-21 de UC_ACC_01: un usuario puede tener múltiples registros
        #    (user, function) con states REVOKED + ACTIVE como historial.
        migrations.AlterUniqueTogether(
            name='userfunctionassignment',
            unique_together=set(),
        ),
    ]
