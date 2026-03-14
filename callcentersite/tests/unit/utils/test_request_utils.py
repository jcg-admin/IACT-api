"""
Tests para RequestUtils.

Verificar funciones utilitarias para requests HTTP.
"""
import pytest
from unittest.mock import Mock
from apps.utils.request import (
    get_client_ip,
    get_user_agent,
    should_exclude_path,
    is_ajax_request,
    get_request_info,
)


class TestGetClientIP:
    """Tests para get_client_ip()."""
    
    def test_get_ip_from_x_forwarded_for(self):
        """Test obtener IP de X-Forwarded-For (proxy)."""
        request = Mock()
        request.META = {
            'HTTP_X_FORWARDED_FOR': '192.168.1.100, 10.0.0.1',
            'REMOTE_ADDR': '127.0.0.1',
        }
        
        ip = get_client_ip(request)
        assert ip == '192.168.1.100'  # Primera IP (cliente real)
    
    def test_get_ip_from_x_real_ip(self):
        """Test obtener IP de X-Real-IP (nginx)."""
        request = Mock()
        request.META = {
            'HTTP_X_REAL_IP': '192.168.1.200',
            'REMOTE_ADDR': '127.0.0.1',
        }
        
        ip = get_client_ip(request)
        assert ip == '192.168.1.200'
    
    def test_get_ip_from_remote_addr(self):
        """Test obtener IP de REMOTE_ADDR (conexión directa)."""
        request = Mock()
        request.META = {
            'REMOTE_ADDR': '203.0.113.50',
        }
        
        ip = get_client_ip(request)
        assert ip == '203.0.113.50'
    
    def test_priority_x_forwarded_for_over_remote_addr(self):
        """Test X-Forwarded-For tiene prioridad sobre REMOTE_ADDR."""
        request = Mock()
        request.META = {
            'HTTP_X_FORWARDED_FOR': '192.168.1.100',
            'REMOTE_ADDR': '127.0.0.1',
        }
        
        ip = get_client_ip(request)
        assert ip == '192.168.1.100'  # X-Forwarded-For prioritario
    
    def test_handles_empty_meta(self):
        """Test maneja META vacío sin error."""
        request = Mock()
        request.META = {}
        
        ip = get_client_ip(request)
        assert ip == ''  # Cadena vacía si no hay IP


class TestGetUserAgent:
    """Tests para get_user_agent()."""
    
    def test_get_user_agent_present(self):
        """Test obtener User-Agent cuando está presente."""
        request = Mock()
        request.META = {
            'HTTP_USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        }
        
        ua = get_user_agent(request)
        assert ua == 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    
    def test_get_user_agent_missing(self):
        """Test User-Agent ausente retorna cadena vacía."""
        request = Mock()
        request.META = {}
        
        ua = get_user_agent(request)
        assert ua == ''
    
    def test_strips_whitespace(self):
        """Test elimina espacios en blanco."""
        request = Mock()
        request.META = {
            'HTTP_USER_AGENT': '  Mozilla/5.0  ',
        }
        
        ua = get_user_agent(request)
        assert ua == 'Mozilla/5.0'


class TestShouldExcludePath:
    """Tests para should_exclude_path()."""
    
    def test_excludes_admin_paths(self):
        """Test excluye paths de admin."""
        assert should_exclude_path('/admin/') is True
        assert should_exclude_path('/admin/users/') is True
    
    def test_excludes_static_paths(self):
        """Test excluye paths estáticos."""
        assert should_exclude_path('/static/') is True
        assert should_exclude_path('/static/css/style.css') is True
    
    def test_excludes_media_paths(self):
        """Test excluye paths de media."""
        assert should_exclude_path('/media/') is True
        assert should_exclude_path('/media/uploads/image.jpg') is True
    
    def test_does_not_exclude_api_paths(self):
        """Test NO excluye paths de API normales."""
        assert should_exclude_path('/api/users/') is False
        assert should_exclude_path('/api/v1/products/') is False
    
    def test_custom_excluded_paths(self):
        """Test paths excluidos personalizados."""
        custom_excluded = ['/custom/', '/special/']
        
        assert should_exclude_path('/custom/', custom_excluded) is True
        assert should_exclude_path('/custom/page/', custom_excluded) is True
        assert should_exclude_path('/special/', custom_excluded) is True
        assert should_exclude_path('/api/', custom_excluded) is False
    
    def test_combines_default_and_custom(self):
        """Test combina paths default y custom."""
        custom = ['/mypath/']
        
        # Default excluido
        assert should_exclude_path('/admin/', custom) is True
        # Custom excluido
        assert should_exclude_path('/mypath/', custom) is True
        # No excluido
        assert should_exclude_path('/api/', custom) is False


class TestIsAjaxRequest:
    """Tests para is_ajax_request()."""
    
    def test_detects_xmlhttprequest_header(self):
        """Test detecta header X-Requested-With (jQuery)."""
        request = Mock()
        request.META = {
            'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest',
        }
        
        assert is_ajax_request(request) is True
    
    def test_detects_json_accept_header(self):
        """Test detecta Accept: application/json."""
        request = Mock()
        request.META = {
            'HTTP_ACCEPT': 'application/json',
        }
        
        assert is_ajax_request(request) is True
    
    def test_non_ajax_request(self):
        """Test request normal no es AJAX."""
        request = Mock()
        request.META = {
            'HTTP_ACCEPT': 'text/html',
        }
        
        assert is_ajax_request(request) is False
    
    def test_empty_meta_not_ajax(self):
        """Test META vacío no es AJAX."""
        request = Mock()
        request.META = {}
        
        assert is_ajax_request(request) is False


class TestGetRequestInfo:
    """Tests para get_request_info()."""
    
    def test_get_complete_request_info(self):
        """Test obtiene información completa del request."""
        request = Mock()
        request.META = {
            'HTTP_X_FORWARDED_FOR': '192.168.1.100',
            'HTTP_USER_AGENT': 'Mozilla/5.0',
            'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest',
        }
        request.path = '/api/users/'
        request.method = 'GET'
        request.is_secure.return_value = True
        request.user.is_authenticated = True
        request.user.username = 'testuser'
        
        info = get_request_info(request)
        
        assert info['ip'] == '192.168.1.100'
        assert info['user_agent'] == 'Mozilla/5.0'
        assert info['path'] == '/api/users/'
        assert info['method'] == 'GET'
        assert info['is_ajax'] is True
        assert info['is_secure'] is True
        assert info['user'] == 'testuser'
    
    def test_anonymous_user(self):
        """Test usuario anónimo."""
        request = Mock()
        request.META = {}
        request.path = '/'
        request.method = 'GET'
        request.is_secure.return_value = False
        request.user.is_authenticated = False
        
        info = get_request_info(request)
        
        assert info['user'] == 'Anonymous'
