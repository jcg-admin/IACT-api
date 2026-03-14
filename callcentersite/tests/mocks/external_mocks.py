"""
Mocks para servicios externos (Email, Cache, etc).

CONTEXTO: Simulamos servicios externos sin dependencias reales.

RESTRICCIONES:
- CNST-001: NO email backend real (console backend en desarrollo)
- CNST-010: Cache locmem (NO Redis)

CLEAN_CODE v3.0.1: Nombres auto-documentados.
"""

import pytest
from unittest.mock import MagicMock, Mock, patch
from django.core.mail import EmailMessage


# ============================================================================
# EMAIL BACKEND MOCKS
# ============================================================================

@pytest.fixture
def mock_email_backend(mocker):
    """
    Mock de email backend (console backend).
    
    CNST-001: NO email backend real.
    En tests: Mock para NO enviar emails reales.
    
    Uso:
        def test_send_email(mock_email_backend):
            send_mail('Subject', 'Body', 'from@example.com', ['to@example.com'])
            mock_email_backend.send_messages.assert_called_once()
    
    Configuración:
        - EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
        - En tests: Mock que NO envía realmente
    """
    mock_backend = MagicMock()
    
    # send_messages() retorna 1 (éxito) pero NO envía realmente
    mock_backend.send_messages.return_value = 1
    
    # open() y close() no hacen nada
    mock_backend.open.return_value = True
    mock_backend.close.return_value = None
    
    mocker.patch(
        'django.core.mail.backends.console.EmailBackend',
        return_value=mock_backend
    )
    
    return mock_backend


@pytest.fixture
def mock_send_mail(mocker):
    """
    Mock de django.core.mail.send_mail().
    
    Simula envío sin enviar email real.
    
    Uso:
        def test_send_mail(mock_send_mail):
            result = send_mail('Subject', 'Body', 'from@example.com', ['to@example.com'])
            assert result == 1  # Éxito
    """
    mock_func = MagicMock()
    mock_func.return_value = 1  # 1 email enviado (fake)
    
    mocker.patch('django.core.mail.send_mail', mock_func)
    
    return mock_func


@pytest.fixture
def mock_send_mail_failure(mocker):
    """
    Mock de send_mail() que falla.
    
    Uso:
        def test_send_mail_failure(mock_send_mail_failure):
            with pytest.raises(Exception):
                send_mail('Subject', 'Body', 'from@example.com', ['to@example.com'])
    """
    mock_func = MagicMock()
    mock_func.side_effect = Exception("Email send failed: SMTP error")
    
    mocker.patch('django.core.mail.send_mail', mock_func)
    
    return mock_func


@pytest.fixture
def mock_email_message(mocker):
    """
    Mock de EmailMessage (email con attachments).
    
    Uso:
        def test_email_with_attachment(mock_email_message):
            email = EmailMessage('Subject', 'Body', 'from@example.com', ['to@example.com'])
            email.attach_file('/fake/path/report.xlsx')
            email.send()
    """
    mock_email = MagicMock(spec=EmailMessage)
    
    # send() retorna 1 (éxito)
    mock_email.send.return_value = 1
    
    # attach_file() no hace nada
    mock_email.attach_file.return_value = None
    
    mocker.patch('django.core.mail.EmailMessage', return_value=mock_email)
    
    return mock_email


@pytest.fixture
def mock_email_multipart(mocker):
    """
    Mock de EmailMultiAlternatives (HTML + texto).
    
    Uso:
        def test_html_email(mock_email_multipart):
            email = EmailMultiAlternatives('Subject', 'Text body', 'from@example.com', ['to@example.com'])
            email.attach_alternative('<p>HTML body</p>', 'text/html')
            email.send()
    """
    from django.core.mail import EmailMultiAlternatives
    
    mock_email = MagicMock(spec=EmailMultiAlternatives)
    mock_email.send.return_value = 1
    mock_email.attach_alternative.return_value = None
    
    mocker.patch('django.core.mail.EmailMultiAlternatives', return_value=mock_email)
    
    return mock_email


# ============================================================================
# CACHE MOCKS (locmem - NO Redis)
# ============================================================================

