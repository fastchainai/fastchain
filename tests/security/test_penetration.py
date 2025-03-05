"""Dynamic security tests using OWASP ZAP-like approaches."""
import pytest
import requests
from urllib.parse import urljoin
import re
import json
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class SecurityTestConfig:
    """Configuration for security tests."""
    BASE_URL = "http://localhost:5000"  # Update with your application URL
    ENDPOINTS = [
        "/api/v1/agents/registry/",
        "/api/v1/chat/",
        "/api/v1/intent/process",
        "/system/status",
    ]

@pytest.mark.security
class TestWebSecurity:
    """Web application security tests."""
    
    def test_secure_headers(self):
        """Test for secure HTTP headers."""
        endpoint = "/api/v1/agents/registry/"
        response = requests.get(urljoin(SecurityTestConfig.BASE_URL, endpoint))
        headers = response.headers
        
        # Check for security headers
        assert headers.get('X-Content-Type-Options') == 'nosniff', \
            "Missing or incorrect X-Content-Type-Options header"
        assert headers.get('X-Frame-Options') in ['DENY', 'SAMEORIGIN'], \
            "Missing or incorrect X-Frame-Options header"
        assert 'X-XSS-Protection' in headers, \
            "Missing X-XSS-Protection header"
    
    def test_sql_injection_prevention(self):
        """Test endpoints for SQL injection vulnerabilities."""
        sql_injection_payloads = [
            "' OR '1'='1",
            "; DROP TABLE users;--",
            "' UNION SELECT * FROM users--",
        ]
        
        for endpoint in SecurityTestConfig.ENDPOINTS:
            url = urljoin(SecurityTestConfig.BASE_URL, endpoint)
            for payload in sql_injection_payloads:
                response = requests.get(
                    url,
                    params={"query": payload},
                    allow_redirects=False
                )
                assert response.status_code in [400, 401, 403, 404], \
                    f"Endpoint {endpoint} might be vulnerable to SQL injection"
    
    def test_xss_prevention(self):
        """Test for Cross-Site Scripting (XSS) vulnerabilities."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            '<img src="x" onerror="alert(\'xss\')">'
        ]
        
        for endpoint in SecurityTestConfig.ENDPOINTS:
            url = urljoin(SecurityTestConfig.BASE_URL, endpoint)
            for payload in xss_payloads:
                response = requests.post(
                    url,
                    json={"message": payload},
                    allow_redirects=False
                )
                assert response.status_code in [400, 401, 403, 404], \
                    f"Endpoint {endpoint} might be vulnerable to XSS"
                if response.headers.get('content-type') == 'application/json':
                    assert payload not in response.text, \
                        f"Endpoint {endpoint} reflects XSS payload in response"
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        endpoint = "/api/v1/chat/"
        url = urljoin(SecurityTestConfig.BASE_URL, endpoint)
        
        # Send multiple requests rapidly
        responses = []
        for _ in range(50):  # Adjust number based on your rate limit
            responses.append(requests.post(url, json={"message": "test"}))
        
        # Check if rate limiting is working
        assert any(r.status_code == 429 for r in responses), \
            "Rate limiting may not be properly configured"
    
    def test_auth_bypass_prevention(self):
        """Test for authentication bypass vulnerabilities."""
        auth_bypass_attempts = [
            {"Authorization": "None"},
            {"Authorization": "Bearer invalid_token"},
            {"Authorization": "Basic invalid_base64"},
        ]
        
        protected_endpoints = ["/api/v1/agents/registry/", "/api/v1/chat/"]
        for endpoint in protected_endpoints:
            url = urljoin(SecurityTestConfig.BASE_URL, endpoint)
            for headers in auth_bypass_attempts:
                response = requests.get(url, headers=headers)
                assert response.status_code in [401, 403], \
                    f"Endpoint {endpoint} might be vulnerable to auth bypass"

@pytest.mark.security
class TestAPISecurityMisconfigurations:
    """Test for common API security misconfigurations."""
    
    def test_error_response_information_disclosure(self):
        """Test that error responses don't leak sensitive information."""
        for endpoint in SecurityTestConfig.ENDPOINTS:
            url = urljoin(SecurityTestConfig.BASE_URL, endpoint)
            response = requests.get(
                url,
                params={"invalid": "parameter"},
                headers={"Accept": "application/json"}
            )
            
            if response.status_code >= 400:
                error_response = response.json()
                # Check that error messages don't contain sensitive information
                assert "stack" not in error_response, \
                    f"Endpoint {endpoint} leaks stack trace"
                assert "exception" not in error_response, \
                    f"Endpoint {endpoint} leaks exception details"
    
    def test_cors_configuration(self):
        """Test CORS configuration."""
        origins = [
            "https://evil.com",
            "http://attacker.com",
            None
        ]
        
        for endpoint in SecurityTestConfig.ENDPOINTS:
            url = urljoin(SecurityTestConfig.BASE_URL, endpoint)
            for origin in origins:
                headers = {"Origin": origin} if origin else {}
                response = requests.options(url, headers=headers)
                
                if origin:
                    assert response.headers.get('Access-Control-Allow-Origin') != '*', \
                        f"Endpoint {endpoint} allows all origins"
                    assert origin not in response.headers.get('Access-Control-Allow-Origin', ''), \
                        f"Endpoint {endpoint} allows unauthorized origin: {origin}"
