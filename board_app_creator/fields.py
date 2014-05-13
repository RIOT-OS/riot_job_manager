"""
Fields for board_app_creator app.
"""
import re
from django import forms
from django.db import models

class SmallHexFormField(forms.IntegerField):
    """
    FormField for SmallHex (0 <= SmallHex <= 65536).
    """
    default_error_messages = {
        'invalid': 'Enter a valid short value: e.g. "ff22"'
    }

    def __init__(self, *args, **kwargs):
        super(SmallHexFormField, self).__init__(*args, **kwargs)

    def clean(self, value):
        if value == '' and not self.required:
            return u''

        if not re.match('^[A-Fa-f0-9]{1,4}$', value):
            raise forms.ValidationError(self.error_messages['invalid'])

        value = int(value, 16)

        if not 0 <= value <= 65536:
            raise forms.ValidationError(self.error_messages['invalid'])


        super(SmallHexFormField, self).clean(value)

        return value

# pylint: disable=R0904
class SmallHexField(models.PositiveSmallIntegerField):
    """
    Model field for SmallHex (0 <= SmallHex <= 65536).
    """
    description = "Hex value for a small integer"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 4
        super(SmallHexField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        super(SmallHexField, self).to_python(value)

        try:
            string = hex(value)[2:]

            return string.lower()
        except TypeError:
            return None

    def get_prep_value(self, value):
        try:
            # hex to int, save the int representation of hex code to the
            # database
            return value
        except ValueError:
            return None

    def formfield(self, *args, **kwargs):
        kwargs['form_class'] = SmallHexFormField

        return super(SmallHexField, self).formfield(*args, **kwargs)