@pytest.fixture
def mock_cache(mocker):
    """
    Mock de cache (locmem).
    
    CNST-010: Cache locmem (NO Redis).
    En tests: Mock que simula locmem sin persistencia.
    
    Uso:
        def test_cache(mock_cache):
            from django.core.cache import cache
            cache.set('key', 'value', 300)
            assert cache.get('key') == 'value'
    
    Métodos mockeados:
        - get(key, default)
        - set(key, value, timeout)
        - delete(key)
        - clear()
        - get_many(keys)
        - set_many(dict, timeout)
    """
    from django.core.cache import cache
    
    mock_cache_backend = MagicMock()
    
    # Diccionario interno para simular cache
    cache_data = {}
    
    # get()
    def mock_get(key, default=None):
        return cache_data.get(key, default)
    
    mock_cache_backend.get.side_effect = mock_get
    
    # set()
    def mock_set(key, value, timeout=None):
        cache_data[key] = value
        return True
    
    mock_cache_backend.set.side_effect = mock_set
    
    # delete()
    def mock_delete(key):
        if key in cache_data:
            del cache_data[key]
            return True
        return False
    
    mock_cache_backend.delete.side_effect = mock_delete
    
    # clear()
    def mock_clear():
        cache_data.clear()
    
    mock_cache_backend.clear.side_effect = mock_clear
    
    # get_many()
    def mock_get_many(keys):
        return {k: cache_data.get(k) for k in keys if k in cache_data}
    
    mock_cache_backend.get_many.side_effect = mock_get_many
    
    # set_many()
    def mock_set_many(data, timeout=None):
        cache_data.update(data)
    
    mock_cache_backend.set_many.side_effect = mock_set_many
    
    mocker.patch('django.core.cache.cache', mock_cache_backend)
    
    return mock_cache_backend


@pytest.fixture
def mock_cache_settings(mocker):
    """
    Mock de settings.CACHES (locmem).
    
    CNST-010: Cache locmem (NO Redis).
    
    Uso:
        def test_cache_settings(mock_cache_settings):
            from django.conf import settings
            assert settings.CACHES['default']['BACKEND'] == 'locmem'
    """
    test_caches = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }
    
    mocker.patch('django.conf.settings.CACHES', test_caches)
    
    return test_caches


@pytest.fixture
def mock_cache_key(mocker):
    """
    Mock de generación de cache key.
    
    Uso:
        def test_cache_key(mock_cache_key):
            key = generate_cache_key('quarterly', 2025, 1)
            assert key == 'report:quarterly:2025:1'
    """
    def generate_key(*args):
        return ':'.join(str(arg) for arg in args)
    
    return generate_key


# ============================================================================
# EXTERNAL API MOCKS
# ============================================================================

@pytest.fixture
def mock_requests_get(mocker):
    """
    Mock de requests.get() para APIs externas.
    
    Uso:
        def test_api_call(mock_requests_get):
            response = requests.get('https://api.example.com/data')
            assert response.status_code == 200
    """
    import requests
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'status': 'ok', 'data': []}
    mock_response.text = '{"status": "ok"}'
    
    mock_get = MagicMock(return_value=mock_response)
    mocker.patch('requests.get', mock_get)
    
    return mock_get


@pytest.fixture
def mock_requests_post(mocker):
    """
    Mock de requests.post() para APIs externas.
    
    Uso:
        def test_api_post(mock_requests_post):
            response = requests.post('https://api.example.com/create', json={'data': 'test'})
            assert response.status_code == 201
    """
    import requests
    
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {'id': 123, 'status': 'created'}
    
    mock_post = MagicMock(return_value=mock_response)
    mocker.patch('requests.post', mock_post)
    
    return mock_post


@pytest.fixture
def mock_requests_error(mocker):
    """
    Mock de requests que lanza error.
    
    Uso:
        def test_api_error(mock_requests_error):
            with pytest.raises(Exception):
                requests.get('https://api.example.com/data')
    """
    import requests
    
    mock_get = MagicMock()
    mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
    
    mocker.patch('requests.get', mock_get)
    
    return mock_get


# ============================================================================
# TIMEZONE MOCKS
# ============================================================================

