"""
Database Router - IACT Call Center System.

CNST-003: Enforce READ-ONLY access to IVR Legacy database.

Routing rules:
- Todos los modelos ORM -> 'default' (PostgreSQL)
- MariaDB (ivr) se accede exclusivamente via connections['ivr'].cursor()
  (raw SQL). El ORM Django no gestiona modelos en esa base de datos.
  Ninguna migration de Django se ejecuta en MariaDB.

Compliance: CNST-003
"""


class DatabaseRouter:
    """
    Database router para dual-database setup.

    - default (PostgreSQL): Analytics DB (READ + WRITE, ORM + migrations)
    - ivr (MariaDB): IVR Legacy DB (READ-ONLY, solo raw SQL via cursor)

    No existen modelos ORM con app_label que apunte a la base ivr.
    El acceso a MariaDB es exclusivamente via connections['ivr'].cursor().
    """

    def db_for_read(self, model, **hints):
        """
        Todos los modelos ORM leen de PostgreSQL.

        Returns:
            str: 'default'
        """
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Todos los modelos ORM escriben a PostgreSQL.

        CNST-003: Los writes a ivr_legacy están bloqueados a nivel de
        usuario de BD (ivr_readonly) y de DatabaseRouter.

        Returns:
            str: 'default'
        """
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Permitir relaciones entre modelos de la misma base de datos.

        Returns:
            bool | None
        """
        if obj1._state.db == obj2._state.db:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Todas las migrations Django van a PostgreSQL (default).

        CNST-003: MariaDB (ivr) no gestiona migrations Django.
        El schema de ivr_legacy es responsabilidad exclusiva de
        los scripts de IACT-db (provisioners/mariadb/).

        Returns:
            bool: True solo si db == 'default'
        """
        return db == 'default'


# ==============================================================================
# TESTS DE VALIDACION
# ==============================================================================

def test_router_read():
    """Test routing READ operations — todos van a default."""
    from django.contrib.auth.models import User

    router = DatabaseRouter()

    assert router.db_for_read(User) == 'default'


def test_router_write():
    """Test routing WRITE operations — todos van a default."""
    from django.contrib.auth.models import User

    router = DatabaseRouter()

    assert router.db_for_write(User) == 'default'


def test_router_migrations_only_on_default():
    """Test migrations solo permitidas en PostgreSQL (CNST-003)."""
    router = DatabaseRouter()

    # Todas las apps migran solo a default
    for app in ('auth', 'users', 'pipeline', 'access', 'core'):
        assert router.allow_migrate('default', app) is True
        assert router.allow_migrate('ivr', app) is False

    # Ninguna app migra a MariaDB — protección CNST-003
    assert router.allow_migrate('ivr', 'any_app') is False
