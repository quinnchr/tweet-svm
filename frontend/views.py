from django.http import HttpResponse
from django.template import RequestContext, Context, loader
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.shortcuts import redirect
from frontend.models import ApiUser, Source, Stream

@login_required
def index(request):
	current_user = ApiUser.objects.get(pk=request.user.id)
	streams = Stream.objects.filter(user=current_user)
	return render_to_response("main/index.html", {'authenticated': True, 'user': current_user, 'streams': streams}, context_instance=RequestContext(request))

def login(request):
	if request.POST:
		username = request.POST['username']
		password = request.POST['password']
		user = auth.authenticate(username=username, password=password)
		if user is not None:
			if user.is_active:
				auth.login(request, user)
				return redirect('/')
			else:
				return redirect('/login?error=inactive')
		else:
			return redirect('/login?error=login')
	else:
		error = False
		if 'error' in request.GET:
			alert = request.GET['error']
			if alert == 'login':
				error = 'Incorrect username or password.'
			if alert == 'inactive':
				error = 'User is no longer active.'
			if alert == 'logout':
				error = 'You have been logged out.'
		return render_to_response("main/login.html", {'error': error}, context_instance=RequestContext(request))

@login_required
def logout(request):
	auth.logout(request)
	return redirect('/login?error=logout')

def api(request):
	return render_to_response("main/api.html", {}, context_instance=RequestContext(request))

@login_required
def stream(request):
	return render_to_response("main/stream.html", {'authenticated': True}, context_instance=RequestContext(request))