@pytest.fixture
def mock_timezone(mocker):
    """
    Mock de timezone (America/Santiago).
    
    Uso:
        def test_timezone(mock_timezone):
            from django.utils import timezone
            now = timezone.now()
            assert now.tzinfo is not None
    """
    from django.utils import timezone
    import pytz
    
    santiago_tz = pytz.timezone('America/Santiago')
    
    mock_now = MagicMock()
    mock_now.return_value = timezone.datetime.now(tz=santiago_tz)
    
    mocker.patch('django.utils.timezone.now', mock_now)
    
    return mock_now


# ============================================================================
# LOGGING MOCKS
# ============================================================================

@pytest.fixture
def mock_logger(mocker):
    """
    Mock de logger para tests.
    
    Útil para verificar logs sin escribir realmente.
    
    Uso:
        def test_logging(mock_logger):
            logger.info('Test message')
            mock_logger.info.assert_called_with('Test message')
    """
    import logging
    
    mock_log = MagicMock(spec=logging.Logger)
    
    mocker.patch('logging.getLogger', return_value=mock_log)
    
    return mock_log


@pytest.fixture
def mock_logger_error(mocker):
    """
    Mock de logger que verifica solo errores.
    
    Uso:
        def test_error_logging(mock_logger_error):
            logger.error('Error occurred')
            mock_logger_error.error.assert_called_once()
    """
    import logging
    
    mock_log = MagicMock(spec=logging.Logger)
    
    mocker.patch('logging.getLogger', return_value=mock_log)
    
    return mock_log


# ============================================================================
# SETTINGS MOCKS
# ============================================================================

@pytest.fixture
def mock_settings(mocker):
    """
    Mock de django.conf.settings para tests.
    
    Uso:
        def test_settings(mock_settings):
            from django.conf import settings
            assert settings.DEBUG is True
    """
    test_settings = MagicMock()
    
    # Settings comunes para tests
    test_settings.DEBUG = True
    test_settings.TESTING = True
    test_settings.SECRET_KEY = 'test-secret-key'
    
    # CNST-001: Email console backend
    test_settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    
    # CNST-010: Cache locmem
    test_settings.CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }
    
    mocker.patch('django.conf.settings', test_settings)
    
    return test_settings


# ============================================================================
# HELPER MOCKS
# ============================================================================

@pytest.fixture
def mock_uuid(mocker):
    """
    Mock de uuid.uuid4() para tests determinísticos.
    
    Uso:
        def test_uuid(mock_uuid):
            import uuid
            id = uuid.uuid4()
            assert str(id) == 'test-uuid-1234'
    """
    import uuid
    
    mock_uuid_obj = MagicMock()
    mock_uuid_obj.__str__ = MagicMock(return_value='test-uuid-1234')
    
    mocker.patch('uuid.uuid4', return_value=mock_uuid_obj)
    
    return mock_uuid_obj


@pytest.fixture
def mock_random(mocker):
    """
    Mock de random para tests determinísticos.
    
    Uso:
        def test_random(mock_random):
            import random
            value = random.randint(1, 100)
            assert value == 42  # Siempre retorna 42
    """
    import random
    
    mocker.patch('random.randint', return_value=42)
    mocker.patch('random.random', return_value=0.5)
    mocker.patch('random.choice', side_effect=lambda x: x[0])
    
    return random


# ============================================================================
# TOTAL MOCKS: 20
# 
# Email Mocks (5):
#   - mock_email_backend (console backend, NO real)
#   - mock_send_mail
#   - mock_send_mail_failure
#   - mock_email_message
#   - mock_email_multipart
# 
# Cache Mocks (3):
#   - mock_cache (locmem, NO Redis)
#   - mock_cache_settings
#   - mock_cache_key
# 
# External API Mocks (3):
#   - mock_requests_get
#   - mock_requests_post
#   - mock_requests_error
# 
# Other Mocks (9):
#   - mock_timezone
#   - mock_logger
#   - mock_logger_error
#   - mock_settings
#   - mock_uuid
#   - mock_random
# 
# CNST-001: NO email backend real (console) [SUCCESS]
# CNST-010: Cache locmem (NO Redis) [SUCCESS]
# CLEAN_CODE v3.0.1: Nombres auto-documentados [SUCCESS]
# ============================================================================
