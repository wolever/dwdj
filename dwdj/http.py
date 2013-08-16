import re
import os
import stat
import mimetypes

from django.utils.http import http_date
from django.views.static import was_modified_since
from django.http import CompatibleStreamingHttpResponse, HttpResponseNotModified

def escape_header(header_value):
    """ Escapes an HTTP header (ex, a ``Content-Disposition``).
        Kind of blunt and probably not 100% correct... But should be safe. """
    return re.sub("\t\n\r;", "", header_value)

def file_response(request, fullpath, download=None, download_name=None):
    statobj = os.stat(fullpath)
    mimetype, encoding = mimetypes.guess_type(fullpath)
    mimetype = mimetype or 'application/octet-stream'
    if not was_modified_since(request.META.get('HTTP_IF_MODIFIED_SINCE'),
                              statobj.st_mtime, statobj.st_size):
        return HttpResponseNotModified()
    response = CompatibleStreamingHttpResponse(open(fullpath, 'rb'), content_type=mimetype)
    response["Last-Modified"] = http_date(statobj.st_mtime)
    if stat.S_ISREG(statobj.st_mode):
        response["Content-Length"] = statobj.st_size
    if encoding:
        response["Content-Encoding"] = encoding

    if download or download is None and download_name:
        response["Content-Disposition"] = "attachment; filename=%s" %(
            escape_header(download_name),
        )
    return response


