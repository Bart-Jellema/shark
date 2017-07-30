import json

from shark.base import Object, Objects, objectify
from shark.resources import Resources


class Renderer:
    object_number = 0

    def __init__(self, handler=None, inline_style_class_base='style_'):
        self.__class__.object_number += 1
        self.id = self.__class__.__name__ + '_' + str(self.__class__.object_number)
        self._html = []
        self._rendering_to = self._html
        self._css = []
        self._css_classes = {}
        self._js = []
        self._rendering_js_to = self._js
        self.indent = 0
        self.handler = handler
        self.translate_inline_styles_to_classes = True
        self.inline_style_class_base = inline_style_class_base
        self.resources = Resources()
        self.parent_tree = []
        self.variables = {}

        if handler:
            self.text = handler.text
        else:
            self.text = ''

        self.separator = '\r\n'
        self.omit_next_indent = False

        self.render_count = 0

    def add_css_class(self, css):
        if not css in self._css_classes:
            self._css_classes[css] = '{}{}_{}'.format(self.inline_style_class_base, self.object_number, len(self._css_classes))
        return self._css_classes[css]

    def append(self, p_object):
        if isinstance(p_object, str):
            self._rendering_to.append((' '*self.indent if not self.omit_next_indent else '') + p_object + self.separator)
            self.omit_next_indent = False

    def append_css(self, css):
        self._css.append(css.strip())

    def append_js(self, js):
        js = js.strip()
        if not js.endswith(';'):
            js += ';'
        self._rendering_js_to.append(js)

    def add_variable(self, web_object):
        name = self.id.lower() + '_' + str(len(self.variables) + 1)
        self.variables[name] = objectify(web_object)
        return name

    def render_variables(self, variables):
        while variables:
            name, obj = variables.popitem()
            html, js = self.render_string_and_js(obj)
            self.append_js('var {} = {};'.format(name, json.dumps(html)))
            self.append_js('function func_{}(){{{}}};'.format(name, js))

    def render(self, indent, web_object):
        self.render_count += 1
        # self.render_variables(self.variables)

        if web_object:
            self.indent += len(indent)

            if self.translate_inline_styles_to_classes and \
                    isinstance(web_object, Object) and \
                    'style' in web_object._attributes and web_object._attributes['style']:
                web_object.add_class(self.add_css_class(web_object._attributes['style']))
                del web_object._attributes['style']

            if web_object._parent and isinstance(web_object._parent, Object):
                self.parent_tree.insert(0, web_object._parent)
                web_object.get_html(self)
                self.parent_tree.pop(0)
            else:
                web_object.get_html(self)

            self.indent -= len(indent)

    def render_all(self, data):
        self.render('', objectify(data))

    def inline_render(self, web_object):
        if self.separator and len(self._rendering_to) and self._rendering_to[-1].endswith(self.separator):
            self._rendering_to[-1] = self._rendering_to[-1][:-len(self.separator)]
        if web_object:
            if not isinstance(web_object, Object) and not isinstance(web_object, Objects):
                web_object = Objects(web_object)

            old_separator = self.separator
            self.separator = ''
            old_indent = self.indent
            self.indent = 0
            web_object.get_html(self)
            self.indent = old_indent

            self.separator = old_separator

        self.omit_next_indent = True

    def render_string(self, web_object):
        original = self._rendering_to
        self._rendering_to = []
        self.render('', web_object)
        html = self.html
        self._rendering_to = original
        return html

    def render_string_and_js(self, web_object):
        original = self._rendering_to
        original_js = self._rendering_js_to
        self._rendering_to = []
        self._rendering_js_to = []
        self.inline_render(web_object)
        html = self.html
        js = self.js
        self._rendering_to = original
        self._rendering_js_to = original_js
        return html, js

    def find_parent(self, type):
        for parent in self.parent_tree:
            if isinstance(parent, type):
                return parent
        return None

    def add_resource(self, url, type, module, name=''):
        self.resources.add_resource(url, type, module, name)

    def replace_resource(self, url, type, module, name=''):
        self.resources.replace_resource(url, type, module, name)

    @property
    def html(self):
        return ''.join(self._rendering_to)

    @property
    def css(self):
        css = self._css.copy()
        for style, class_name in self._css_classes.items():
            css.append('.' + class_name + '{' + style + '}')

        return '\r\n'.join(css)

    @property
    def js(self):
        return '\r\n'.join(self._rendering_js_to)

    @property
    def css_files(self):
        return [resource.url for resource in self.resources if resource.type=='css']

    @property
    def css_resources(self):
        return [resource for resource in self.resources if resource.type=='css']

    @property
    def js_files(self):
        return [resource.url for resource in self.resources if resource.type=='js']

    @property
    def js_resources(self):
        return [resource for resource in self.resources if resource.type=='js']


