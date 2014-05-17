from django.conf.urls import url, include
from django.contrib.auth.decorators import login_required

from board_app_creator import views

urlpatterns = [
    url(r'', include('social.apps.django_app.urls', namespace='social')),
    url(r'^repository/?$', views.RepositoryList.as_view(), name='repository-list'),
    url(r'^repository/create/?$', views.RepositoryCreate.as_view(), name='repository-create'),
    url(r'^repository/(?P<pk>\d+)/?$', views.RepositoryDetail.as_view(), name='repository-detail'),
    url(r'^repository/(?P<pk>\d+)/delete/?$', views.RepositoryDelete.as_view(), name='repository-delete'),
    url(r'^repository/(?P<pk>\d+)/update/?$', views.RepositoryUpdate.as_view(), name='repository-update'),
]
