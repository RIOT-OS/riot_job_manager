from django.conf.urls import url, include
from django.contrib.auth.decorators import login_required

from board_app_creator import views

urlpatterns = [
    url(r'', include('social.apps.django_app.urls', namespace='social')),
    url(r'^board/?$', views.BoardList.as_view(), name='board-list'),
    url(r'^board/create/?$', views.BoardCreate.as_view(), name='board-create'),
    url(r'^board/(?P<pk>\d+)/?$', views.BoardDetail.as_view(), name='board-detail'),
    url(r'^board/(?P<pk>\d+)/delete/?$', views.BoardDelete.as_view(), name='board-delete'),
    url(r'^board/(?P<pk>\d+)/update/?$', views.BoardUpdate.as_view(), name='board-update'),
    url(r'^repository/?$', views.RepositoryList.as_view(), name='repository-list'),
    url(r'^repository/create/?$', views.RepositoryCreate.as_view(), name='repository-create'),
    url(r'^repository/(?P<pk>\d+)/?$', views.RepositoryDetail.as_view(), name='repository-detail'),
    url(r'^repository/(?P<pk>\d+)/delete/?$', views.RepositoryDelete.as_view(), name='repository-delete'),
    url(r'^repository/(?P<pk>\d+)/update/?$', views.RepositoryUpdate.as_view(), name='repository-update'),
]
