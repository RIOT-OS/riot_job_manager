from os.path import dirname
from django import forms
from django.conf import settings

from board_app_creator import models

class TreeSelectMultipleForm(forms.Form):
    trees = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                      required=False)

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices')
        super(TreeSelectMultipleForm, self).__init__(*args, **kwargs)
        self.fields['trees'].choices = choices

class ApplicationForm(forms.ModelForm):
    class Meta():
        model = models.Application
        widgets = {"blacklisted_boards": forms.CheckboxSelectMultiple,
                   "whitelisted_boards": forms.CheckboxSelectMultiple,
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
    class Meta():
        model = models.Board
        widgets = {"prototype_jobs": forms.CheckboxSelectMultiple}

    def __init__(self, *args, **kwargs):
        board = kwargs.get('instance')
        super(BoardForm, self).__init__(*args, **kwargs)
        self.fields['prototype_jobs'].choices = models.ApplicationJob.objects.\
            filter(board__riot_name__in=settings.RIOT_DEFAULT_BOARDS + [
                board.riot_name if board else None]
            ).values_list('pk', 'name')
