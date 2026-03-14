# Flujo: scripts/check_tools.sh

Verifica el estado del entorno de desarrollo. Solo lectura, no instala nada.

## Invocacion

```bash
source venv/bin/activate   # recomendado
bash scripts/check_tools.sh
```

## Variables de entorno opcionales

| Variable        | Default (desde .env)    |
|-----------------|-------------------------|
| POSTGRES_HOST   | DB_HOST                 |
| POSTGRES_PORT   | DB_PORT                 |
| MARIADB_HOST    | IVR_DB_HOST             |
| MARIADB_PORT    | IVR_DB_PORT             |

## Contadores

- `OK_COUNT` incrementa por cada check exitoso
- `WARNINGS` incrementa por herramienta opcional ausente
- `ERRORS` incrementa por dependencia critica ausente

## Secciones

```
check_tools.sh
     |
     |-- [1] check_python
     |         python3 >= 3.11 ?     OK / ERROR
     |         pip disponible ?      OK / ERROR
     |         venv disponible ?     OK / WARN
     |
     |-- [2] check_python_packages
     |
     |-- [3] check_testing_tools
     |
     |-- [4] check_dev_extras
     |
     |-- [5] check_code_quality
     |
     |-- [6] check_system_tools
     |
     |-- [7] check_database_connectivity
     |
     |-- [8] check_environment_file
     |
     +-- [9] check_project_structure
```

## Paquetes Python verificados

### Core (ERROR si falta)

| import          | pip package       |
|-----------------|-------------------|
| django          | django            |
| psycopg2        | psycopg2-binary   |
| MySQLdb         | mysqlclient       |

### Aplicacion (WARN si falta)

| import                  | pip package                   |
|-------------------------|-------------------------------|
| rest_framework          | djangorestframework           |
| rest_framework_simplejwt| djangorestframework-simplejwt |
| django_filters          | django-filter                 |
| drf_spectacular         | drf-spectacular               |
| apscheduler             | APScheduler                   |
| boto3                   | boto3                         |
| openpyxl                | openpyxl                      |
| decouple                | python-decouple               |
| pytz                    | pytz                          |
| dateutil                | python-dateutil               |
| jwt                     | PyJWT                         |
| sqlparse                | sqlparse                      |
| tzlocal                 | tzlocal                       |
| yaml                    | PyYAML                        |

### Testing (WARN si falta)

| import       | pip package  |
|--------------|--------------|
| pytest       | pytest       |
| pytest_django| pytest-django|
| pytest_cov   | pytest-cov   |
| factory      | factory-boy  |
| faker        | faker        |
| coverage     | coverage     |

### Dev extras (WARN si falta)

| import           | pip package           |
|------------------|-----------------------|
| debug_toolbar    | django-debug-toolbar  |
| django_extensions| django-extensions     |
| IPython          | ipython               |

### Calidad de codigo (WARN si falta)

| comando | pip package |
|---------|-------------|
| black   | black       |
| flake8  | flake8      |
| isort   | isort       |
| mypy    | mypy        |

## Decision final

```
ERRORS == 0  AND  WARNINGS == 0
--> "Entorno listo para desarrollo."
    exit 0

ERRORS == 0  AND  WARNINGS > 0
--> "Entorno funcional con advertencias."
    exit 0

ERRORS > 0
--> "Entorno incompleto. Corregir errores."
    exit 1
```

## Resultado en entorno local (Ubuntu 24.04)

```
OK:           56
Advertencias:  1   (manage.py no existe aun)
Errores:       0
Tiempo:        4s
```
