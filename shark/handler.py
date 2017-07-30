import json
import logging
from collections import Iterable

import bleach
import pickle

import markdown
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core import signing
from django.core.exceptions import FieldDoesNotExist
from django.core.urlresolvers import reverse, get_resolver, RegexURLResolver, RegexURLPattern, NoReverseMatch
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.test import Client
from django.test import TestCase
from django.utils.html import escape
from django.utils.http import urlquote
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.views.static import serve

from shark import models
from shark.actions import JS, JQ, URL, Action, BaseAction
from shark.common import listify
from shark.extensions.markdown import Markdown, ALLOWED_TAGS, ALLOWED_ATTRIBUTES, ALLOWED_STYLES
from shark.models import EditableText, StaticPage as StaticPageModel
from shark.objects.analytics import GoogleAnalyticsTracking
from shark.objects.base import Script
from shark.objects.layout import Div, Spacer, Row
from shark.objects.navigation import NavLink
from shark.objects.ui_elements import BreadCrumbs
from shark.param_converters import ObjectsParam
from shark.renderer import Renderer
from shark.settings import SharkSettings
from .base import Objects, Object, PlaceholderWebObject
from .resources import Resources

unique_name_counter = 0

class BaseHandler:
    route = None
    redirects = None

    def __init__(self, *args, **kwargs):
        pass

    def render_base(self, request, *args, **kwargs):
        return self.render(request, *args, **kwargs)

    def render(self, request, *args, **kwargs):
        raise Http404("Not Implemented")

    unique_name = None
    @classmethod
    def get_unique_name(cls):
        if not cls.unique_name:
            global unique_name_counter
            unique_name_counter += 1
            cls.unique_name = '{}-{}'.format(cls.__name__, unique_name_counter)

        return cls.unique_name

    @classmethod
    def url(cls, *args, **kwargs):
        return URL(reverse('shark:' + cls.get_unique_name(), args=args, kwargs=kwargs, current_app='shark'), False)

    @classmethod
    def sitemap(cls):
        return True

    @classmethod
    def get_sitemap(cls, include_false=False):
        sitemap = cls.sitemap()
        if sitemap == True or (sitemap == False and include_false):
            try:
                u = cls.url()
                return [[]]
            except NoReverseMatch:
                return []
        elif isinstance(sitemap, str):
            return [sitemap]
        elif isinstance(sitemap, list):
            return sitemap

        return []

    def build_absolute_uri(self):
        return self.re

class NotFound404(Exception):
    pass


