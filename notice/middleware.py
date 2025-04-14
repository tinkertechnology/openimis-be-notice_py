import time
from django.http import HttpRequest, HttpResponse
from django.urls import resolve
from django.conf import settings
from django.utils import timezone
from .models import RequestLog
import json
import logging
logger = logging.getLogger('request_logger')
logging.basicConfig(level=logging.DEBUG)

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logging_enabled = getattr(settings, 'REQUEST_LOGGING_ENABLED', True)
        logger.debug(f"Middleware initialized. Logging enabled: {self.logging_enabled}")

    def __call__(self, request: HttpRequest):
        if not self.logging_enabled:
            return self.get_response(request)

        start_time = time.time()
        route_name = self.get_route_name(request)
        app_name = self.get_app_name(request)  # New method
        request_data = self.capture_request_data(request)
        
        response = self.get_response(request)
        
        duration_ms = (time.time() - start_time) * 1000
        response_data = self.capture_response_data(response)
        
        try:
            self.save_log(request, response, app_name, route_name, request_data, response_data, duration_ms)
            logger.debug(f"Logged request: {app_name}:{route_name}")
        except Exception as e:
            logger.error(f"Failed to save log: {str(e)}")
        
        return response

    def get_route_name(self, request):
        try:
            resolved = resolve(request.path_info)
            return resolved.url_name or request.path_info
        except:
            return request.path_info

    def get_app_name(self, request):
            """Extract the Django app name from the resolved view or URL pattern."""
            try:
                resolved = resolve(request.path_info)
                # import pdb;pdb.set_trace()
                # Get the app name from the view's module or URL configuration
                if hasattr(resolved.func, '__module__'):
                    module_name = resolved.func.__module__
                    # Extract app name from module (e.g., 'yourproject.user.views' -> 'user')
                    app_name = module_name.split('.')[1] if len(module_name.split('.')) > 1 else "unknown"
                    return app_name
                return resolved.app_name or "unknown"  # Fallback to app_name if available
            except Exception as e:
                logger.debug(f"Failed to resolve app name: {str(e)}")
                # Fallback: infer from path (optional, can be removed if not needed)
                if request.path.startswith('/api/api_fhir_r4/'):
                    return 'fhir'
                return 'unknown'

    def capture_request_data(self, request):
        request_data = {
            'method': request.method,
            'path': request.path,
            'headers': dict(request.headers),
        }
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = request.body.decode('utf-8')
                request_data['body'] = json.loads(body) if body else {}
            except:
                request_data['body'] = str(request.body[:1000])
        return request_data

    def capture_response_data(self, response: HttpResponse):
        response_data = {
            'status_code': response.status_code,
            'content_type': response.get('Content-Type', ''),
        }
        try:
            if hasattr(response, 'content'):
                content = response.content.decode('utf-8')[:10000]
                response_data['content'] = json.loads(content) if 'json' in response_data['content_type'].lower() else content
        except:
            response_data['content'] = 'Unable to decode response'
        return response_data

    def save_log(self, request, response, app_name, route_name, request_data, response_data, duration_ms):
        RequestLog.objects.create(
            app_name=app_name,
            route_name=route_name,
            method=request_data['method'],
            path=request_data['path'],
            status_code=response_data['status_code'],
            duration_ms=duration_ms,
            request_data=request_data,
            response_data=response_data,
            user=str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else None
        )