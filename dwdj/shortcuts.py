from django.shortcuts import render_to_response
from django.template import RequestContext

def r2r(request, template, dictionary=None, mimetype=None):
    """ A shortcut for 'render_to_response' which uses a RequestContext. """
    context = RequestContext(request)
    return render_to_response(template, dictionary, context_instance=context,
                              mimetype=mimetype)
