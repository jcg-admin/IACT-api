"""
WSGI config for IACT Call Center project.

Expone el callable WSGI como ``application`` para mod_wsgi.

Autenticación Apache (mod_wsgi):
    check_password   — verifica usuario/contraseña contra la BD de Django.
                       Usado por Apache para proteger /admin/ con HTTP Basic Auth.
                       Extiende el handler estándar de Django con validación
                       de SoftDelete (is_deleted) específica de este proyecto.

    groups_for_user  — retorna los grupos Django del usuario.
                       Permite a Apache restringir rutas por grupo
                       (WSGIAuthGroupScript).

Ver: scripts/apache/iact-apache.conf  →  <Location "/admin/">
Ver: https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/modwsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

application = get_wsgi_application()


# ==============================================================================
# Apache mod_wsgi — autenticación contra la BD de Django
# ==============================================================================

def check_password(environ, username, password):
    """
    Verifica credenciales de un usuario para HTTP Basic Auth en Apache.

    Apache llama a esta función cuando una ruta protegida con
    ``AuthBasicProvider wsgi`` recibe una petición. Devuelve True solo si:
      1. El usuario existe en la BD.
      2. La contraseña es correcta (django.contrib.auth.authenticate).
      3. is_active = True  (usuario habilitado en Django).
      4. is_deleted = False (usuario no eliminado vía SoftDeleteMixin).

    Args:
        environ (dict): Variables de entorno WSGI (no se usa directamente).
        username (str): Nombre de usuario enviado en el encabezado Basic Auth.
        password (str): Contraseña en texto plano enviada por el cliente.

    Returns:
        bool | None:
            True   — credenciales válidas, acceso concedido.
            None   — credenciales inválidas o usuario inactivo/eliminado
                     (None es equivalente a False para Apache pero permite
                     distinguir "usuario no encontrado" de "acceso denegado").
    """
    from django.contrib.auth import authenticate

    user = authenticate(username=username, password=password)

    if user is None:
        return None

    # Bloquear usuarios soft-deleted aunque is_active siga en True
    if getattr(user, 'is_deleted', False):
        return None

    return user.is_active or None


def groups_for_user(environ, username):
    """
    Retorna la lista de grupos Django a los que pertenece el usuario.

    Apache llama a esta función cuando una ruta usa ``WSGIAuthGroupScript``
    con ``Require group <nombre>``. Permite restringir rutas por grupo.

    Solo considera usuarios activos y no eliminados (SoftDelete).

    Args:
        environ (dict): Variables de entorno WSGI.
        username (str): Nombre de usuario ya autenticado por check_password.

    Returns:
        list[str]: Lista de nombres de grupos. Lista vacía si el usuario
                   no existe, está inactivo o fue eliminado.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return []

    if not user.is_active or getattr(user, 'is_deleted', False):
        return []

    return list(user.groups.values_list('name', flat=True))
