from django.http import HttpResponse
from django.template import RequestContext, Context, loader
from django.shortcuts import render_to_response

def index(request):
    return render_to_response("main/index.html", {}, context_instance=RequestContext(request))

def test(request):
    return render_to_response("main/test.html", {}, context_instance=RequestContext(request))
