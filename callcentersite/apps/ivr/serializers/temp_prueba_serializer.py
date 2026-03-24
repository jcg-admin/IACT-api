"""
Serializer para TblTempPruebaIvr.

CNST-003: READ-ONLY (MariaDB ivr_legacy — tbl_temp_prueba_ivr).
Schema creado por scripts/provisioners/mariadb/schema_temp_prueba.sh
"""
from rest_framework import serializers
from apps.ivr.models import TblTempPruebaIvr


class TblTempPruebaIvrSerializer(serializers.ModelSerializer):
    """
    Serializer READ-ONLY para tbl_temp_prueba_ivr.

    Campos:
        id     — identificador único (PK)
        numero — número random de 10 caracteres

    CNST-003: todos los campos son read_only.
    """

    class Meta:
        model  = TblTempPruebaIvr
        fields = ('id', 'numero')
        read_only_fields = ('id', 'numero')
