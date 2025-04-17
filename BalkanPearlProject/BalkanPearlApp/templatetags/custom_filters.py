from django import template

register = template.Library()

@register.filter(name='replace')
def replace(value, arg):
    """
    Заменяет подстроку в строке.
    Аргумент должен иметь вид "old=>new".
    Например, чтобы заменить запятую на точку, передайте ",=>.".
    """
    try:
        old, new = arg.split("=>")
    except ValueError:
        return value
    return str(value).replace(old, new)
    