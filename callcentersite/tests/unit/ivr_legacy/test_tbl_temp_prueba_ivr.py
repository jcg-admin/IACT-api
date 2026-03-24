"""
Tests para TblTempPruebaIvr — modelo activo de apps/ivr.

Verifica que el modelo está correctamente definido para consumir
la tabla tbl_temp_prueba_ivr de MariaDB (managed=False, READ-ONLY).

Schema creado por:
    scripts/provisioners/mariadb/schema_temp_prueba.sh
"""
import pytest


class TestTblTempPruebaIvrModelo:
    """Tests de estructura del modelo TblTempPruebaIvr."""

    def test_modelo_importable(self):
        """TblTempPruebaIvr debe ser importable desde apps.ivr.models."""
        from apps.ivr.models import TblTempPruebaIvr
        assert TblTempPruebaIvr is not None

    def test_modelo_es_unmanaged(self):
        """managed=False: Django no gestiona el schema (lo hace el provisioner)."""
        from apps.ivr.models import TblTempPruebaIvr
        assert TblTempPruebaIvr._meta.managed is False

    def test_modelo_db_table(self):
        """db_table debe apuntar a tbl_temp_prueba_ivr."""
        from apps.ivr.models import TblTempPruebaIvr
        assert TblTempPruebaIvr._meta.db_table == 'tbl_temp_prueba_ivr'

    def test_modelo_tiene_campo_numero(self):
        """El modelo debe tener el campo 'numero'."""
        from apps.ivr.models import TblTempPruebaIvr
        field_names = [f.name for f in TblTempPruebaIvr._meta.get_fields()]
        assert 'numero' in field_names

    def test_modelo_tiene_campo_id(self):
        """El modelo debe tener el campo 'id' (PK)."""
        from apps.ivr.models import TblTempPruebaIvr
        field_names = [f.name for f in TblTempPruebaIvr._meta.get_fields()]
        assert 'id' in field_names

    def test_campo_numero_max_length(self):
        """El campo 'numero' debe tener max_length=10."""
        from apps.ivr.models import TblTempPruebaIvr
        field = TblTempPruebaIvr._meta.get_field('numero')
        assert field.max_length == 10

    def test_ordering_por_id(self):
        """El modelo debe ordenarse por id."""
        from apps.ivr.models import TblTempPruebaIvr
        assert TblTempPruebaIvr._meta.ordering == ['id']


class TestTblTempPruebaIvrSerializer:
    """Tests de estructura del serializer."""

    def test_serializer_importable(self):
        """TblTempPruebaIvrSerializer debe ser importable."""
        from apps.ivr.serializers import TblTempPruebaIvrSerializer
        assert TblTempPruebaIvrSerializer is not None

    def test_serializer_campos(self):
        """El serializer debe exponer id y numero."""
        from apps.ivr.serializers import TblTempPruebaIvrSerializer
        campos = list(TblTempPruebaIvrSerializer().fields.keys())
        assert 'id' in campos
        assert 'numero' in campos

    def test_serializer_solo_dos_campos(self):
        """El serializer solo debe tener 2 campos: id y numero."""
        from apps.ivr.serializers import TblTempPruebaIvrSerializer
        campos = list(TblTempPruebaIvrSerializer().fields.keys())
        assert len(campos) == 2

    def test_serializer_campos_son_readonly(self):
        """Todos los campos deben ser read_only (CNST-003)."""
        from apps.ivr.serializers import TblTempPruebaIvrSerializer
        s = TblTempPruebaIvrSerializer()
        for field_name, field in s.fields.items():
            assert field.read_only is True, \
                f"Campo '{field_name}' debe ser read_only (CNST-003)"


class TestTblTempPruebaIvrViewSet:
    """Tests de estructura del viewset."""

    def test_viewset_importable(self):
        """TblTempPruebaIvrViewSet debe ser importable."""
        from apps.ivr.viewsets import TblTempPruebaIvrViewSet
        assert TblTempPruebaIvrViewSet is not None

    def test_viewset_es_readonly(self):
        """El viewset debe ser ReadOnlyModelViewSet."""
        from rest_framework import viewsets as drf_viewsets
        from apps.ivr.viewsets import TblTempPruebaIvrViewSet
        assert issubclass(TblTempPruebaIvrViewSet, drf_viewsets.ReadOnlyModelViewSet)
