from os.path import dirname
from django import forms
from django.core.exceptions import ValidationError
from django.conf import settings

from board_app_creator import models

import vcs

class TreeSelectMultipleForm(forms.Form):
    trees = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                      required=False)

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices')
        super(TreeSelectMultipleForm, self).__init__(*args, **kwargs)
        self.fields['trees'].choices = choices

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = models.Application
        widgets = {"blacklisted_boards": forms.CheckboxSelectMultiple,
                   "whitelisted_boards": forms.CheckboxSelectMultiple,
                   "repository": forms.CheckboxSelectMultiple,
                   "prototype_jobs": forms.CheckboxSelectMultiple}

    def __init__(self, *args, **kwargs):
        application = kwargs.get('instance')
        super(ApplicationForm, self).__init__(*args, **kwargs)
        self.fields['prototype_jobs'].choices = models.ApplicationJob.objects.\
            filter(application__name__in=settings.RIOT_DEFAULT_APPLICATIONS + [
                application.name if application else None]
            ).values_list('pk', 'name')

    def save(self, *args, **kwargs):
        if kwargs.get('commit', True):
            super(ApplicationForm, self).save(commit=False)
            repository = self.cleaned_data.pop('repository', None)
            app = super(ApplicationForm, self).save(*args, **kwargs)
            if repository:
                tree_name = dirname(self.cleaned_data['path'])
                models.ApplicationTree.objects.get_or_create(repo=repository,
                                                             tree_name=tree_name,
                                                             application=app)
        else:
            app = super(ApplicationForm, self).save(*args, **kwargs)
        return app

class BoardForm(forms.ModelForm):
    class Meta:
        model = models.Board
        widgets = {"prototype_jobs": forms.CheckboxSelectMultiple}

    def __init__(self, *args, **kwargs):
        board = kwargs.get('instance')
        super(BoardForm, self).__init__(*args, **kwargs)
        self.fields['prototype_jobs'].choices = models.ApplicationJob.objects.\
            filter(board__riot_name__in=settings.RIOT_DEFAULT_BOARDS + [
                board.riot_name if board else None]
            ).values_list('pk', 'name')

class JobFromPrototypeForm(forms.ModelForm):
    prototype_job = forms.ModelChoiceField(queryset=models.ApplicationJob.objects.all())
    next_application = forms.CharField(widget=forms.HiddenInput())
    next_board = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = models.ApplicationJob
        widgets = {'board': forms.HiddenInput(),
                   'application': forms.HiddenInput()}
        exclude = ['upstream_job', 'namespace']

class RepositoryForm(forms.ModelForm):
    class Meta:
        model = models.Repository

    def clean_is_default(self):
        is_default = self.cleaned_data.get('is_default')
        if is_default:
            qs = models.Repository.objects.filter(is_default=True)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    "A default repository already exists ({}).".format(qs.first()))
        return is_default

    def precheckout_repo(self):
        if not hasattr(self, '_repo'):
            repo_url = self.cleaned_data['url']
            repo_path = self.cleaned_data['path']
            repo_type = self.cleaned_data['vcs']

            self._repo = vcs.get_repository(repo_path, repo_type, repo_url)
        return self._repo

    def clean_boards_tree(self):
        boards_tree = self.cleaned_data.get('boards_tree')
        if boards_tree == '.' or not self.cleaned_data.get('has_boards_tree', True):
            return boards_tree
        try:
            repo = self.precheckout_repo()
        except KeyError:
            return board_tree
        try:
            tree = repo.head.base_tree.get_file(boards_tree)
            if isinstance(tree, vcs.Tree):
                raise ValidationError("{} is not a tree.".format(boards_tree))
        except ValueError, e:
            raise ValidationError(e)
        return boards_tree

    def clean_cpu_tree(self):
        cpu_tree = self.cleaned_data.get('cpu_tree')
        if cpu_tree == '.' or not self.cleaned_data.get('has_cpu_tree', True):
            return cpu_tree
        try:
            repo = self.precheckout_repo()
        except KeyError:
            return cpu_tree
        try:
            tree = repo.head.base_tree.get_file(cpu_tree)
            if isinstance(tree, vcs.Tree):
                raise ValidationError("{} is not a tree.".format(cpu_tree))
        except ValueError, e:
            raise ValidationError(e)
        return cpu_tree
