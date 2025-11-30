import time
from .models import TrafficLog
from django.utils.deprecation import MiddlewareMixin

class TrafficLoggingMiddleware(MiddlewareMixin):
    """
    Logs basic request/response data to TrafficLog.
    Add to MIDDLEWARE after any auth middleware so request.user is available if needed.
    """

    def process_request(self, request):
        request._start_time = time.perf_counter()

    def process_response(self, request, response):
        try:
            start = getattr(request, "_start_time", None)
            elapsed_ms = (time.perf_counter() - start) * 1000 if start else None

            # get client IP (behind proxy, read X-Forwarded-For first)
            xff = request.META.get("HTTP_X_FORWARDED_FOR")
            if xff:
                ip = xff.split(",")[0].strip()
            else:
                ip = request.META.get("REMOTE_ADDR")

            path = request.get_full_path()[:512]
            user_agent = request.META.get("HTTP_USER_AGENT", "")[:1000]
            referer = request.META.get("HTTP_REFERER", "")[:1024]
            content_length = response.get("Content-Length")
            try:
                content_length = int(content_length) if content_length is not None else None
            except:
                content_length = None

            TrafficLog.objects.create(
                ip=ip,
                path=path,
                method=request.method,
                status_code=getattr(response, "status_code", None),
                response_time_ms=elapsed_ms,
                user_agent=user_agent,
                referer=referer,
                content_length=content_length,
                is_ajax=request.headers.get("X-Requested-With") == "XMLHttpRequest"
            )
        except Exception:
            # never break the request on logging failure
            pass

        return response
