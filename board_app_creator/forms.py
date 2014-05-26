from os.path import dirname
from django import forms

from board_app_creator import models

class TreeSelectMultipleForm(forms.Form):
    trees = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices')
        super(TreeSelectMultipleForm, self).__init__(*args, **kwargs)
        self.fields['trees'].choices = choices

class ApplicationForm(forms.ModelForm):
    class Meta():
        model = models.Application
        widgets = {"blacklisted_boards": forms.CheckboxSelectMultiple,
                   "whitelisted_boards": forms.CheckboxSelectMultiple}
    
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
