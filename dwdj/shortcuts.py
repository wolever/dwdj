from django.shortcuts import render_to_response
from django.template import RequestContext

def r2r(request, template, dictionary=None, mimetype=None, content_type=None):
    """ A shortcut for 'render_to_response' which uses a RequestContext. """
    if mimetype is not None and content_type is None:
        content_type = mimetype
    context = RequestContext(request)
    return render_to_response(template, dictionary, context_instance=context,
                              content_type=content_type)
