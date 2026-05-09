import pytest
from django.test import RequestFactory
from apps.utils.network import get_client_ip, get_user_agent, get_request_metadata


@pytest.fixture
def request_factory():
    """Django RequestFactory."""
    return RequestFactory()


class TestGetClientIP:
    """Tests get_client_ip()."""
    
    def test_direct_remote_addr(self, request_factory):
        """IP desde REMOTE_ADDR sin proxy."""
        request = request_factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.100'
        
        ip = get_client_ip(request)
        assert ip == '192.168.1.100'
    
    def test_x_forwarded_for_single(self, request_factory):
        """IP desde X-Forwarded-For (single IP)."""
        request = request_factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.1'
        request.META['REMOTE_ADDR'] = '10.0.0.1'  # Proxy
        
        ip = get_client_ip(request)
        assert ip == '203.0.113.1'
    
    def test_x_forwarded_for_multiple(self, request_factory):
        """IP desde X-Forwarded-For (multiples IPs)."""
        request = request_factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.1, 10.0.0.1, 10.0.0.2'
        
        ip = get_client_ip(request)
        assert ip == '203.0.113.1'  # Primer IP
    
    def test_x_real_ip(self, request_factory):
        """IP desde X-Real-IP."""
        request = request_factory.get('/')
        request.META['HTTP_X_REAL_IP'] = '203.0.113.5'
        request.META['REMOTE_ADDR'] = '10.0.0.1'
        
        ip = get_client_ip(request)
        assert ip == '203.0.113.5'
    
    def test_priority_x_forwarded_over_real_ip(self, request_factory):
        """X-Forwarded-For tiene prioridad sobre X-Real-IP."""
        request = request_factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.1'
        request.META['HTTP_X_REAL_IP'] = '203.0.113.2'
        
        ip = get_client_ip(request)
        assert ip == '203.0.113.1'


class TestGetUserAgent:
    """Tests get_user_agent()."""
    
    def test_user_agent_present(self, request_factory):
        """User-Agent cuando presente."""
        request = request_factory.get('/')
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 (Test)'
        
        ua = get_user_agent(request)
        assert ua == 'Mozilla/5.0 (Test)'
    
    def test_user_agent_missing(self, request_factory):
        """User-Agent cuando ausente."""
        request = request_factory.get('/')
        
        ua = get_user_agent(request)
        assert ua == ''


class TestGetRequestMetadata:
    """Tests get_request_metadata()."""
    
    def test_complete_metadata(self, request_factory):
        """Metadata completo."""
        request = request_factory.get('/api/v1/calls/?page=1')
        request.META['REMOTE_ADDR'] = '192.168.1.100'
        request.META['HTTP_USER_AGENT'] = 'TestClient/1.0'
        request.META['QUERY_STRING'] = 'page=1'
        
        metadata = get_request_metadata(request)
        
        assert metadata['ip'] == '192.168.1.100'
        assert metadata['user_agent'] == 'TestClient/1.0'
        assert metadata['method'] == 'GET'
        assert metadata['path'] == '/api/v1/calls/'
        assert metadata['query_string'] == 'page=1'
