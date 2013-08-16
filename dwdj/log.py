import logging

from django.conf import settings as s


class RequireDebugFalse(logging.Filter):
    def filter(self, record):
        return not s.DEBUG
