from django import forms

class TreeSelectMultipleForm(forms.Form):
    trees = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices')
        super(TreeSelectMultipleForm, self).__init__(*args, **kwargs)
        self.fields['trees'].choices = choices
