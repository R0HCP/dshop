from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    try:
        return dictionary.get(key)
    except AttributeError: 
        try:
            return dictionary[key]
        except (KeyError, TypeError):
            return None