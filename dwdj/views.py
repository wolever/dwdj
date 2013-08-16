import urlparse

from django.http import HttpResponseRedirect

def guess_next(request, default=None):
    if "next" in request.GET:
        return request.GET["next"]
    if default is None:
        default = request.META.get("HTTP_REFERER")
    if not default:
        return "/"
    parsed = urlparse.urlsplit(default)
    next = urlparse.urlunsplit(('', '') + parsed[2:])
    return next

def redirect_next(request, default=None):
    next = guess_next(request, default)
    if not next.startswith("/"):
        next = "/" + next
    return HttpResponseRedirect(next)

