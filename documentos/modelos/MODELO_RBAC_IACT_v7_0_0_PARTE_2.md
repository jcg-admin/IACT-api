# MODELO RBAC IACT v7.0.0 - PARTE 2

**Sistema de Análisis IVR de Atención al Cliente (IACT)**
**Versión:** 7.0.0
**Fecha:** 17 de Febrero de 2026
**Tipo:** Breaking Changes desde v6.0.0
**Estado:** Definitivo

---

## ÍNDICE

1. [Modelo de Datos](#6-modelo)
2. [Patrones Comunes de Asignación](#7-patrones)
3. [Casos de Uso](#8-casos-uso)
4. [Implementación Técnica](#9-implementacion)
5. [Migración desde v6.0.0](#10-migracion)

Parte anterior: `MODELO_RBAC_IACT_v7_0_0_PARTE_1.md`

---

<a name="6-modelo"></a>
## 6. MODELO DE DATOS

### 6.1 Diagrama Entidad-Relación

```
┌──────────────────────────────────────────────────┐
│         MODELO DE DATOS v7.0.0                   │
│    (Cambios desde v6.0.0 marcados con *)         │
└──────────────────────────────────────────────────┘

┌──────────────┐
│     User     │
│ (Django)     │
├──────────────┤
│ id (PK)      │
│ username     │
│ email        │
│ is_active    │
└──────┬───────┘
       │
       │ 1:N
       │
       ↓
┌────────────────────────────────────────┐
│   UserFunctionAssignment               │
├────────────────────────────────────────┤
│ id (PK)                                │
│ user_id (FK)                           │
│ function_id (FK)                       │
│ is_temporary                           │
│ valid_from                             │
│ valid_until                            │
│ sod_exception                          │
│ sod_exception_reason                   │
│ sod_exception_approved_by_id (FK)      │
│ created_by_id (FK)                     │
│ approved_by_id (FK)                    │
│ justification                          │
│ created_at                             │
│ revoked_at                             │
│ revoked_by_id (FK)                     │
│ revocation_reason                      │
└────────┬───────────────────────────────┘
         │
         │ N:1
         │
         ↓
┌────────────────────────────────┐
│        Function                │
│               * SIN campo code │
├────────────────────────────────┤
│ permission_django (PK)         │
│ display_name                   │
│ module                         │
│ status                         │
│ description                    │
│ use_cases                      │
│ created_at                     │
│ updated_at                     │
└────────────────────────────────┘

┌────────────────────────────────┐
│         SoDRule                │
├────────────────────────────────┤
│ id (PK)                        │
│ name (unique)                  │
│ description                    │
│ group_a (JSON)                 │
│ group_b (JSON)                 │
│ is_active                      │
│ created_at                     │
│ updated_at                     │
└────────────────────────────────┘

┌────────────────────────────────┐
│        AuditLog                │
├────────────────────────────────┤
│ id (PK)                        │
│ timestamp                      │
│ action                         │
│ user_id (FK)                   │
│ target_user_id (FK)            │
│ function                       │
│ details (JSON)                 │
│ ip_address                     │
│ user_agent                     │
└────────────────────────────────┘

ELIMINADO en v7.0.0:
  - FunctionGroup
  - UserFunctionGroupAssignment
  - Campo code de Function
```

### 6.2 Modelo Function

```python
from django.db import models


class Function(models.Model):
    """
    Función atómica del sistema RBAC.

    Representa UNA acción específica que un usuario puede realizar.
    No representa títulos, roles o posiciones organizacionales.

    Cambios v7.0.0:
    - Eliminado campo code
    - permission_django es la única identificación
    """

    permission_django = models.CharField(
        max_length=100,
        primary_key=True,
        help_text="Permiso Django (ej: reports.view, users.create)"
    )

    display_name = models.CharField(
        max_length=200,
        help_text="Nombre para UI en español (ej: Ver reportes)"
    )

    module = models.CharField(
        max_length=50,
        help_text="Módulo (ej: reports, users, dashboard)"
    )

    STATUS_CHOICES = [
        ('activo', 'Activo'),
        ('planificado', 'Planificado'),
        ('deprecado', 'Deprecado'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='activo',
        help_text="Estado de la función"
    )

    description = models.TextField(
        help_text="Descripción detallada de qué permite hacer"
    )

    use_cases = models.CharField(
        max_length=200,
        blank=True,
        help_text="Casos de uso relacionados (ej: UC_001, UC_002)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rbac_function'
        verbose_name = 'Función'
        verbose_name_plural = 'Funciones'
        ordering = ['module', 'permission_django']

    def __str__(self):
        return f"{self.permission_django} - {self.display_name}"

    @property
    def is_active(self):
        """Retorna True si la función está activa."""
        return self.status == 'activo'
```

### 6.3 Modelo UserFunctionAssignment

```python
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta

User = get_user_model()


class UserFunctionAssignment(models.Model):
    """
    Asignación de función a usuario.

    Puede ser permanente o temporal.
    Incluye auditoría completa y excepciones SoD.

    Cambios v7.0.0:
    - Asignaciones directas (sin grupos intermedios)
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='function_assignments'
    )

    function = models.ForeignKey(
        'Function',
        on_delete=models.PROTECT,
        related_name='user_assignments'
    )

    # Temporal
    is_temporary = models.BooleanField(
        default=False,
        help_text="Si True, expira en valid_until"
    )

    valid_from = models.DateTimeField(
        auto_now_add=True,
        help_text="Inicio de validez"
    )

    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fin de validez (solo si temporal)"
    )

    # Excepción SoD
    sod_exception = models.BooleanField(
        default=False,
        help_text="Excepción aprobada a reglas SoD"
    )

    sod_exception_reason = models.TextField(
        blank=True,
        help_text="Justificación de excepción SoD"
    )

    sod_exception_approved_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='sod_exceptions_approved',
        help_text="Quien aprobó excepción SoD"
    )

    # Auditoría creación
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='functions_assigned_by_me',
        help_text="Quien asignó esta función"
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='functions_approved_by_me',
        help_text="Quien aprobó (si requiere)"
    )

    justification = models.TextField(
        validators=[MinLengthValidator(20)],
        help_text="Justificación (mínimo 20 caracteres)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # Auditoría revocación
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de revocación"
    )

    revoked_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='functions_revoked_by_me',
        help_text="Quien revocó"
    )

    revocation_reason = models.TextField(
        blank=True,
        help_text="Razón de revocación"
    )

    class Meta:
        db_table = 'rbac_user_function_assignment'
        verbose_name = 'Asignación de Función'
        verbose_name_plural = 'Asignaciones de Funciones'
        ordering = ['-created_at']

        indexes = [
            models.Index(fields=['user', 'revoked_at']),
            models.Index(fields=['function']),
            models.Index(fields=['valid_until']),
        ]

        constraints = [
            # Temporal debe tener valid_until
            models.CheckConstraint(
                check=models.Q(
                    is_temporary=False,
                    valid_until__isnull=True
                ) | models.Q(
                    is_temporary=True,
                    valid_until__isnull=False
                ),
                name='temporary_must_have_expiration'
            ),

            # valid_until posterior a valid_from
            models.CheckConstraint(
                check=models.Q(
                    valid_until__isnull=True
                ) | models.Q(
                    valid_until__gte=models.F('valid_from')
                ),
                name='valid_until_after_valid_from'
            ),

            # Excepción SoD requiere razón y aprobador
            models.CheckConstraint(
                check=models.Q(
                    sod_exception=False
                ) | models.Q(
                    sod_exception=True,
                    sod_exception_reason__gt='',
                    sod_exception_approved_by__isnull=False
                ),
                name='sod_exception_requires_approval'
            ),
        ]

    def clean(self):
        """Validaciones adicionales."""
        super().clean()

        # Validar duración máxima temporales (6 meses)
        if self.is_temporary and self.valid_until:
            max_duration = self.valid_from + timedelta(days=180)
            if self.valid_until > max_duration:
                raise ValidationError(
                    "Duración máxima: 6 meses (180 días)"
                )

    def is_currently_valid(self):
        """Retorna True si asignación está activa."""
        now = datetime.now()

        if self.revoked_at:
            return False

        if self.is_temporary and self.valid_until:
            if now > self.valid_until:
                return False

        return True

    def __str__(self):
        temp = " (TEMPORAL)" if self.is_temporary else ""
        revoked = " [REVOCADA]" if self.revoked_at else ""
        return f"{self.user.username} → {self.function.permission_django}{temp}{revoked}"
```

### 6.4 Modelo SoDRule

```python
from django.db import models


class SoDRule(models.Model):
    """
    Regla de Separación de Funciones.

    Define grupos mutuamente excluyentes.
    Usuario NO puede tener funciones de ambos grupos.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nombre (ej: reports_export_separation)"
    )

    description = models.TextField(
        help_text="Descripción de qué previene"
    )

    group_a = models.JSONField(
        help_text="Array de permission_django del grupo A"
    )

    group_b = models.JSONField(
        help_text="Array de permission_django del grupo B"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Si False, no se valida"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rbac_sod_rule'
        verbose_name = 'Regla SoD'
        verbose_name_plural = 'Reglas SoD'
        ordering = ['name']

    def __str__(self):
        return self.name

    def validate_for_user(self, user, new_function_permission):
        """
        Valida si asignar new_function_permission violaría esta regla.

        Returns:
            (bool, str): (is_valid, error_message)
        """
        if not self.is_active:
            return True, ""

        # Funciones activas del usuario
        user_functions = user.function_assignments.filter(
            revoked_at__isnull=True
        ).values_list('function__permission_django', flat=True)

        # Verificar grupos
        has_group_a = any(f in user_functions for f in self.group_a)
        has_group_b = any(f in user_functions for f in self.group_b)

        new_in_group_a = new_function_permission in self.group_a
        new_in_group_b = new_function_permission in self.group_b

        # Validar conflictos
        if has_group_a and new_in_group_b:
            return False, (
                f"Violación SoD '{self.name}': Usuario tiene "
                f"funciones grupo A, no puede recibir '{new_function_permission}' "
                f"del grupo B"
            )

        if has_group_b and new_in_group_a:
            return False, (
                f"Violación SoD '{self.name}': Usuario tiene "
                f"funciones grupo B, no puede recibir '{new_function_permission}' "
                f"del grupo A"
            )

        return True, ""
```

### 6.5 Modelo AuditLog

```python
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class AuditLog(models.Model):
    """
    Log de auditoría de acciones RBAC.

    Inmutable (no modificable ni eliminable).
    Retención: 7 años.
    """

    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Momento exacto de la acción"
    )

    ACTION_CHOICES = [
        ('assign_function', 'Asignar Función'),
        ('revoke_function', 'Revocar Función'),
        ('revoke_function_auto', 'Revocación Automática'),
        ('sod_violation_detected', 'Violación SoD'),
        ('sod_exception_granted', 'Excepción SoD'),
        ('login', 'Inicio Sesión'),
        ('logout', 'Cierre Sesión'),
        ('password_reset', 'Reseteo Contraseña'),
        ('user_created', 'Usuario Creado'),
        ('user_edited', 'Usuario Editado'),
        ('user_deleted', 'Usuario Eliminado'),
        ('user_locked', 'Usuario Bloqueado'),
        ('user_unlocked', 'Usuario Desbloqueado'),
    ]

    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        db_index=True,
        help_text="Tipo de acción"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='audit_logs_as_actor',
        help_text="Usuario que realizó la acción"
    )

    target_user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='audit_logs_as_target',
        help_text="Usuario sobre el que se realizó la acción"
    )

    function = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Función involucrada"
    )

    details = models.JSONField(
        default=dict,
        help_text="Detalles adicionales en JSON"
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP desde donde se realizó"
    )

    user_agent = models.TextField(
        blank=True,
        help_text="User agent del navegador"
    )

    class Meta:
        db_table = 'rbac_audit_log'
        verbose_name = 'Log de Auditoría'
        verbose_name_plural = 'Logs de Auditoría'
        ordering = ['-timestamp']

        indexes = [
            models.Index(fields=['timestamp', 'action']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['target_user', 'timestamp']),
        ]

        permissions = [
            ('view_auditlog', 'Can view audit logs'),
            ('export_auditlog', 'Can export audit logs'),
        ]

    def __str__(self):
        return f"{self.timestamp} - {self.action} by {self.user.username}"

    def save(self, *args, **kwargs):
        """Prevenir edición de logs existentes."""
        if self.pk:
            raise ValidationError(
                "Logs de auditoría son inmutables"
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevenir eliminación de logs."""
        raise ValidationError(
            "Logs de auditoría no pueden eliminarse"
        )
```

---

<a name="7-patrones"></a>
## 7. PATRONES COMUNES DE ASIGNACIÓN

### 7.1 IMPORTANTE: NO son Roles

Los patrones documentados aquí **NO son "roles" ni "grupos" oficiales**.

Son guías opcionales que documentan combinaciones frecuentes observadas en la operación real del sistema.

**PROHIBIDO:**
- Usar estos patrones como roles obligatorios
- Crear código que dependa de estos patrones
- Forzar usuarios a encajar en estos patrones

**PERMITIDO:**
- Usar como referencia al asignar funciones
- Personalizar según necesidades específicas
- Crear combinaciones diferentes

### 7.2 Patrón 1: Operación Telefónica

**Responsabilidad observada:** Personal que opera teléfonos en call center. Solo necesita ver dashboard personal y gestionar alertas propias.

**Funciones típicas (7):**

```
auth.login
auth.logout
auth.recover_password
dashboard.view
alerts.view
alerts.mark_read
```

**Características:**
- Solo lectura (excepto marcar alertas)
- Sin exportación
- Sin gestión de usuarios
- Solo datos propios

**Usuarios estimados:** 50-100

**Restricciones:**
- Dashboard filtrado a datos propios
- No ve datos de otros agentes

### 7.3 Patrón 2: Análisis de Datos

**Responsabilidad observada:** Personal que analiza datos del IVR, genera reportes y exporta información.

**Funciones típicas (10):**

```
auth.login
auth.logout
auth.recover_password
reports.view
reports.export.csv
reports.export.excel
dashboard.view
dashboard.export.csv
alerts.view
alerts.mark_read
```

**Características:**
- Lectura de reportes
- Exportación (CSV y Excel)
- NO crea/edita reportes (cumple SoD 1)
- Dashboard con datos de su área

**Usuarios estimados:** 10-15

**Cumplimiento SoD:**

> NO asignar: `reports.create`, `reports.edit`, `reports.delete`
> Razón: Regla SoD 1

**Restricciones:**
- Exportación máximo 10,000 registros
- Solo datos de área asignada

### 7.4 Patrón 3: Gestión Operativa

**Responsabilidad observada:** Personal de gestión operativa que supervisa call center, gestiona usuarios operativos y configura alertas.

**Funciones típicas (21):**

```
auth.login
auth.logout
auth.recover_password
auth.manage_sessions
reports.view
reports.export.csv
reports.export.excel
dashboard.view
dashboard.export.csv
dashboard.export.excel
users.view
users.create
users.edit
users.lock
users.unlock
users.search
access.view
pipeline.view
pipeline.monitor
alerts.view
alerts.create
alerts.edit
alerts.delete
alerts.mark_read
alerts.send
```

**Características:**
- Gestión de usuarios operativos
- NO asigna permisos RBAC
- Monitoreo pipeline (sin control)
- Gestión completa alertas
- NO accede a auditoría (cumple SoD 2)

**Usuarios estimados:** 3-5

**Cumplimiento SoD:**

> NO asignar: `audit.view`, `audit.search` (SoD 2)
> NO asignar: `pipeline.execute`, `pipeline.stop` (SoD 3)

**Restricciones:**
- Crea usuarios pero NO asigna funciones
- Solo ve pipeline, no ejecuta
- Datos de todas áreas operativas

### 7.5 Patrón 4: Administración Técnica

**Responsabilidad observada:** Administradores técnicos que requieren acceso total para mantenimiento y soporte.

**Funciones:** TODAS las 42 activas

**Características:**
- Acceso total
- Incluye funciones que violan SoD
- Requiere excepción SoD aprobada
- Auditoría reforzada

**Usuarios estimados:** 1-2

**Excepción SoD:**
- Funciones de los 3 grupos SoD
- Aprobación dual obligatoria
- Auditoría reforzada
- Revisión trimestral

**Mitigaciones:**
- Toda acción auditada
- Alertas en acciones críticas
- Revisión mensual de logs
- Justificación por acción sensible

### 7.6 Resumen de Patrones

| Patrón | Funciones | Usuarios | Exporta | Gestiona | Audita | SoD |
|---|---|---|---|---|---|---|
| 1. Operación | 7 | 50-100 | No | No | No | OK |
| 2. Análisis | 10 | 10-15 | Sí | No | No | OK |
| 3. Gestión | 21 | 3-5 | Sí | Sí | No | OK |
| 4. Admin | 42 | 1-2 | Sí | Sí | Sí | Excepción |

> **RECORDATORIO:** Estos son GUÍAS, no roles obligatorios. Cada usuario puede tener combinación personalizada según necesidades.

---

<a name="8-casos-uso"></a>
## 8. CASOS DE USO

### 8.1 UC_001: Iniciar Sesión

**Función:** `auth.login`
**Actor:** Cualquier usuario

**Precondiciones:**
- Cuenta activa
- Conoce credenciales

**Flujo:**
1. Usuario accede a login
2. Ingresa username y password
3. Sistema valida credenciales
4. Sistema verifica cuenta no bloqueada
5. Sistema crea sesión
6. Sistema registra en AuditLog
7. Redirección a dashboard

**Postcondiciones:**
- Sesión activa
- Evento auditado

### 8.2 UC_015: Asignar Funciones

**Función:** `access.assign`
**Actor:** Usuario con `access.assign`

**Precondiciones:**
- Actor tiene `access.assign`
- Usuario objetivo existe
- Función existe y activa

**Flujo:**
1. Actor selecciona usuario
2. Actor selecciona funciones
3. Actor ingresa justificación (min 20 caracteres)
4. Sistema valida SoD
5. Si pasa, crea `UserFunctionAssignment`
6. Sistema registra en AuditLog
7. Sistema notifica usuario

**Flujo alternativo (violación SoD):**

```
4a. Sistema muestra error SoD
4b. Actor puede solicitar excepción
4c. Requiere aprobación adicional
4d. Si aprueba, continúa paso 5
```

**Postcondiciones:**
- Función asignada
- SoD validada
- Evento auditado

### 8.3 UC_024: Crear Reportes

**Función:** `reports.create`
**Actor:** Usuario con `reports.create`

**Precondiciones:**
- Actor tiene `reports.create`
- Actor NO tiene export (SoD 1)

**Flujo:**
1. Actor define parámetros
2. Sistema valida parámetros
3. Sistema genera reporte
4. Sistema almacena (30 días)
5. Sistema registra en AuditLog

**Postcondiciones:**
- Reporte creado
- Evento auditado

> **Nota SoD:** Si actor tiene `reports.export.csv` o `reports.export.excel`, NO puede tener `reports.create`

### 8.4 UC_042: Ver Auditoría

**Función:** `audit.view`
**Actor:** Usuario con `audit.view`

**Precondiciones:**
- Actor tiene `audit.view`
- Actor NO gestiona usuarios (SoD 2)
- Actor NO controla pipeline (SoD 3)

**Flujo:**
1. Actor accede a auditoría
2. Actor aplica filtros
3. Sistema muestra logs
4. Actor puede exportar (si tiene `audit.export`)

**Postcondiciones:**
- Consulta registrada

> **Nota SoD:** Si gestiona usuarios o controla pipeline, NO puede ver auditoría

### 8.5 UC_020: Ejecutar Jobs ETL

**Función:** `pipeline.execute`
**Actor:** Usuario con `pipeline.execute`

**Precondiciones:**
- Actor tiene `pipeline.execute`
- Actor NO tiene auditoría (SoD 3)
- Horario: 00:00-06:00
- No hay job en ejecución

**Flujo:**
1. Actor selecciona job
2. Sistema valida horario
3. Sistema valida no hay job activo
4. Sistema inicia job
5. Sistema registra inicio en AuditLog
6. Job ejecuta (max 4 horas)
7. Sistema registra finalización

**Flujo alternativo (fuera de horario):**

```
2a. Sistema rechaza
2b. Muestra mensaje horario
```

**Postcondiciones:**
- Job ejecutado
- Inicio y fin auditados

---

<a name="9-implementacion"></a>
## 9. IMPLEMENTACIÓN TÉCNICA

### 9.1 Servicio de Asignación

```python
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Function, UserFunctionAssignment, SoDRule, AuditLog


class FunctionAssignmentService:
    """Servicio para asignación con validación SoD."""

    @staticmethod
    @transaction.atomic
    def assign_function(user, permission_django, assigned_by,
                        justification, is_temporary=False,
                        valid_until=None, sod_exception=False,
                        sod_exception_reason=None, approved_by=None):
        """
        Asigna función con validación completa.

        Args:
            user: Usuario objetivo
            permission_django: Permiso (ej: 'reports.view')
            assigned_by: Quien asigna
            justification: Justificación (min 20 chars)
            is_temporary: Si es temporal
            valid_until: Expiración (si temporal)
            sod_exception: Si es excepción SoD
            sod_exception_reason: Razón excepción
            approved_by: Quien aprueba

        Returns:
            UserFunctionAssignment

        Raises:
            ValidationError
        """

        # Obtener función
        try:
            function = Function.objects.get(
                permission_django=permission_django
            )
        except Function.DoesNotExist:
            raise ValidationError(
                f"Función '{permission_django}' no existe"
            )

        # Validar activa
        if function.status != 'activo':
            raise ValidationError(
                f"Función '{permission_django}' no activa"
            )

        # Validar justificación
        if len(justification) < 20:
            raise ValidationError(
                "Justificación mínimo 20 caracteres"
            )

        # Validar SoD si NO es excepción
        if not sod_exception:
            FunctionAssignmentService._validate_sod(
                user, permission_django
            )
        else:
            if not sod_exception_reason or not approved_by:
                raise ValidationError(
                    "Excepción SoD requiere razón y aprobador"
                )

        # Validar temporal
        if is_temporary:
            if not valid_until:
                raise ValidationError(
                    "Temporal requiere fecha expiración"
                )

            from datetime import datetime, timedelta
            max_duration = datetime.now() + timedelta(days=180)
            if valid_until > max_duration:
                raise ValidationError(
                    "Duración máxima: 6 meses"
                )

        # Crear asignación
        assignment = UserFunctionAssignment.objects.create(
            user=user,
            function=function,
            is_temporary=is_temporary,
            valid_until=valid_until,
            sod_exception=sod_exception,
            sod_exception_reason=sod_exception_reason or '',
            sod_exception_approved_by=approved_by if sod_exception else None,
            created_by=assigned_by,
            approved_by=approved_by,
            justification=justification
        )

        # Auditar
        AuditLog.objects.create(
            action='assign_function',
            user=assigned_by,
            target_user=user,
            function=permission_django,
            details={
                'justification': justification,
                'is_temporary': is_temporary,
                'valid_until': valid_until.isoformat() if valid_until else None,
                'sod_exception': sod_exception
            }
        )

        return assignment

    @staticmethod
    def _validate_sod(user, new_function_permission):
        """Valida todas reglas SoD activas."""

        for sod_rule in SoDRule.objects.filter(is_active=True):
            is_valid, error = sod_rule.validate_for_user(
                user, new_function_permission
            )

            if not is_valid:
                # Registrar intento
                AuditLog.objects.create(
                    action='sod_violation_detected',
                    user=user,
                    function=new_function_permission,
                    details={
                        'rule': sod_rule.name,
                        'error': error
                    }
                )

                raise ValidationError(error)

    @staticmethod
    @transaction.atomic
    def revoke_function(user, permission_django, revoked_by, reason):
        """Revoca función."""

        try:
            assignment = UserFunctionAssignment.objects.get(
                user=user,
                function__permission_django=permission_django,
                revoked_at__isnull=True
            )
        except UserFunctionAssignment.DoesNotExist:
            raise ValidationError(
                f"Usuario no tiene '{permission_django}' activa"
            )

        # Revocar
        from django.utils import timezone
        assignment.revoked_at = timezone.now()
        assignment.revoked_by = revoked_by
        assignment.revocation_reason = reason
        assignment.save()

        # Auditar
        AuditLog.objects.create(
            action='revoke_function',
            user=revoked_by,
            target_user=user,
            function=permission_django,
            details={'reason': reason}
        )

        return assignment
```

### 9.2 Middleware de Validación

```python
from django.core.exceptions import PermissionDenied
from .models import UserFunctionAssignment


class RBACMiddleware:
    """Middleware para validar funciones."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            request.user.has_function = lambda perm: (
                self.user_has_function(request.user, perm)
            )

        response = self.get_response(request)
        return response

    @staticmethod
    def user_has_function(user, permission_django):
        """Verifica si usuario tiene función activa."""

        from django.utils import timezone
        from django.db import models
        now = timezone.now()

        return UserFunctionAssignment.objects.filter(
            user=user,
            function__permission_django=permission_django,
            revoked_at__isnull=True,
            function__status='activo'
        ).filter(
            models.Q(is_temporary=False) |
            models.Q(is_temporary=True, valid_until__gte=now)
        ).exists()
```

### 9.3 Decorador de Funciones

```python
from functools import wraps
from django.core.exceptions import PermissionDenied


def require_function(permission_django):
    """
    Decorador para vistas que requieren función específica.

    Uso:
        @require_function('reports.create')
        def create_report_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Autenticación requerida")

            if not request.user.has_function(permission_django):
                raise PermissionDenied(
                    f"Requiere función: {permission_django}"
                )

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator
```

---

<a name="10-migracion"></a>
## 10. MIGRACIÓN DESDE v6.0.0

### 10.1 Cambios Breaking

**1. Campo `code` eliminado:**

```python
# v6.0.0:
function.code  # 'RPT_VIEW'

# v7.0.0:
function.permission_django  # 'reports.view'
```

**2. Modelos de grupos eliminados:**

```python
# v6.0.0:
FunctionGroup.objects.get(group_id='AGR-002')
UserFunctionGroupAssignment.objects.filter(user=user)

# v7.0.0:
# Estos modelos no existen
# Usar UserFunctionAssignment directamente
```

**3. Asignación directa:**

```python
# v6.0.0:
user.groups.add(agr_002)

# v7.0.0:
for func in functions:
    assign_function_to_user(user, func, by, justification)
```

### 10.2 Script de Migración

```python
from django.db import transaction
from apps.access.models import (
    Function, UserFunctionAssignment,
    FunctionGroup, UserFunctionGroupAssignment
)


@transaction.atomic
def migrate_groups_to_functions():
    """
    Migra asignaciones de grupos a funciones individuales.

    Para cada usuario con grupos:
    1. Obtiene funciones del grupo
    2. Crea UserFunctionAssignment por función
    3. Marca grupo como migrado
    """

    print("Iniciando migración v6.0.0 → v7.0.0...")

    group_assignments = UserFunctionGroupAssignment.objects.filter(
        revoked_at__isnull=True
    )

    total = group_assignments.count()
    migrated = 0
    errors = []

    for group_assignment in group_assignments:
        try:
            user = group_assignment.user
            group = group_assignment.group

            print(f"Migrando {user.username} - {group.group_id}...")

            functions = group.functions.all()

            for function in functions:
                exists = UserFunctionAssignment.objects.filter(
                    user=user,
                    function=function,
                    revoked_at__isnull=True
                ).exists()

                if exists:
                    print(f"  {function.permission_django}: existe")
                    continue

                UserFunctionAssignment.objects.create(
                    user=user,
                    function=function,
                    created_by=group_assignment.created_by,
                    justification=f"Migrado desde {group.group_id}: {group.name}",
                    created_at=group_assignment.created_at
                )

                print(f"  {function.permission_django}: migrado")

            group_assignment.migration_completed = True
            group_assignment.migration_date = timezone.now()
            group_assignment.save()

            migrated += 1

        except Exception as e:
            error = f"Error {user.username}: {str(e)}"
            print(error)
            errors.append(error)

    print(f"\nMigración completada:")
    print(f"  Total: {total}")
    print(f"  Migradas: {migrated}")
    print(f"  Errores: {len(errors)}")

    if errors:
        print("\nErrores:")
        for error in errors:
            print(f"  {error}")

    return migrated, errors


def remove_code_field():
    """
    Campo code se elimina con migración Django.
    Este script valida que no haya dependencias.
    """

    print("\nValidando eliminación campo code...")
    print("  IMPORTANTE: Revisar manualmente:")
    print("    - function.code")
    print("    - Function.objects.filter(code=...)")
    print("  Reemplazar con: function.permission_django")


def run_migration():
    """Ejecuta migración completa."""

    print("=" * 60)
    print("MIGRACIÓN v6.0.0 → v7.0.0")
    print("=" * 60)
    print()

    migrated, errors = migrate_groups_to_functions()

    if errors:
        print("\nMigración con errores.")
        print("Revisar antes de continuar.")
        return False

    remove_code_field()

    print("\n" + "=" * 60)
    print("MIGRACIÓN COMPLETADA")
    print("=" * 60)
    print("\nPróximos pasos:")
    print("1. Revisar referencias a code")
    print("2. Ejecutar: python manage.py migrate access")
    print("3. Validar sistema")
    print("4. Backup completado")

    return True
```

### 10.3 Migración Django

```python
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('access', '0001_initial'),
    ]

    operations = [
        # Agregar campos migración
        migrations.AddField(
            model_name='userfunctiongroupassignment',
            name='migration_completed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userfunctiongroupassignment',
            name='migration_date',
            field=models.DateTimeField(null=True, blank=True),
        ),

        # Agregar constraints
        migrations.AddConstraint(
            model_name='userfunctionassignment',
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(is_temporary=False, valid_until__isnull=True) |
                    models.Q(is_temporary=True, valid_until__isnull=False)
                ),
                name='temporary_must_have_expiration'
            ),
        ),

        # Eliminar campo code
        migrations.RemoveField(
            model_name='function',
            name='code',
        ),
    ]
```

### 10.4 Validación Post-Migración

```python
def validate_migration():
    """Valida migración completada correctamente."""

    from apps.access.models import UserFunctionAssignment, Function
    from django.contrib.auth import get_user_model

    User = get_user_model()

    print("Validando migración v7.0.0...")
    print()

    # Verificar campo code eliminado
    try:
        Function.objects.first().code
        print("ERROR: Campo code existe")
        return False
    except AttributeError:
        print("✓ Campo code eliminado")

    # Verificar asignaciones
    total_users = User.objects.filter(is_active=True).count()
    users_with_functions = User.objects.filter(
        function_assignments__revoked_at__isnull=True
    ).distinct().count()

    print(f"✓ Usuarios activos: {total_users}")
    print(f"✓ Usuarios con funciones: {users_with_functions}")

    # Verificar SoD
    from apps.access.models import SoDRule
    sod_rules = SoDRule.objects.filter(is_active=True).count()
    print(f"✓ Reglas SoD activas: {sod_rules}")

    if sod_rules < 3:
        print("  ADVERTENCIA: Menos de 3 reglas SoD")

    # Verificar funciones
    active = Function.objects.filter(status='activo').count()
    print(f"✓ Funciones activas: {active}")

    if active != 42:
        print(f"  ADVERTENCIA: Esperadas 42 activas")

    print()
    print("Validación completada")
    return True
```

### 10.5 Rollback

```python
@transaction.atomic
def rollback_to_v6():
    """
    Rollback v7.0.0 → v6.0.0 si necesario.

    ADVERTENCIA: Solo si NO se eliminaron modelos v6.
    """

    print("ROLLBACK v7.0.0 → v6.0.0")
    print()
    print("IMPORTANTE: Rollback requiere:")
    print("  1. Backup de base de datos")
    print("  2. Migración Django a anterior")
    print("  3. Código fuente v6.0.0")
    print()
    print("Recomendado: Restaurar desde backup")
```

---

## FIN DE PARTE 2

**Documento completo:**
- `MODELO_RBAC_IACT_v7_0_0_PARTE_1.md`
- `MODELO_RBAC_IACT_v7_0_0_PARTE_2.md`

---

Sistema IACT — Análisis IVR
**Versión:** 7.0.0 | **Fecha:** 17 de Febrero de 2026 | **Documento:** Parte 2 de 2 | **Estado:** Definitivo
