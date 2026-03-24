# Deuda Técnica

Registro de tareas pendientes, configuraciones manuales requeridas y
decisiones tomadas por tiempo/contexto que deben resolverse antes de
pasar a producción o en la siguiente iteración.

Formato de cada ítem:
- **ID** — identificador único
- **Área** — componente o capa afectada
- **Descripción** — qué falta o qué está mal
- **Por qué existe** — contexto de la decisión
- **Acción requerida** — qué debe hacer el desarrollador/operador
- **Prioridad** — Alta / Media / Baja

---

## DT-001 — Crear grupo `iact-admins` y asignar usuarios administradores

| Campo      | Detalle |
|------------|---------|
| **Área**   | Apache / Autenticación / Django Admin |
| **Prioridad** | Alta |

### Descripción

El bloque `<Location "/admin/">` en `scripts/apache/iact-apache.conf` protege
el panel de administración con HTTP Basic Auth respaldado por la BD de Django.
La directiva `Require group iact-admins` requiere que el grupo exista y que
los usuarios administradores estén asignados a él.

**El grupo no se crea automáticamente.** Hasta que no se ejecuten los pasos
siguientes, `/admin/` devolverá `401 Unauthorized` para todos los usuarios.

### Por qué existe

La creación del grupo y la asignación de usuarios son operaciones de datos
(no de código), por lo que no se incluyen en migraciones ni en el setup
automático. Deben ejecutarse manualmente una vez por entorno.

### Acción requerida

**1. Abrir el shell de Django:**

```bash
cd /home/user/IACT-api/callcentersite
DJANGO_SETTINGS_MODULE=config.settings.production \
    ../venv/bin/python manage.py shell
```

**2. Crear el grupo:**

```python
from django.contrib.auth.models import Group

Group.objects.get_or_create(name='iact-admins')
```

**3. Asignar el usuario administrador al grupo:**

```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User  = get_user_model()
grupo = Group.objects.get(name='iact-admins')

user = User.objects.get(username='tu_usuario')
user.groups.add(grupo)
```

**4. Recargar Apache:**

```bash
sudo apache2ctl graceful
```

### Verificación

```python
# En el shell de Django
user = User.objects.get(username='tu_usuario')
print(user.is_active)                                          # True
print(user.is_deleted)                                         # False
print(list(user.groups.values_list('name', flat=True)))        # ['iact-admins']
```

```bash
# Desde terminal
curl -i -u tu_usuario:tu_contraseña http://localhost/admin/    # 200 o redirect
curl -i http://localhost/admin/                                 # 401
```

### Referencia

- Implementación: `callcentersite/config/wsgi.py` → `check_password`, `groups_for_user`
- Configuración Apache: `scripts/apache/iact-apache.conf` → `<Location "/admin/">`
- Documentación completa: `scripts/documents/apache_admin_auth.md`

---

<!-- Agregar nuevos ítems con el siguiente ID disponible -->
