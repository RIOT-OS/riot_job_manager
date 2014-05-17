from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'riot_job_manager.views.home', name='home'),
    url(r'^jobs/', include('board_app_creator.urls')),
)
