from django import template

register = template.Library()

@register.filter
def update_behavior_letter(value):
    letter = ['A', 'U', 'M']
    try:
        return letter[value]
    except Exception:
        return ''
