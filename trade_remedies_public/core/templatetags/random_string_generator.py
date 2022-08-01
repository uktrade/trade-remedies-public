import random

from core.templatetags import register
import string
"""
Template tag to generate a random string of X characters
Usage:
    {% random_string_generator 4 %}
"""


@register.simple_tag
def random_string_generator(number_of_characters):
    return ''.join(random.choice(string.ascii_letters) for _ in range(number_of_characters))
