# Tests End-to-End

Tests que verifican flujos completos de usuario.

## Ejemplos
- Login -> Crear usuario -> Asignar funciones -> Logout
- ETL trigger -> Proceso completo -> Verificar resultados

## Ejecución
```bash
pytest tests/e2e/ -v --tb=short
```
