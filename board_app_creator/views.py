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

class ApplicationCreate(CreateView):
    model = models.Application
    success_url = reverse_lazy('application-list')
    form_class =  modelform_factory(models.Application,
                    widgets={"blacklisted_boards": CheckboxSelectMultiple,
                             "whitelisted_boards": CheckboxSelectMultiple})


class ApplicationDelete(DeleteView):
    model = models.Application
    success_url = reverse_lazy('application-list')

class ApplicationUpdate(UpdateView):
    model = models.Application
    success_url = reverse_lazy('application-list')
    form_class =  modelform_factory(models.Application,
                    widgets={"blacklisted_boards": CheckboxSelectMultiple,
                             "whitelisted_boards": CheckboxSelectMultiple})

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

class RepositoryAddApplicationTrees(View):
    form_class = forms.TreeSelectMultipleForm
    template_name = 'board_app_creator/repository_add_application_trees.html'

    def get(self, request, pk):
        repo = get_object_or_404(models.Repository, pk=pk)

        choices = [(d[0][2:], d[0]) \
            for d in repo.vcs_repo.head.base_tree.walk()]

        form = self.form_class(choices=choices)

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
                    makefile = path_join(tree, app.name, 'Makefile')
                    try:
                        makefile_blob = repo.vcs_repo.head.get_file(makefile)
                    except KeyError:
                        continue
                    if not isinstance(makefile_blob, vcs.Blob):
                        continue
                    makefile_content = makefile_blob.read()
                    app_name = ''
                    blacklist = []
                    whitelist = []
                    next_line_blacklist = False
                    next_line_whitelist = False
                    for line in makefile_content.splitlines():
                        if next_line_blacklist:
                            blacklist.extend(re.sub(r"\s*(.+)\s*\\?$", r'\1', line).split(' '))
                            if not line.endswith('\\'):
                                next_line_blacklist = False
                        if next_line_whitelist:
                            whitelist.extend(re.sub(r"\s*(.+)\s*\\?$", r'\1', line).split(' '))
                            if not line.endswith('\\'):
                                next_line_whitelist = False
                        if re.match(r".*PROJECT\s*[:?]?=\s*([^\s]+).*", line):
                            app_name = re.sub(r".*PROJECT\s*=\s*([^\s]+).*", r'\1', line)
                        if re.match(r".*BOARD_BLACKLIST\s*[:?]?=\s*([^\\]+)\s*\\?$", line):
                            blacklist.extend(re.sub(r".*BOARD_BLACKLIST\s*[:?]?=\s*([^\\]+)\s*\\?$", r'\1', line).split(' '))
                            if line.endswith('\\'):
                                blacklist.pop(-1)
                                next_line_blacklist = True
                        if re.match(r".*BOARD_WHITELIST\s*[:?]?=\s*([^\\]+)\s*\\?$", line):
                            whitelist.extend(re.sub(r".*BOARD_WHITELIST\s*[:?]?=\s*([^\\]+)\s*\\?$", r'\1', line).split(' '))
                            if line.endswith('\\'):
                                whitelist.pop(-1)
                                next_line_whitelist = True
                    if app_name == '':
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
            return HttpResponseRedirect(reverse_lazy('repository-list'))
        return render(request, self.template_name, form)

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
