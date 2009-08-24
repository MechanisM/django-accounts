from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseNotAllowed
from django.core.urlresolvers import reverse

def render(request, template, data={}):
    return render_to_response(
        template,
        data,
        context_instance=RequestContext(request)
    )    

def redirect(fn):
    return HttpResponseRedirect(
        reverse(fn)
    )

def requires_post():
    return HttpResponseNotAllowed(['POST'])
