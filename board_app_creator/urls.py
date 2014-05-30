from django.conf.urls import url, include
from django.contrib.auth.decorators import login_required

from board_app_creator import models, views

urlpatterns = [
    url(r'^social_auth/', include('social.apps.django_app.urls', namespace='social')),
    url(r'^logout/', 'django.contrib.auth.views.logout', {'template_name': 'board_app_creator/logout.html'}, name='logout'),
    url(r'^application/?$', views.ApplicationList.as_view(queryset=models.Application.objects.all_real()), name='application-list'),
    url(r'^application/create/?$', login_required(views.ApplicationCreate.as_view()), name='application-create'),
    url(r'^application/hidden/?$', views.ApplicationList.as_view(), name='application-hidden'),
    url(r'^application/(?P<pk>\d+)/?$', views.ApplicationDetail.as_view(), name='application-detail'),
    url(r'^application/(?P<pk>\d+)/delete/?$', login_required(views.ApplicationDelete.as_view()), name='application-delete'),
    url(r'^application/(?P<pk>\d+)/ignore/?$', login_required(views.application_toggle_no_application), name='application-ignore'),
    url(r'^application/(?P<pk>\d+)/renew/?$', login_required(views.application_update_from_makefile), name='application-renew'),
    url(r'^application/(?P<pk>\d+)/update/?$', login_required(views.ApplicationUpdate.as_view()), name='application-update'),
    url(r'^board/?$', views.BoardList.as_view(queryset=models.Board.objects.all_real()), name='board-list'),
    url(r'^board/create/?$', login_required(views.BoardCreate.as_view()), name='board-create'),
    url(r'^board/hidden/?$', views.BoardList.as_view(), name='board-hidden'),
    url(r'^board/(?P<pk>\d+)/?$', views.BoardDetail.as_view(), name='board-detail'),
    url(r'^board/(?P<pk>\d+)/delete/?$', login_required(views.BoardDelete.as_view()), name='board-delete'),
    url(r'^board/(?P<pk>\d+)/ignore/?$', login_required(views.board_toggle_no_board), name='board-ignore'),
    url(r'^board/(?P<pk>\d+)/update/?$', login_required(views.BoardUpdate.as_view()), name='board-update'),
    url(r'^job/?$', views.JobList.as_view(queryset=models.Job.objects.select_subclasses()), name='job-list'),
    url(r'^job/create/?$', login_required(views.JobCreate.as_view()), name='job-create'),
    url(r'^job/renew/?$', login_required(views.job_update_all), name='job-renew-all'),
    url(r'^job/(?P<pk>\d+)/?$', views.JobDetail.as_view(), name='job-detail'),
    url(r'^job/(?P<pk>\d+)/delete/?$', login_required(views.JobDelete.as_view()), name='job-delete'),
    url(r'^job/(?P<pk>\d+)/renew/?$', login_required(views.job_update), name='job-renew'),
    url(r'^job/(?P<pk>\d+)/update/?$', login_required(views.JobUpdate.as_view()), name='job-update'),
    url(r'^job/(?P<pk>\d+)/update_board_app/?$', login_required(views.ApplicationJobUpdate.as_view()), name='job-update-board-app'),
    url(r'^repository/?$', views.RepositoryList.as_view(), name='repository-list'),
    url(r'^repository/create/?$', login_required(views.RepositoryCreate.as_view()), name='repository-create'),
    url(r'^repository/(?P<pk>\d+)/?$', views.RepositoryDetail.as_view(), name='repository-detail'),
    url(r'^repository/(?P<pk>\d+)/add_application_trees/$', login_required(views.RepositoryAddApplicationTrees.as_view()), name='repository-add-application-trees'),
    url(r'^repository/(?P<pk>\d+)/delete/?$', login_required(views.RepositoryDelete.as_view()), name='repository-delete'),
    url(r'^repository/(?P<pk>\d+)/renew/?$', login_required(views.repository_update_applications_and_boards), name='repository-renew'),
    url(r'^repository/(?P<pk>\d+)/update/?$', login_required(views.RepositoryUpdate.as_view()), name='repository-update'),
]
