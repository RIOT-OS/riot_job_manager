from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views.generic import View, DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from board_app_creator import models

class RepositoryDetail(DetailView):
    model = models.Repository

class RepositoryList(ListView):
    model = models.Repository

class RepositoryCreate(CreateView):
    model = models.Repository
    success_url = reverse_lazy('repository-list')

class RepositoryDelete(DeleteView):
    model = models.Repository
    success_url = reverse_lazy('repository-list')

class RepositoryUpdate(UpdateView):
    model = models.Repository
    success_url = reverse_lazy('repository-list')

# Create your views here.
