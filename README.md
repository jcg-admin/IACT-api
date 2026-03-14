# IACT API

API REST para el sistema IACT Call Center construida con Django REST Framework.

## Descripción

Servicio backend que gestiona autenticación, control de acceso, alertas, auditoría, reportes y pipeline de llamadas del sistema IACT. Implementa compliance CNST v2.2.1 sin Celery, Channels, Sentry ni Redis.

## Compliance CNST v2.2.1

- CNST-001: NO email
- CNST-002: SESSION_ENGINE='db'
- CNST-003: Dual database (READ-ONLY ivr_legacy)
- CNST-004: NO Celery, NO Channels
- CNST-005: Throttling + MAX_PAGE_SIZE
- CNST_TECNICAS: NO Sentry, NO Redis

## Stack Tecnológico

- Python 3.11+
- Django 5.0+
- Django REST Framework 3.14+
- PostgreSQL 16 (analytics - default)
- MariaDB 11.4 (ivr_legacy - READ-ONLY)
- pytest + FactoryBoy (testing)
- Apache 2.4+ (producción)

## Requisitos

- Python 3.11+
- PostgreSQL 16+
- MariaDB 11.4+
- pip
- virtualenv

## Instalación

### 1. Clonar repositorio

```bash
git clone https://github.com/jcg-admin/IACT-api.git
cd IACT-api
```

### 2. Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements/development.txt
```

### 4. Configurar variables de entorno

```bash
Editar .env con los valores del entorno
```

Edita `.env` con tus valores:

```
DEBUG=True
SECRET_KEY=tu-clave-secreta-muy-larga-y-aleatoria
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.56.11

# Bases de datos
DATABASE_URL=postgresql://django_user:django_pass@192.168.56.11:5432/iact_analytics
LEGACY_DATABASE_URL=mysql://django_user:django_pass@192.168.56.10:3306/ivr_legacy

# Sesiones
SESSION_ENGINE=django.contrib.sessions.backends.db

# Throttling y paginación
REST_FRAMEWORK_THROTTLE_RATES=anon=100/hour,user=1000/hour
MAX_PAGE_SIZE=100

# Email (NO se usa - CNST-001)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Seguridad
SECURE_SSL_REDIRECT=False
CSRF_COOKIE_SECURE=False
SESSION_COOKIE_SECURE=False
```

### 5. Ejecutar migraciones

```bash
# Migraciones de PostgreSQL (default)
python manage.py migrate

# Migraciones de MariaDB (ivr_legacy - READ-ONLY)
python manage.py migrate --database=legacy
```

### 6. Crear superuser

```bash
python manage.py createsuperuser
```

### 7. Cargar datos iniciales

```bash
# Cargar fixtures de módulos
python manage.py loaddata callcentersite/apps/access/fixtures/modules.json
python manage.py loaddata callcentersite/apps/authentication/fixtures/security_questions.json
python manage.py loaddata callcentersite/apps/alerts/fixtures/alert_configurations.json
```

### 8. Iniciar servidor de desarrollo

```bash
python manage.py runserver
```

El servidor estará disponible en `http://localhost:8000`

## Desarrollo

### Estructura del Proyecto

