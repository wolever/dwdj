from django.conf import settings as s

def debug(request):
    return {
        "DEBUG": s.DEBUG,
    }

def request(request):
    return {
        "request": request,
    }
