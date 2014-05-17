from django.conf.urls import url, include
from django.contrib.auth.decorators import login_required

from board_app_creator import views

urlpatterns = [
    url(r'', include('social.apps.django_app.urls', namespace='social')),
]
