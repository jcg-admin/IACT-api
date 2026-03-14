# Apache mod_wsgi — Autenticación HTTP Basic para /admin/

Protege el panel de administración de Django con una capa de autenticación
a nivel Apache, **antes** de que la petición llegue a Django.

La verificación usa la propia base de datos de usuarios del proyecto, con
soporte para `SoftDeleteMixin` (usuarios eliminados lógicamente no pueden
acceder aunque `is_active` siga en `True`).

---

## Cómo funciona

```
Navegador  →  GET /admin/
               │
               ▼
         Apache (mod_wsgi)
               │
               ▼
    ┌─────────────────────────────────┐
    │  check_password (wsgi.py)       │
    │  1. authenticate(user, pass)    │
    │  2. is_deleted == False?        │
    │  3. is_active  == True?         │
    └─────────────────────────────────┘
               │ OK
               ▼
    ┌─────────────────────────────────┐
    │  groups_for_user (wsgi.py)      │
    │  Require group iact-admins      │
    └─────────────────────────────────┘
               │ OK
               ▼
         Django Admin
```

Si cualquier paso falla, Apache devuelve `401 Unauthorized` sin que Django
procese nada.

---

## Prerequisito

Apache y mod_wsgi ya instalados y el sitio activo:

```bash
sudo bash scripts/apache/install_apache_deb.sh
sudo bash scripts/apache/setup_apache.sh
```

---

## Paso 1 — Crear el grupo `iact-admins` en Django

Abre el shell de Django:

```bash
cd /home/user/IACT-api/callcentersite
DJANGO_SETTINGS_MODULE=config.settings.production \
    ../venv/bin/python manage.py shell
```

Dentro del shell:

```python
from django.contrib.auth.models import Group

# Crear el grupo (si ya existe, get_or_create no falla)
grupo, creado = Group.objects.get_or_create(name='iact-admins')
print("Creado" if creado else "Ya existía")
```

---

## Paso 2 — Asignar el grupo al usuario administrador

Continúa en el mismo shell o abre uno nuevo:

```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User  = get_user_model()
grupo = Group.objects.get(name='iact-admins')

# Reemplaza 'tu_usuario' con el username real
admin = User.objects.get(username='tu_usuario')
admin.groups.add(grupo)

print(f"Grupos de {admin.username}: {list(admin.groups.values_list('name', flat=True))}")
```

Para verificar que el usuario cumple todos los requisitos de acceso:

```python
print("is_active  :", admin.is_active)
print("is_deleted :", admin.is_deleted)
print("is_staff   :", admin.is_staff)
print("grupos     :", list(admin.groups.values_list('name', flat=True)))
```

Los cuatro deben ser:

| Campo       | Valor esperado       |
|-------------|----------------------|
| `is_active` | `True`               |
| `is_deleted`| `False`              |
| `is_staff`  | `True` (para admin)  |
| grupos      | incluye `iact-admins`|

---

## Paso 3 — Aplicar la configuración en Apache

No es necesario reiniciar Apache. Recarga la configuración sin cortar
conexiones activas:

```bash
sudo apache2ctl graceful
```

Verifica que no hay errores de sintaxis:

```bash
sudo apache2ctl configtest
# Esperado: Syntax OK
```

---

## Paso 4 — Probar el acceso

Abre el navegador en `http://iact.local/admin/` (o la IP del servidor).

Apache debe mostrar un diálogo de autenticación HTTP Basic **antes** del
formulario de login de Django.

Desde terminal:

```bash
# Debe devolver 401 sin credenciales
curl -i http://localhost/admin/

# Debe devolver 200 o redirect al login de Django con credenciales válidas
curl -i -u tu_usuario:tu_contraseña http://localhost/admin/

# Debe devolver 401 si el usuario NO está en iact-admins
curl -i -u otro_usuario:su_contraseña http://localhost/admin/
```

---

## Dónde están los archivos relevantes

| Archivo | Qué contiene |
|---------|-------------|
| `callcentersite/config/wsgi.py` | `check_password` y `groups_for_user` |
| `scripts/apache/iact-apache.conf` | Bloque `<Location "/admin/">` |

### Fragmento en `wsgi.py`

```python
def check_password(environ, username, password):
    from django.contrib.auth import authenticate
    user = authenticate(username=username, password=password)
    if user is None:
        return None
    if getattr(user, 'is_deleted', False):   # SoftDeleteMixin
        return None
    return user.is_active or None

def groups_for_user(environ, username):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return []
    if not user.is_active or getattr(user, 'is_deleted', False):
        return []
    return list(user.groups.values_list('name', flat=True))
```

### Fragmento en `iact-apache.conf`

```apache
<Location "/admin/">
    AuthType Basic
    AuthName "IACT Admin — acceso restringido"
    AuthBasicProvider wsgi
    WSGIAuthUserScript  ${WSGI_FILE}
    WSGIAuthGroupScript ${WSGI_FILE}
    Require group iact-admins
    Require valid-user
</Location>
```

---

## Agregar más usuarios al grupo

```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User  = get_user_model()
grupo = Group.objects.get(name='iact-admins')

User.objects.get(username='otro_admin').groups.add(grupo)
```

Cambios en la BD se aplican de inmediato, sin recargar Apache.

---

## Quitar acceso a un usuario

```python
User.objects.get(username='ex_admin').groups.remove(grupo)
```

---

## Solución de problemas

**Apache sigue pidiendo usuario aunque las credenciales sean correctas**
- Verificar que el usuario tiene `is_active=True` y `is_deleted=False`.
- Verificar que pertenece al grupo `iact-admins`.
- Revisar el log: `sudo tail -f /var/log/apache2/iact_error.log`

**`401 Unauthorized` inmediato sin mostrar el diálogo**
- El módulo `mod_auth_basic` puede estar deshabilitado.
  ```bash
  sudo a2enmod auth_basic authz_user && sudo apache2ctl graceful
  ```

**El diálogo Basic Auth no aparece (va directo al login de Django)**
- El bloque `<Location>` puede no estar activo. Verificar:
  ```bash
  sudo apache2ctl -S | grep admin
  ```

**`WSGIAuthUserScript` genera error en el log**
- Verificar que `DJANGO_SETTINGS_MODULE` está seteado en el proceso WSGI.
  La directiva `SetEnv` del VirtualHost debe estar antes del `<Location>`.
