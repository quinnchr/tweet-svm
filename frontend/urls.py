from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
	url(r'^$', 'frontend.views.index'),
	url(r'^api/', 'frontend.views.api'),
	url(r'^stream/$', 'frontend.views.stream'),
	url(r'^stream/(?P<stream>\w+)/$', 'frontend.views.stream'),
	url(r'^stream/(?P<stream>\w+)/(?P<source>\w+)/$', 'frontend.views.stream'),
	url(r'^login', 'frontend.views.login'),
	url(r'^logout', 'frontend.views.logout'),
	url(r'^admin/', include(admin.site.urls))
)