```
api/
├── callcentersite/
│   ├── apps/
│   │   ├── access/              # Control de acceso y RBAC
│   │   │   ├── models.py
│   │   │   ├── serializers/
│   │   │   ├── views.py
│   │   │   ├── permissions.py
│   │   │   ├── services.py
│   │   │   └── urls.py
│   │   ├── alerts/              # Sistema de alertas
│   │   │   ├── models.py
│   │   │   ├── serializers/
│   │   │   ├── services/
│   │   │   ├── scheduler.py
│   │   │   └── views.py
│   │   ├── audit/               # Auditoría de cambios
│   │   │   ├── models.py
│   │   │   ├── middleware/
│   │   │   ├── decorators.py
│   │   │   ├── services.py
│   │   │   └── views.py
│   │   ├── authentication/      # Autenticación y sesiones
│   │   │   ├── models.py
│   │   │   ├── serializers/
│   │   │   ├── services/
│   │   │   ├── viewsets.py
│   │   │   └── urls.py
│   │   ├── core/                # Funcionalidades base
│   │   │   ├── models.py
│   │   │   ├── middleware/
│   │   │   ├── navigation/
│   │   │   ├── services/
│   │   │   ├── permissions.py
│   │   │   ├── mixins.py
│   │   │   └── validators.py
│   │   ├── dashboard/           # Dashboards
│   │   │   ├── models.py
│   │   │   ├── serializers/
│   │   │   ├── services/
│   │   │   ├── rbac.py
│   │   │   └── viewsets.py
│   │   ├── ivr/                 # Sistema IVR
│   │   │   ├── models.py
│   │   │   ├── adapters.py
│   │   │   ├── serializers/
│   │   │   └── viewsets.py
│   │   ├── ivr_legacy/          # IVR legacy (datos de ivr_legacy)
│   │   │   ├── models.py
│   │   │   ├── adapters.py
│   │   │   └── views.py
│   │   ├── pipeline/            # Pipeline de llamadas
│   │   │   ├── models.py
│   │   │   ├── serializers/
│   │   │   ├── services/
│   │   │   ├── scheduler.py
│   │   │   ├── filters.py
│   │   │   └── viewsets.py
│   │   ├── reports/             # Reportes y exportación
│   │   │   ├── models.py
│   │   │   ├── serializers/
│   │   │   ├── services.py
│   │   │   ├── permissions.py
│   │   │   └── views.py
│   │   ├── users/               # Gestión de usuarios
│   │   │   ├── models.py
│   │   │   ├── serializers/
│   │   │   ├── services/
│   │   │   ├── viewsets/
│   │   │   ├── signals.py
│   │   │   ├── filters.py
│   │   │   └── validators.py
│   │   └── utils/               # Utilidades compartidas
│   │       ├── constants.py
│   │       ├── decorators.py
│   │       ├── formatters.py
│   │       ├── helpers.py
│   │       ├── validators.py
│   │       └── models.py
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py          # Configuración base
│   │   │   ├── development.py   # Desarrollo
│   │   │   ├── production.py    # Producción
│   │   │   └── testing.py       # Testing
│   │   ├── database_router.py   # Router para dual database
│   │   ├── urls.py              # URLs principales
│   │   └── wsgi.py              # WSGI para Apache
│   ├── static/                  # Archivos estáticos
│   ├── media/                   # Archivos de usuario
│   ├── manage.py
│   └── pytest.ini
├── tests/
│   ├── unit/                    # Tests unitarios
│   ├── integration/             # Tests de integración
│   ├── api/                     # Tests de API
│   ├── factories/               # Factory Boy factories
│   ├── fixtures/                # Datos de prueba
│   ├── mocks/                   # Mocks y patches
│   ├── conftest.py
│   └── README.md
├── scripts/
│   ├── create_modules.py
│   ├── run_db.sh
│   ├── run_tests.sh
│   └── verificar_implementacion.sh
├── requirements/
│   ├── base.txt                 # Dependencias comunes
│   ├── development.txt          # Desarrollo
│   ├── production.txt           # Producción
│   └── testing.txt              # Testing
├── docs/
│   ├── architecture/            # Documentación de arquitectura
│   ├── api/                     # Documentación de API
│   ├── setup/                   # Guías de setup
│   └── README.md
├── .env
├── .gitignore
├── Makefile                     # Scripts útiles
└── README.md
```

### Apps Principales

#### access
Gestión de control de acceso y RBAC (Role-Based Access Control).
- Módulos
- Funciones
- Permisos por módulo
- Asignación de permisos a usuarios y roles

