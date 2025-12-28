"""
Custom middleware to handle non-standard hostnames in Docker containers.

Django's SecurityMiddleware validates HTTP_HOST against RFC 1034/1035 before
checking ALLOWED_HOSTS. This middleware normalizes non-standard hostnames
(like 'serv_fd:8000') to a valid format before SecurityMiddleware processes them.
"""
import re
from django.conf import settings


class HostValidationMiddleware:
    """
    Middleware to normalize HTTP_HOST header for non-standard hostnames.
    
    This middleware should be placed BEFORE SecurityMiddleware in MIDDLEWARE list.
    It normalizes hostnames like 'serv_fd:8000' to 'localhost:8000' or removes
    the port if ALLOWED_HOSTS contains '*'.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Get the HTTP_HOST header
        host = request.META.get('HTTP_HOST', '')
        
        if host:
            # Check if hostname is non-standard (doesn't contain a dot and isn't an IP)
            hostname = host.split(':')[0]  # Remove port if present
            is_ip = re.match(r'^(\d{1,3}\.){3}\d{1,3}$', hostname)
            has_dot = '.' in hostname
            is_localhost = hostname in ['localhost', '127.0.0.1']
            
            # If hostname is non-standard and ALLOWED_HOSTS allows all hosts
            if not is_ip and not has_dot and not is_localhost:
                if '*' in settings.ALLOWED_HOSTS:
                    # Normalize to localhost to pass RFC validation
                    # SecurityMiddleware will still allow it because ALLOWED_HOSTS = ['*']
                    port = host.split(':')[1] if ':' in host else ''
                    if port:
                        new_host = f'localhost:{port}'
                    else:
                        new_host = 'localhost'
                    
                    # Update HTTP_HOST header
                    request.META['HTTP_HOST'] = new_host
                    # Also update SERVER_NAME if present
                    if 'SERVER_NAME' in request.META:
                        request.META['SERVER_NAME'] = 'localhost'
        
        response = self.get_response(request)
        return response

