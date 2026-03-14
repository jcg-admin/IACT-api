from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.pipeline.models import ETLExecution
from datetime import timedelta


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def etl_status(request):
    """
    Status ultima ejecucion ETL.
    
    CNST-004: Mostrar ultima actualizacion y proxima (NO real-time).
    
    Returns:
        {
            "last_execution": {
                "started_at": "2026-01-15T10:00:00Z",
                "completed_at": "2026-01-15T10:15:00Z",
                "status": "SUCCESS",
                "records_extracted": 1500,
                "records_loaded": 1450
            },
            "next_execution": "2026-01-15T22:00:00Z"
        }
    
    Si no hay ejecuciones:
        {
            "last_execution": null,
            "next_execution": null
        }
    """
    last = ETLExecution.objects.first()
    
    if not last:
        return Response({
            'last_execution': None,
            'next_execution': None,
            'message': 'No hay ejecuciones ETL aun'
        })
    
    # Calcular proxima ejecucion (12 horas despues de ultima)
    next_exec = last.started_at + timedelta(hours=12)
    
    return Response({
        'last_execution': {
            'id': last.id,
            'started_at': last.started_at,
            'completed_at': last.completed_at,
            'status': last.status,
            'records_extracted': last.records_extracted,
            'records_loaded': last.records_loaded,
            'start_date': last.start_date,
            'end_date': last.end_date,
        },
        'next_execution': next_exec,
    })