#### authentication
Autenticación, sesiones y seguridad.
- Login/Logout
- Recuperación de contraseña
- Preguntas de seguridad
- Lockout de cuenta
- Gestión de sesiones (BD)

#### users
Gestión de usuarios, perfiles y configuración.
- Crear/editar/eliminar usuarios
- Perfiles de usuario
- Cambio de contraseña
- Avatar/foto de perfil
- Configuración de usuario

#### audit
Auditoría de cambios y logging.
- Registro de todas las acciones
- Middleware de seguridad
- Tracking de sesiones
- Decoradores para auditoría

#### alerts
Sistema de alertas y notificaciones.
- Configuración de alertas
- Suscripción a alertas
- Notificaciones por email (console backend)
- Scheduler para alertas periódicas

#### pipeline
Pipeline de procesamiento de llamadas.
- Call records
- Call notes
- Centros de llamadas
- Servicios
- ETL para datos

#### reports
Sistema de reportes y exportación.
- Creación de reportes
- Exportación de datos
- CNST-007 compliance

#### dashboard
Dashboards personalizables.
- Widgets
- Filtros
- Preferencias de usuario
- RBAC en dashboards

#### ivr / ivr_legacy
Datos de sistemas IVR.
- ivr: Nueva integración
- ivr_legacy: Datos READ-ONLY de MariaDB

#### core
Funcionalidades base compartidas.
- Modelos abstractos
- Middleware
- Navegación
- Servicios base

#### utils
Utilidades y helpers.
- Formatters
- Validators
- Decorators
- Helpers

## Testing

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Tests específicos
pytest tests/unit/users/
pytest tests/integration/authentication/
pytest tests/api/

# Con coverage
pytest --cov=callcentersite.apps --cov-report=html

# Tests en paralelo
pytest -n auto

# Tests con marcas
pytest -m unit
pytest -m integration
pytest -m api
```

### Estructura de Tests

```
tests/
├── unit/                    # Tests de modelos, servicios, etc.
├── integration/             # Tests de flujos completos
├── api/                     # Tests de endpoints
├── factories/               # Factory Boy factories
├── fixtures/                # Datos de prueba
├── mocks/                   # Mocks y patches
├── conftest.py              # Configuración pytest
└── README.md
```

### Escribir Tests

```python
import pytest
from tests.factories import UserFactory
from rest_framework.test import APIClient

@pytest.mark.django_db
class TestUserAPI:
    def setup_method(self):
        self.client = APIClient()
        self.user = UserFactory()
    
    def test_list_users(self):
        response = self.client.get('/api/users/')
        assert response.status_code == 200
```

## API Documentation

### OpenAPI/Swagger

```bash
# Acceder a la documentación
http://localhost:8000/api/schema/swagger/
http://localhost:8000/api/schema/redoc/
```

### Endpoints Principales

```
POST   /api/auth/login/                    - Login
POST   /api/auth/logout/                   - Logout
GET    /api/auth/me/                       - Usuario actual

GET    /api/users/                         - Listar usuarios
POST   /api/users/                         - Crear usuario
GET    /api/users/{id}/                    - Obtener usuario
PATCH  /api/users/{id}/                    - Actualizar usuario
DELETE /api/users/{id}/                    - Eliminar usuario

GET    /api/access/modules/                - Listar módulos
GET    /api/access/permissions/            - Listar permisos
GET    /api/access/user-permissions/       - Permisos del usuario