class BasePageHandler(BaseHandler):
    ignored_variables = ['items', 'modals', 'nav', 'container', 'base_object', 'current_user', 'user']

    def __init__(self, *args, **kwargs):
        self.title = ''
        self.description = ''
        self.keywords = ''
        self.author = ''
        self.extra_meta = ''
        self.robots_index = True
        self.robots_follow = True

        self.items = Objects()
        self.base_object = self.items
        self.modals = Objects()
        self.nav = None
        self.crumbs = []
        self.main = None
        self.footer = None

        self.javascript = ''

        self.resources = Resources()

        print('Handler created', self.__class__.__name__, now())

    def init(self, request):
        pass

    def output_html(self, args, kwargs):
        print('Start output HTML', now())
        content = Objects()
        content.append(self.modals)
        content.append(self.nav)
        content.append(self.main)
        if self.crumbs:
            self.base_object.insert(0, Spacer())
            self.base_object.insert(1, Row(Div(BreadCrumbs(*self.crumbs), classes='col-md-12')))
        content.append(self.items)
        content.append(self.footer)

        keep_variables = {}
        for variable_name in dir(self):
            if variable_name not in self.ignored_variables:
                variable = self.__getattribute__(variable_name)
                if isinstance(variable, Object):
                    keep_variables[variable_name] = variable.serialize()

        renderer = Renderer(self)
        print('Start render', now())
        renderer.render('        ', content)
        print('End render', now(), renderer.render_count)

        renderer.resources.add_resources(self.resources)

        if not self.robots_follow:
            self.extra_meta += '\r\n        <meta name="robots" content="nofollow">'
        if not self.robots_index:
            self.extra_meta += '\r\n        <meta name="robots" content="noindex">'

        html = render(self.request, 'shark/base.html', {
                                  'title': self.title,
                                  'description': self.description.replace('"', '\''),
                                  'keywords': self.keywords,
                                  'author': self.author,
                                  'extra_meta': self.extra_meta,
                                  'content': renderer.html,
                                  'extra_css': '\r\n'.join(
                                      [
                                          '        <link rel="stylesheet" href="{}" id="resource-{}-{}"/>'.format(css_resource.url, css_resource.module, css_resource.name)
                                          for css_resource in renderer.css_resources
                                      ]
                                  ),
                                  'extra_js': '\r\n'.join(
                                      ['        <script src="{}"></script>'.format(js_file)
                                      for js_file in renderer.js_files]
                                  ),
                                  'javascript': renderer.js,
                                  'css': renderer.css,
                                  'keep_variables': keep_variables
        })

        print('End output HTML', now())
        return html


    def render(self, request, *args, **kwargs):
        #Always send the crsf token
        get_token(request)

        self.request = request
        self.user = self.request.user

        if request.method == 'GET':
            self.init(request)
            if SharkSettings.SHARK_GOOGLE_ANALYTICS_CODE:
                self += GoogleAnalyticsTracking(SharkSettings.SHARK_GOOGLE_ANALYTICS_CODE)
            try:
                result = self.render_page(request, *args, **kwargs)
            except NotFound404:
                raise Http404()
            else:
                if result is None:
                    return self.output_html(args, kwargs)
                else:
                    return result
        elif request.method == 'POST':
            action = self.request.POST.get('action', '')
            keep_variables = json.loads(self.request.POST.get('keep_variables', '{}'))
            keep_variable_objects = []
            for variable_name in keep_variables:
                placeholder = PlaceholderWebObject(
                    self,
                    keep_variables[variable_name]['id'],
                    keep_variables[variable_name]['class_name']
                )
                keep_variable_objects.append(placeholder)

                self.__setattr__(variable_name, placeholder)

            arguments = {}
            for argument in self.request.POST:
                if argument not in ['action', 'keep_variables', 'csrfmiddlewaretoken']:
                    arguments[argument] = self.request.POST[argument]

            self.renderer = Renderer()

            if action:
                self.__getattribute__(action)(*args, **arguments)

            javascript = [self.javascript]

            for obj in keep_variable_objects:
                self.renderer.render_variables(obj.variables)

            self.renderer.render_all(self.items)

            javascript.append(self.renderer.js)

            for obj in keep_variable_objects:
                javascript.extend([jq.js(self.renderer) for jq in obj.jqs])

            data = {'javascript': ''.join(javascript),
                    'html': '',
                    'data': ''}
            json_data = json.dumps(data)

            return HttpResponse(json_data)

    def __iadd__(self, other):
        self.base_object += other
        return self

    def append_row(self, *args, **kwargs):
        self += Row(Div(args, classes='col-md-12'), **kwargs)

    def add_javascript(self, script):
        if isinstance(script, Object):
            self += script
            return

        if isinstance(script, BaseAction):
            script = script.js

        if self.request.method == 'GET':
            self += Script(script)
        else:
            self.javascript += ';' + script

    def render_page(self, request):
        raise NotImplementedError

    def text(self, name, default_txt=None):
        text = EditableText.load(name)
        if not text:
            text = EditableText()
            text.name = name
            text.content = default_txt or name
            text.filename = ''
            text.handler_name = self.__class__.__name__
            text.line_nr = 0
            text.last_used = now()
            text.save()

        return text.content

    def replace_resource_js(self, resource):
        return JS('$("#resource-{}-{}").attr("href", "{}").on("load", function(){{$(window).resize()}});'.format(resource.module, resource.name, resource.url))

    def redirect(self, url):
        self.add_javascript('window.location="{}"'.format(urlquote(url, ':/@')))

    def _form_post(self, *args, **kwargs):
        form_data = signing.loads(kwargs.pop('form_data'), serializer=lambda: pickle)
        cls = form_data['cls']
        print('FORM DATA', form_data)
        action = self.__getattribute__(kwargs.pop('sub_action'))
        form_error_handler = cls[form_data['err']]()

        has_error = False
        for field in kwargs:
            if field in form_data['fld']:
                fld = form_data['fld'][field]
                value = kwargs[field]
                for validator_class, data in fld['valid']:
                    validator_instance = cls[validator_class]()
                    validator_instance.deserialize(data)
                    outcome = validator_instance.validate(value)

                    if outcome is not None:
                        has_error = True

                        error_class, id = fld['err']
                        field_error = cls[error_class](field)
                        if isinstance(id, int):
                            id = '{}_{}'.format(field_error.__class__.__name__, id)

                        selector = '$("#{}")'.format(id)
                        error_renderer = Renderer()
                        field_error.render_error(error_renderer, outcome)
                        self.javascript += JQ(selector).append_raw(error_renderer.html).js(error_renderer)
                        self.javascript += error_renderer.js

        if has_error:
            return
        else:
            if 'data' in form_data:
                data_class, data_id = form_data['data']
                if data_id:
                    data = data_class.objects.get(id=data_id)
                else:
                    data = data_class()
                fields = data._meta.get_fields()

                for field_name in kwargs:
                    try:
                        field = data._meta.get_field(field_name)
                        data.__setattr__(field_name, kwargs[field_name])
                    except FieldDoesNotExist:
                        pass #TODO: handle these

                action(*args, data)
            else:
                action(*args, kwargs)


def exists_or_404(value):
    if not value:
        raise Http404()
    return value


class HandlerTestCase(TestCase):
    def setUp(self):
        pass

    url = None
    def test_response_is_200(self):
        if self.__class__.url:
            logging.info('URL', self.__class__.url)
            client = Client()
            response = client.get(self.__class__.url)

            self.assertEqual(response.status_code, 200)


