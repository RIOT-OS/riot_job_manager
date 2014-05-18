from django.core.urlresolvers import reverse_lazy
from django.forms import CheckboxSelectMultiple
from django.forms.models import modelform_factory
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views.generic import View, DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from board_app_creator import models

class BoardDetail(DetailView):
    model = models.Board

class BoardList(ListView):
    model = models.Board

class BoardCreate(CreateView):
    model = models.Board
    success_url = reverse_lazy('board-list')
    form_class =  modelform_factory(models.Board,
                    widgets={"prototype_jobs": CheckboxSelectMultiple })

    def get(self, *args, **kwargs):
        models.USBDevice.objects.update_from_system()
        return super(BoardCreate, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        models.USBDevice.objects.update_from_system()
        return super(BoardCreate, self).post(*args, **kwargs)

class BoardDelete(DeleteView):
    model = models.Board
    success_url = reverse_lazy('board-list')

class BoardUpdate(UpdateView):
    model = models.Board
    success_url = reverse_lazy('board-list')
    form_class =  modelform_factory(models.Board,
                    widgets={"prototype_jobs": CheckboxSelectMultiple })

    def get(self, *args, **kwargs):
        models.USBDevice.objects.update_from_system()
        return super(BoardUpdate, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        models.USBDevice.objects.update_from_system()
        return super(BoardUpdate, self).post(*args, **kwargs)

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