GET    /api/audit/logs/                    - Logs de auditoría
GET    /api/alerts/                        - Listar alertas
GET    /api/dashboard/                     - Dashboard
GET    /api/pipeline/calls/                - Llamadas
GET    /api/reports/                       - Reportes
```

## Seguridad

### Autenticación
- Session-based (Django sessions en BD)
- Token opcional
- CSRF protection

### Permisos
- RBAC (Role-Based Access Control)
- Permisos por función
- Permisos por módulo

### Auditoría
- Logging de todas las acciones
- Middleware de seguridad
- Tracking de sesiones

### Protecciones
- Throttling: 100/hora (anónimo), 1000/hora (autenticado)
- MAX_PAGE_SIZE: 100 registros por página
- NO email (CNST-001)
- NO Celery/Channels (CNST-004)
- NO Sentry/Redis (CNST_TECNICAS)

## Despliegue en Producción (Apache + Linux)

### 1. Preparar el servidor

```bash
# Instalar dependencias
sudo apt-get update
sudo apt-get install -y \
    apache2 apache2-dev \
    libapache2-mod-wsgi-py3 \
    python3-dev \
    python3-venv \
    postgresql-client \
    mysql-client

# Crear usuario
sudo useradd -m -s /bin/bash iact
```

### 2. Configurar el proyecto

```bash
# Clone y setup
sudo su - iact
git clone https://github.com/jcg-admin/IACT-api.git
cd IACT-api

# Virtualenv
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias de producción
pip install -r requirements/production.txt

# Configurar .env
Editar .env con los valores del entorno
# Editar con valores de producción
```

### 3. Recolectar archivos estáticos

```bash
python manage.py collectstatic --noinput
```

### 4. Configurar Apache

Crear `/etc/apache2/sites-available/iact-api.conf`:

```apache
<VirtualHost *:80>
    ServerName tu-dominio.com
    ServerAlias www.tu-dominio.com
    
    # Logs
    ErrorLog ${APACHE_LOG_DIR}/iact-api-error.log
    CustomLog ${APACHE_LOG_DIR}/iact-api-access.log combined
    
    # Static files
    Alias /static/ /home/iact/IACT-api/callcentersite/static/
    <Directory /home/iact/IACT-api/callcentersite/static>
        Require all granted
    </Directory>
    
    # Media files
    Alias /media/ /home/iact/IACT-api/callcentersite/media/
    <Directory /home/iact/IACT-api/callcentersite/media>
        Require all granted
    </Directory>
    
    # WSGI
    WSGIScriptAlias / /home/iact/IACT-api/callcentersite/config/wsgi.py
    WSGIDaemonProcess iact-api python-home=/home/iact/IACT-api/venv python-path=/home/iact/IACT-api
    WSGIProcessGroup iact-api
    
    <Directory /home/iact/IACT-api/callcentersite/config>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>
</VirtualHost>
```

### 5. Habilitar sitio

```bash
sudo a2ensite iact-api.conf
sudo a2enmod wsgi
sudo apache2ctl configtest
sudo systemctl restart apache2
```

### 6. Verificar

```bash
# Ver estado de Apache
sudo systemctl status apache2

# Ver logs
sudo tail -f /var/log/apache2/iact-api-error.log
sudo tail -f /var/log/apache2/iact-api-access.log

# Verificar acceso
curl http://localhost/api/
```

## Bases de Datos

### PostgreSQL (Default - iact_analytics)

```bash
# Conexión
PGPASSWORD='django_pass' psql -h 192.168.56.11 -U django_user -d iact_analytics

# Migraciones
python manage.py migrate
```

### MariaDB (ivr_legacy - READ-ONLY)

```bash
# Conexión
mysql -h 192.168.56.10 -u django_user -p'django_pass' ivr_legacy

# Migraciones (si hay)
python manage.py migrate --database=legacy

# Nota: Este modelo está configurado como READ-ONLY
# Solo se leen datos, no se escriben
```

### Database Router

El archivo `config/database_router.py` define qué apps usan qué base de datos:

```python
# PostgreSQL (default)
- access, alerts, audit, authentication, core, dashboard, 
- ivr, pipeline, reports, users

# MariaDB (ivr_legacy - READ-ONLY)
- ivr_legacy
```

## Contribuciones

Por favor lee CONTRIBUTING.md antes de hacer cambios.

## Licencia

Propiedad de JCG Admin
