import django.utils.timezone
"""
Migration 0005 — FASE 0: Schema canónico v5.4.0.

Cambios:
1. SeparationRule — reestructuración completa:
   - Elimina FKs binarios (function_a, function_b)
   - Elimina constraint unique_separation_pair_active
   - Agrega code (canónico: SOD-001..003)
   - Agrega M2M functions_set_a y functions_set_b (SoD grupal)
   - Cambia state choices: active/suspended → ENABLED/DISABLED (BR-009)
   - Agrega created_at, updated_at

2. UserFunctionAssignment — estado canónico:
   - Agrega state: ACTIVE/EXPIRED/REVOKED (BR-009, Assignment en modelo-dominio)
   - Agrega expires_at (UC_ACC_01 CA-02, UC_PERM_07 CA-06/07/17)
   - Agrega revoked_at, revoked_by, revoke_reason (UC_ACC_02)

Fuentes:
- modelo-rbac-iact.rst v5.4.0
- modelo-dominio-iact.rst § 4.2 (Assignment class)
- BR-007 (SoD), BR-009 (bajas lógicas)
- UC_ACC_01 CA-02, UC_ACC_02 CA-01/CA-02, UC_PERM_07 CA-05..07
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('access', '0004_add_menuitem'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ================================================================
        # 1. SeparationRule — reestructuración completa
        # ================================================================

        # 1a. Eliminar constraint binario (depende de function_a/b que se van)
        migrations.RemoveConstraint(
            model_name='separationrule',
            name='unique_separation_pair_active',
        ),

        # 1b. Eliminar FKs binarios
        migrations.RemoveField(
            model_name='separationrule',
            name='function_a',
        ),
        migrations.RemoveField(
            model_name='separationrule',
            name='function_b',
        ),

        # 1c. Eliminar campo status (choices: active/suspended/deleted)
        migrations.RemoveField(
            model_name='separationrule',
            name='status',
        ),

        # 1d. Eliminar is_active (del SoftDeleteModel que ya no hereda)
        migrations.RemoveField(
            model_name='separationrule',
            name='is_active',
        ),

        # 1e. Eliminar created_at, updated_at del SoftDeleteModel (se van a volver a agregar)
        migrations.RemoveField(
            model_name='separationrule',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='separationrule',
            name='updated_at',
        ),

        # 1f. Eliminar justification (renombrado a description, ver abajo)
        migrations.RemoveField(
            model_name='separationrule',
            name='justification',
        ),

        # 1g. Agregar code canónico (SOD-001, SOD-002, SOD-003)
        migrations.AddField(
            model_name='separationrule',
            name='code',
            field=models.CharField(
                default='SOD-TEMP',
                help_text='Identificador canónico. Ej: SOD-001.',
                max_length=20,
                verbose_name='Codigo',
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='separationrule',
            name='code',
            field=models.CharField(
                help_text='Identificador canónico. Ej: SOD-001.',
                max_length=20,
                unique=True,
                verbose_name='Codigo',
            ),
        ),

        # 1h. Agregar description (era justification)
        migrations.AddField(
            model_name='separationrule',
            name='description',
            field=models.TextField(
                blank=True,
                verbose_name='Descripcion',
                help_text='Razon de negocio.',
            ),
        ),

        # 1i. Agregar state canónico: ENABLED/DISABLED (BR-009)
        migrations.AddField(
            model_name='separationrule',
            name='state',
            field=models.CharField(
                choices=[('ENABLED', 'Enabled'), ('DISABLED', 'Disabled')],
                default='ENABLED',
                max_length=10,
                verbose_name='Estado',
                help_text='ENABLED | DISABLED. BR-009: nunca DELETE.',
            ),
        ),

        # 1j. Agregar timestamps
        migrations.AddField(
            model_name='separationrule',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True,
                verbose_name='Creado',
                default=django.utils.timezone.now,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='separationrule',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Actualizado'),
        ),

        # 1k. Agregar M2M funciones_set_a y functions_set_b
        migrations.AddField(
            model_name='separationrule',
            name='functions_set_a',
            field=models.ManyToManyField(
                blank=True,
                related_name='sod_rules_as_set_a',
                to='access.function',
                verbose_name='Conjunto A',
            ),
        ),
        migrations.AddField(
            model_name='separationrule',
            name='functions_set_b',
            field=models.ManyToManyField(
                blank=True,
                related_name='sod_rules_as_set_b',
                to='access.function',
                verbose_name='Conjunto B',
            ),
        ),

        # ================================================================
        # 2. UserFunctionAssignment — estado canónico
        # ================================================================

        # 2a. Agregar state: ACTIVE/EXPIRED/REVOKED
        migrations.AddField(
            model_name='userfunctionassignment',
            name='state',
            field=models.CharField(
                choices=[
                    ('ACTIVE', 'Active'),
                    ('EXPIRED', 'Expired'),
                    ('REVOKED', 'Revoked'),
                ],
                default='ACTIVE',
                max_length=10,
                verbose_name='Estado',
                help_text='ACTIVE | EXPIRED | REVOKED. BR-009: nunca DELETE.',
                db_index=True,
            ),
        ),

        # 2b. Agregar expires_at (UC_ACC_01 CA-02, UC_PERM_07 CA-06)
        migrations.AddField(
            model_name='userfunctionassignment',
            name='expires_at',
            field=models.DateTimeField(
                null=True,
                blank=True,
                verbose_name='Expira en',
                help_text='Nullable: sin fecha no expira.',
                db_index=True,
            ),
        ),

        # 2c. Agregar revoked_at (UC_ACC_02)
        migrations.AddField(
            model_name='userfunctionassignment',
            name='revoked_at',
            field=models.DateTimeField(
                null=True,
                blank=True,
                verbose_name='Revocada en',
            ),
        ),

        # 2d. Agregar revoked_by (UC_ACC_02)
        migrations.AddField(
            model_name='userfunctionassignment',
            name='revoked_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='function_assignments_revoked',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Revocada por',
            ),
        ),

        # 2e. Agregar revoke_reason (UC_ACC_02)
        migrations.AddField(
            model_name='userfunctionassignment',
            name='revoke_reason',
            field=models.CharField(
                blank=True,
                max_length=500,
                verbose_name='Motivo de revocacion',
                help_text='UC_ACC_02: obligatorio al revocar.',
            ),
        ),

        # 2f. Agregar índice compuesto user+state
        migrations.AddIndex(
            model_name='userfunctionassignment',
            index=models.Index(
                fields=['user', 'state'],
                name='idx_ufassign_user_state',
            ),
        ),
        migrations.AddIndex(
            model_name='userfunctionassignment',
            index=models.Index(
                fields=['state', 'expires_at'],
                name='idx_ufassign_state_expires',
            ),
        ),
    ]
