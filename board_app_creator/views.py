import re
from os.path import join as path_join

from django.core.urlresolvers import reverse_lazy
from django.forms import CheckboxSelectMultiple
from django.forms.models import modelform_factory
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views.generic import View, DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from board_app_creator import forms, models
import vcs

class ApplicationDetail(DetailView):
    model = models.Application

class ApplicationList(ListView):
    model = models.Application

    def get_context_data(self, **kwargs):
        context = super(ApplicationList, self).get_context_data(**kwargs)
        context['hidden_shown'] = context['application_list'].filter(no_application=True).exists()
        return context

class ApplicationCreate(CreateView):
    model = models.Application
    success_url = reverse_lazy('application-list')
    form_class = forms.ApplicationForm

    def get_context_data(self, **kwargs):
        context = super(ApplicationCreate, self).get_context_data(**kwargs)
        context['form_verb'] = "Add"
        return context

class ApplicationDelete(DeleteView):
    model = models.Application
    success_url = reverse_lazy('application-list')

class ApplicationUpdate(UpdateView):
    model = models.Application
    success_url = reverse_lazy('application-list')
    form_class = forms.ApplicationForm

    def get_context_data(self, **kwargs):
        context = super(ApplicationUpdate, self).get_context_data(**kwargs)
        context['form_verb'] = "Edit"
        return context

def application_toggle_no_application(request, pk):
    app = get_object_or_404(models.Application, pk=pk)
    app.no_application = not app.no_application
    app.save()

    if app.no_application:
        return HttpResponseRedirect(reverse_lazy('application-list'))
    else:
        return HttpResponseRedirect(reverse_lazy('application-hidden'))

def application_update_from_makefile(request, pk):
    app = get_object_or_404(models.Application, pk=pk)
    app.update_from_makefile()
    return HttpResponseRedirect(reverse_lazy('application-list'))

class BoardDetail(DetailView):
    model = models.Board

class BoardList(ListView):
    model = models.Board

    def get_context_data(self, **kwargs):
        context = super(BoardList, self).get_context_data(**kwargs)
        context['hidden_shown'] = context['board_list'].filter(no_board=True).exists()
        return context

class BoardCreate(CreateView):
    model = models.Board
    success_url = reverse_lazy('board-list')
    form_class = forms.BoardForm

    def get(self, *args, **kwargs):
        models.USBDevice.objects.update_from_system()
        return super(BoardCreate, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        models.USBDevice.objects.update_from_system()
        return super(BoardCreate, self).post(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(BoardCreate, self).get_context_data(**kwargs)
        context['form_verb'] = "Add"
        return context

class BoardDelete(DeleteView):
    model = models.Board
    success_url = reverse_lazy('board-list')

class BoardUpdate(UpdateView):
    model = models.Board
    success_url = reverse_lazy('board-list')
    form_class = forms.BoardForm

    def get(self, *args, **kwargs):
        models.USBDevice.objects.update_from_system()
        return super(BoardUpdate, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        models.USBDevice.objects.update_from_system()
        return super(BoardUpdate, self).post(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(BoardUpdate, self).get_context_data(**kwargs)
        context['form_verb'] = "Edit"
        return context

def board_toggle_no_board(request, pk):
    board = get_object_or_404(models.Board, pk=pk)
    board.no_board = not board.no_board
    board.save()

    if board.no_board:
        return HttpResponseRedirect(reverse_lazy('board-list'))
    else:
        return HttpResponseRedirect(reverse_lazy('board-hidden'))

class RepositoryAddApplicationTrees(View):
    form_class = forms.TreeSelectMultipleForm
    template_name = 'board_app_creator/repository_add_application_trees.html'

    def get(self, request, pk):
        repo = get_object_or_404(models.Repository, pk=pk)

        choices = [(d[0][2:], d[0]) \
            for d in repo.vcs_repo.head.base_tree.walk()]

        preselect = repo.application_trees.values_list('tree_name', flat=True)
        form = self.form_class(initial={'trees': preselect}, choices=choices)

        return render(request, self.template_name, {'form': form, 'repo_tree': repo.vcs_repo.head.base_tree.walk()})

    def post(self, request, pk):
        repo = get_object_or_404(models.Repository, pk=pk)

        choices = [(d[0][2:], d[0]) \
            for d in repo.vcs_repo.head.base_tree.walk()]

        form = self.form_class(request.POST, choices=choices)
        if form.is_valid():
            for tree in form.cleaned_data['trees']:
                for app in repo.vcs_repo.head.get_file(tree).trees:
                    abs_path = path_join(tree, app.name)
                    makefile = path_join(abs_path, 'Makefile')
                    try:
                        app_name, blacklist, whitelist = models.Application.get_name_and_lists_from_makefile(repo, makefile)
                    except models.Application.DoesNotExist:
                        continue
                    except AssertionError:
                        continue
                    appobj = models.Application(name=app_name, path=abs_path)
                    appobj.save()
                    app_tree, created = models.ApplicationTree.objects.get_or_create(
                        tree_name=tree, repo=repo, application=appobj)
                    for board in models.Board.objects.all():
                        if board.riot_name in blacklist and board not in appobj.blacklisted_boards.all():
                            appobj.blacklisted_boards.add(board)
                        if board.riot_name in whitelist and board not in appobj.blacklisted_boards.all():
                            appobj.whitelisted_boards.add(board)
            models.Job.create_from_jenkins_xml()
            return HttpResponseRedirect(reverse_lazy('repository-list'))
        return render(request, self.template_name, {'form': form})

class RepositoryDetail(DetailView):
    model = models.Repository

class RepositoryList(ListView):
    model = models.Repository

class RepositoryCreate(CreateView):
    model = models.Repository

    def get_success_url(self):
        return reverse_lazy('repository-add-application-trees', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super(RepositoryCreate, self).get_context_data(**kwargs)
        context['form_verb'] = "Add"
        return context

class RepositoryDelete(DeleteView):
    model = models.Repository
    success_url = reverse_lazy('repository-list')

class RepositoryUpdate(UpdateView):
    model = models.Repository
    success_url = reverse_lazy('repository-list')

    def get_context_data(self, **kwargs):
        context = super(RepositoryUpdate, self).get_context_data(**kwargs)
        context['form_verb'] = "Edit"
        return context

def repository_update_applications_and_boards(request, pk):
    repo = get_object_or_404(models.Repository, pk=pk)
    repo.update_boards()
    repo.update_applications()
    return HttpResponseRedirect(reverse_lazy('repository-list'))

# Create your views here.
