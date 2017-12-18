""" Widgets for django-markdown. """
import json
import os

from django import forms
from django.contrib.admin.widgets import AdminTextareaWidget
from django.urls import reverse
from django.template import Context
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe


def editor_js_initialization(selector):
    ctx = Context(dict(
        selector=selector,
        extra_settings=json.dumps({'previewParserPath': reverse('shark:django_markdown_preview')})),
        autoescape=False)
    return render_to_string('django_markdown/editor_init.html', ctx)


class MarkdownWidget(forms.Textarea):

    """ Widget for a textarea.
    Takes two additional optional keyword arguments:
    ``markdown_set_name``
        Name for current set. Default: value of MARKDOWN_SET_NAME setting.
    ``markdown_skin``
        Name for current skin. Default: value of MARKDOWN_EDITOR_SKIN setting.
    """

    def __init__(self, attrs=None):
        super(MarkdownWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        """ Render widget.
        :returns: A rendered HTML
        """
        html = super(MarkdownWidget, self).render(name, value, attrs)
        attrs = self.build_attrs(attrs)
        html += editor_js_initialization("#%s" % attrs['id'])
        return mark_safe(html)

    class Media:
        css = {
            'screen': (
                os.path.join('django_markdown', 'skins', 'simple', 'style.css'),
                os.path.join('django_markdown/sets', 'markdown', 'style.css')
            )
        }

        js = (
            os.path.join('django_markdown', 'jquery.init.js'),
            os.path.join('django_markdown', 'jquery.markitup.js'),
            os.path.join('django_markdown/sets', 'markdown', 'set.js')
        )


class AdminMarkdownWidget(MarkdownWidget, AdminTextareaWidget):

    """ Support markdown widget in Django Admin. """

    pass
