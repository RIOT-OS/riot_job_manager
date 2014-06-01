import re
from os.path import join as path_join
from urllib import urlencode

from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.forms import RadioSelect
from django.forms.models import modelform_factory
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render
from django.views.generic import View, DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from board_app_creator import forms, models
import vcs

def index(request):
    if not models.Repository.objects.exists():
        return HttpResponseRedirect(reverse_lazy('repository-create'))
    elif not models.Job.objects.exists():
        return HttpResponseRedirect(reverse_lazy('job-create'))
    else:
        return HttpResponseRedirect(reverse_lazy('job-list'))

class ApplicationDetail(DetailView):
    model = models.Application

class ApplicationList(ListView):
    model = models.Application
    paginate_by = settings.RIOT_DEFAULT_PAGINATION

    def get_context_data(self, **kwargs):
        context = super(ApplicationList, self).get_context_data(**kwargs)
        context['hidden_shown'] = any(b.no_application for b in context['application_list'])
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
    paginate_by = settings.RIOT_DEFAULT_PAGINATION

    def get_context_data(self, **kwargs):
        context = super(BoardList, self).get_context_data(**kwargs)
        context['hidden_shown'] = any(b.no_board for b in context['board_list'])
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

def _get_next_application_job_params(prev_app_name, prev_board_name):
    next_applications = models.Application.objects.filter(name__gt=prev_app_name)
    next_boards = models.Board.objects.filter(riot_name__gt=prev_board_name)

    while next_applications.exists() and \
        not models.ApplicationJob.objects.exclude(board__riot_name=prev_board_name,
                                                  application=next_applications.first(),
                                                  update_behavior__gt=0):
        next_applications = models.Application.objects.filter(name__gt=next_applications.first().name)

    if next_applications.exists():
        return next_applications.first().name, prev_board_name
    while next_boards.exists() and \
        not models.ApplicationJob.objects.exclude(board=next_boards.first(),
                                                  application__name=prev_app_name,
                                                  update_behavior__gt=0):
        next_boards = models.Board.objects.filter(riot_name__gt=next_boards.first().name)

    if next_boards.exists():
        return prev_app_name, next_boards.first().riot_name
    return None, None

class JobCreate(CreateView):
    form_class = modelform_factory(models.Job, widgets={
        'update_behavior': RadioSelect})
    model = models.Job
    success_url = reverse_lazy('job-list')
    template_name = 'board_app_creator/job_form.html'

    def get_context_data(self, **kwargs):
        context = super(JobCreate, self).get_context_data(**kwargs)
        context['form_verb'] = "Add"
        return context

class JobDelete(DeleteView):
    model = models.Job
    success_url = reverse_lazy('job-list')
    template_name = 'board_app_creator/job_confirm_delete.html'

class JobDetail(DetailView):
    model = models.Job
    template_name = 'board_app_creator/job_detail.html'

    def get_object(self, queryset=None):
        return super(JobDetail, self).get_object(queryset).get_subclass()

class JobList(ListView):
    model = models.Job
    paginate_by = settings.RIOT_DEFAULT_PAGINATION

    def get_context_data(self, **kwargs):
        context = super(JobList, self).get_context_data(**kwargs)
        board = models.Board.objects.first()
        application = models.Application.objects.first()

        next_application, next_board = _get_next_application_job_params(
            application.name, board.riot_name)

        if next_application and next_board:
            params = '?'+urlencode({'next_application': next_application,
                                    'next_board': next_board})
        else:
            params = ''

        context['create_url'] = reverse_lazy('job-update-from-board-app',
                                        kwargs={
                                            'board': board,
                                            'application': application
                                        })+params
        return context

class JobUpdate(UpdateView):
    form_class = modelform_factory(models.Job, widgets={
        'update_behavior': RadioSelect})
    model = models.Job
    success_url = reverse_lazy('job-list')
    template_name = 'board_app_creator/job_form.html'

    def get_context_data(self, **kwargs):
        context = super(JobUpdate, self).get_context_data(**kwargs)
        context['form_verb'] = "Edit"
        return context

class ApplicationJobCreate(JobCreate):
    form_class = modelform_factory(models.ApplicationJob, widgets={
        'update_behavior': RadioSelect})
    model = models.ApplicationJob

class ApplicationJobUpdate(JobUpdate):
    form_class = modelform_factory(models.ApplicationJob, widgets={
        'update_behavior': RadioSelect})
    model = models.ApplicationJob

    def __init__(self, *args, **kwargs):
        super(ApplicationJobUpdate, self).__init__(*args, **kwargs)

    def get_form_kwargs(self):
        if not hasattr(self.object, 'job_ptr_id'):
            self.object.job_ptr_id = self.object.id
            self.object.id = None
        if not hasattr(self.object, 'board_id'):
            self.object.board_id = None
        if not hasattr(self.object, 'application_id'):
            self.object.application_id = None
        kwargs = super(ApplicationJobUpdate, self).get_form_kwargs()
        return kwargs

    def get_object(self, queryset=None):
        try:
            obj = super(ApplicationJobUpdate, self).get_object(queryset)
        except Http404:
            self.model = models.Job
            obj = super(ApplicationJobUpdate, self).get_object(queryset)
            self.model = models.ApplicationJob
            obj.__class__ = models.ApplicationJob
        return obj

def job_update_all(request):
    models.Job.create_from_jenkins_xml()
    return HttpResponseRedirect(reverse_lazy('job-list'))

def job_update(request, pk):
    job = get_object_or_404(models.Job, pk=pk).get_subclass()
    job.update_from_jenkins_xml()
    job.save()
    return HttpResponseRedirect(reverse_lazy('job-list'))

def job_update_from_board_app(request, board, application):
    if 'next_application' in request.REQUEST:
        next_application = request.REQUEST['next_application']
    else:
        next_application = application

    if 'next_board' in request.REQUEST:
        next_board = request.REQUEST['next_board']
    else:
        next_board = board

    if next_application == application and next_board == board:
        return HttpResponseRedirect(reverse_lazy('job-list'))
    else:
        next_next_application, next_next_board = _get_next_application_job_params(
            next_application, next_board)

        if next_next_application and next_next_board:
            params = '?'+urlencode({'next_application': next_next_application,
                                    'next_board': next_next_board})
        else:
            params = ''

        return HttpResponseRedirect(reverse_lazy('job-update-from-board-app',
            kwargs={'application': next_application,
                    'board': next_board})+params)

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
    paginate_by = settings.RIOT_DEFAULT_PAGINATION

class RepositoryCreate(CreateView):
    model = models.Repository
    form_class = forms.RepositoryForm

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
    form_class = forms.RepositoryForm
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
