import logging
from datetime import datetime

from django.core import urlresolvers
from django.conf import settings as s
from django.http import Http404, HttpResponsePermanentRedirect


class ActualHTTPMethodMiddleware(object):
    """ Allow an 'actual_method' GET paramter to modify the HTTP request
        parameter (for JavaScript and friends which don't really support
        PUT/DELETE). """

    def process_request(self, request):
        _old_mutable = request.GET._mutable
        request.GET._mutable = True
        try:
            actual_method = request.GET.pop("__actual_method", None)
            if actual_method is not None:
                request.method = actual_method[0].upper()
        finally:
            request.GET._mutable = _old_mutable


class SetRemoteAddrFromForwardedFor(object):
    """ Sets ``request.META["REMOTE_ADDR"]`` based on the value of the
        ``X-Forwarded-For`` header. """

    def process_request(self, request):
        try:
            http_x_forwarded_for = request.META["HTTP_X_FORWARDED_FOR"]
        except KeyError:
            return
        # If the x-forwarded-for header exists when Apache gets the request,
        # it will stick its address onto the end:
        #     X-Forwarded-For: user-supplied-value, actual-user-address
        # Only grab the last address, which will be the one added by Apache.
        remote_addr = http_x_forwarded_for.rsplit(",", 1)[-1].strip()
        request.META["REMOTE_ADDR"] = remote_addr


class AccessLogMiddleware(object):
    """ Log Apache-style access logs using Python's logging module. """

    access_log = logging.getLogger("accesslog.access")
    error_log = logging.getLogger("accesslog.error")

    def __init__(self):
        logging.getLogger("django.request").setLevel(logging.CRITICAL)

    def format_log(self, request, status_code, body_bytes):
        env = request.META
        user = getattr(request, "user", None)
        username = user and user.username or "-"
        su_state = getattr(request, "su_state", None)
        if su_state is not None and su_state.old_user is not None:
            username = '"%s acting-as %s"' %(
                su_state.old_user.username, username,
            )
        return ('%s %s %s [%s] "%s %s %s" %s %s' %(
            env.get("REMOTE_ADDR"),
            hex(id(request))[-6:],
            username,
            datetime.utcnow().strftime("%d/%b/%Y:%H:%M:%S -0000"),
            env.get("REQUEST_METHOD"),
            env.get("PATH_INFO"),
            env.get("SERVER_PROTOCOL"),
            status_code,
            body_bytes or "-",
        )).encode("utf-8")

    def process_response(self, request, response):
        body_bytes_func = getattr(response.content, "__len__", None)
        if body_bytes_func is not None:
            body_bytes = body_bytes_func()
        else:
            body_bytes = 0
        status = response.status_code
        formatted = self.format_log(request, status, body_bytes)
        if status < 500:
            self.access_log.info(formatted)
        else:
            self.access_log.warning(formatted)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, Http404):
            # Note: this will be caught by Django and handled by
            # process_response.
            return
        self.error_log.exception(self.format_log(request, 500, 0))


class RemoveTrailingSlashMiddleware(object):
    """ The opposite of Django's ``APPEND_SLASH``, removes a trailing slash
        from URLs when appropriate. """

    def process_request(self, request):
        old_path = request.path
        if not old_path.endswith("/") or old_path == "/":
            return

        urlconf = getattr(request, "urlconf", None)

        if urlresolvers.is_valid_path(request.path_info, urlconf):
            return

        if not urlresolvers.is_valid_path(request.path_info.rstrip("/"), urlconf):
            return

        new_path = request.path.rstrip("/")

        if s.DEBUG and request.method == 'POST':
            raise RuntimeError((
                "You called this URL via POST, but the URL should not end "
                "in a slash and RemoveTrailingSlashMiddleware is active. "
                "I can't redirect to the slash URL while maintaining POST data. "
                "Change your form to point to %s (no trailing slash)."
            ) %(new_path, ))

        query = request.environ.get("QUERY_STRING")
        if query:
            new_path += "?" + query
        return HttpResponsePermanentRedirect(new_path)
