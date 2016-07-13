import re
import os
import mimetypes
from cStringIO import StringIO

from django.utils.http import http_date
from django.views.static import was_modified_since
from django.http import HttpResponseNotModified
try:
    from django.http import CompatibleStreamingHttpResponse as StreamingHttpResponse
except ImportError:
    from django.http import StreamingHttpResponse

def escape_header(header_value):
    """ Escapes an HTTP header (ex, a ``Content-Disposition``).
        Kind of blunt and probably not 100% correct... But should be safe. """
    return re.sub(" *[\t\n\r;,]+ *", " ", header_value)


def data_response(data, size=None,
                  attachment=False, attachment_name=None,
                  mimetype=None, encoding=None):
    if hasattr(data, "getvalue"):
        data = data.getvalue()
    if isinstance(data, unicode):
        data = data.encode("utf-8")
        encoding = "utf-8"
    if isinstance(data, str):
        size = len(data)
        data = StringIO(data)
    mimetype = mimetype or 'application/octet-stream'
    response = StreamingHttpResponse(data, content_type=mimetype)
    if size is not None:
        response["Content-Length"] = size
    if encoding:
        response["Content-Encoding"] = encoding
    if attachment or attachment_name:
        response["Content-Disposition"] = "attachment" + (
            attachment_name and
            "; filename=%s" %(escape_header(attachment_name), ) or ""
        )
    return response


def file_response(request, filepath,
                  attachment=False, attachment_name=None,
                  mimetype=None, encoding=None):
    statobj = os.stat(filepath)
    if not was_modified_since(request.META.get('HTTP_IF_MODIFIED_SINCE'),
                              statobj.st_mtime, statobj.st_size):
        return HttpResponseNotModified()

    if mimetype is None:
        mimetype, encoding = mimetypes.guess_type(filepath)
    response = data_response(
        open(filepath, 'rb'), size=statobj.st_size,
        mimetype=mimetype, encoding=encoding,
    )
    response["Last-Modified"] = http_date(statobj.st_mtime)
    return response