class Container(Object):
    def __init__(self, items=None, **kwargs):
        self.init(kwargs)
        self.items = self.param(items, ObjectsParam, 'Items in the container', Objects())
        self.add_class('container')

    def get_html(self, html):
        html.append('<div' + self.base_attributes + '>')
        html.render('    ', self.items)
        html.append('</div>')

    def insert(self, i, x):
        self.items.insert(i, x)


class BaseContainerPageHandler(BasePageHandler):
    def __init__(self, *args, **kwargs):
        super(BaseContainerPageHandler, self).__init__(*args, **kwargs)

        self.container = Container(Objects())
        self += self.container
        self.base_object = self.container.items


def shark_django_handler(request, *args, handler=None, **kwargs):
    handler_instance = handler()
    outcome = handler_instance.render_base(request, *args, **kwargs)
    return outcome


@csrf_exempt
def shark_django_handler_no_csrf(request, *args, handler=None, **kwargs):
    handler_instance = handler()
    outcome = handler_instance.render_base(request, *args, **kwargs)
    return outcome


def shark_django_redirect_handler(request, *args, handler=None, function=None, **kwargs):
    if function:
        if isinstance(function, str):
            url = handler().__getattribute__(function)(request, *args, **kwargs)
        else:
            url = handler.url(*listify(function(request, *args, **kwargs)))
    else:
        url = handler.url(*args, **kwargs)

    return HttpResponsePermanentRedirect(url)


class StaticPage(BasePageHandler):
    def render_page(self, request, url_name):
        page = StaticPageModel.load(url_name)
        if not page:
            raise NotFound404()

        self.title = page.title
        self.description = page.description
        self += Markdown(page.body)

        if self.user.is_staff and self.user.has_perm('shark.staticpage_change'):
            if self.nav:
                self.nav.right_items.append(NavLink('Edit Page', reverse('admin:shark_staticpage_change', args=[page.url_name])))

    @classmethod
    def url(cls, *args, **kwargs):
        return URL(reverse('shark:shark_static_page', args=args, kwargs=kwargs), False)

    @classmethod
    def sitemap(cls):
        pages = models.StaticPage.objects.filter(sitemap=True).all()
        return [sp.url_name for sp in pages]


def markdown_preview(request):
    """ Render preview page.
    :returns: A rendered preview
    """
    user = getattr(request, 'user', None)
    if not user or not user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())

    dirty = markdown.markdown(text=escape(request.POST.get('data', 'No content posted')), output_format='html5')
    value = bleach.clean(dirty, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, styles=ALLOWED_STYLES)
    return HttpResponse(value)


class Robots(BaseHandler):
    route = '^robots.txt$'

    def render(self, request):
        return HttpResponse(
            "User-agent: *\r\n" +
            "Disallow: /admin/*\r\n" +
            "Disallow: /__debug__/*"
        )

    @classmethod
    def sitemap(cls):
        return False


class SiteMap(BaseHandler):
    route = '^sitemap.xml$'

    def get_urls(self, include_false=False):
        urls = set()

        handlers = set()

        def add_patterns(patterns):
            for pattern in patterns:
                if isinstance(pattern, RegexURLResolver):
                    add_patterns(pattern.url_patterns)
                elif isinstance(pattern, RegexURLPattern):
                    if 'handler' in pattern.default_args and issubclass(pattern.default_args['handler'], BaseHandler):
                        handler = pattern.default_args['handler']
                        if handler not in handlers:
                            handlers.add(handler)
                            for args in handler.get_sitemap(include_false):
                                if isinstance(args, str) or not isinstance(args, Iterable):
                                    args=[args]
                                urls.add(handler.url(*args))

        add_patterns(get_resolver().url_patterns)

        return urls

    def render(self, request):
        lines = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
        handlers = set()
        for url in self.get_urls():
            lines.append('    <url><loc>{}</loc></url>'.format(request.build_absolute_uri(url.url)))

        lines.append('</urlset>')
        return HttpResponse('\r\n'.join(lines))

    @classmethod
    def sitemap(cls):
        return False


class Favicon(BaseHandler):
    route = '^favicon.ico$'

    def render(self, request, *args, **kwargs):
        return HttpResponseRedirect(staticfiles_storage.url('icons/favicon-32x32.png'))


class GoogleVerification(BaseHandler):
    def render(self, request):
        return HttpResponse('google-site-verification: {}.html'.format(SharkSettings.SHARK_GOOGLE_VERIFICATION))

    @classmethod
    def sitemap(cls):
        return False


class BingVerification(BaseHandler):
    def render(self, request):
        return HttpResponse('<?xml version="1.0"?><users><user>{}</user></users>'.format(SharkSettings.SHARK_BING_VERIFICATION))

    @classmethod
    def sitemap(cls):
        return False


class YandexVerification(BaseHandler):
    def render(self, request):
        return HttpResponse('<html><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"></head><body>Verification: {}</body></html>'.format(SharkSettings.SHARK_YANDEX_VERIFICATION))

    @classmethod
    def sitemap(cls):
        return False
