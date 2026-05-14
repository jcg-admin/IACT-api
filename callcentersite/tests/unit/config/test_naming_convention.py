"""
tests/unit/config/test_naming_convention.py

DT-NAMING-001 — Regresión de convención de nombres de tests.

Verifica que ningún archivo nuevo viola la convención §2
del plan TDD v5.1.0:
  - Sin directorio faseN/ dentro de tests/unit/
  - Sin nombre de archivo test_uc_*.py
  - Sin nombres genéricos prohibidos (test_models.py, etc.)
  - Sin código de ciclo en nombres (f0_t6, fase1)
"""
import os
import re
import pytest

UNIT_ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
UNIT_ROOT = os.path.abspath(os.path.join(UNIT_ROOT, 'unit'))

_PROHIBITED_DIRS = re.compile(r'^fase\d+$')
_PROHIBITED_FILE_PREFIX = re.compile(r'^test_uc_')
_PROHIBITED_CYCLE_CODE = re.compile(r'fase\d+|f\d+_t\d+')
_PROHIBITED_GENERIC = frozenset({
    'test_models.py',
    'test_views.py',
    'test_services.py',
    'test_api.py',
    'test_serializers.py',
})


def _collect_violations():
    dir_violations = []
    file_violations = []

    for root, dirs, files in os.walk(UNIT_ROOT):
        rel_root = os.path.relpath(root, UNIT_ROOT)

        # Verificar directorios
        for d in dirs:
            if d.startswith('__'):
                continue
            if _PROHIBITED_DIRS.match(d):
                dir_violations.append(f"Directorio prohibido: tests/unit/{rel_root}/{d}")

        # Verificar archivos
        for fname in files:
            if not fname.endswith('.py') or fname.startswith('__'):
                continue
            rel_path = os.path.join(rel_root, fname).replace('\\', '/')
            full_rel = f"tests/unit/{rel_path}"

            if _PROHIBITED_FILE_PREFIX.match(fname):
                file_violations.append(f"Prefijo 'test_uc_' prohibido: {full_rel}")
            elif _PROHIBITED_CYCLE_CODE.search(fname):
                file_violations.append(f"Código de ciclo en nombre: {full_rel}")
            elif fname in _PROHIBITED_GENERIC:
                file_violations.append(f"Nombre genérico prohibido: {full_rel}")

    return dir_violations, file_violations


class TestNamingConvention:

    def test_sin_directorios_fase(self):
        """Ningún subdirectorio de tests/unit/ se llama faseN."""
        dir_violations, _ = _collect_violations()
        assert dir_violations == [], (
            "Directorios prohibidos detectados (viola §2.1 del plan TDD v5.1.0):\n"
            + "\n".join(f"  - {v}" for v in dir_violations)
        )

    def test_sin_codigo_uc_en_nombre(self):
        """Ningún archivo comienza con test_uc_."""
        _, file_violations = _collect_violations()
        uc_violations = [v for v in file_violations if 'test_uc_' in v]
        assert uc_violations == [], (
            "Archivos con código UC en nombre (viola §2.2 Regla A):\n"
            + "\n".join(f"  - {v}" for v in uc_violations)
        )

    def test_sin_codigo_ciclo_en_nombre(self):
        """Ningún archivo contiene faseN o f0_t6 en el nombre."""
        _, file_violations = _collect_violations()
        cycle_violations = [v for v in file_violations if 'ciclo' in v]
        assert cycle_violations == [], (
            "Archivos con código de ciclo en nombre (viola §2.2 Regla B):\n"
            + "\n".join(f"  - {v}" for v in cycle_violations)
        )

    def test_sin_nombres_genericos(self):
        """Ningún archivo usa nombres genéricos prohibidos."""
        _, file_violations = _collect_violations()
        generic_violations = [v for v in file_violations if 'genérico' in v]
        assert generic_violations == [], (
            "Archivos con nombre genérico prohibido (viola §2.2 Regla C):\n"
            + "\n".join(f"  - {v}" for v in generic_violations)
        )

    def test_total_cero_violaciones(self):
        """Test integrador: cero violaciones en total."""
        dir_violations, file_violations = _collect_violations()
        all_violations = dir_violations + file_violations
        assert all_violations == [], (
            f"Total: {len(all_violations)} violación(es) de la convención §2 "
            "del plan TDD v5.1.0:\n"
            + "\n".join(f"  - {v}" for v in all_violations)
        )
