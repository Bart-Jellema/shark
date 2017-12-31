from shark.common import iif
from shark.extensions.markdown import MarkdownParam
from shark.objects.base import Raw
from shark.objects.enumerations import ButtonStyle, Size, ButtonState
from shark.objects.layout import Span, Paragraph, Footer
from shark.base import Object, Default, Objects, StringParam
from shark.param_converters import BooleanParam, ObjectsParam, UrlParam, IntegerParam, RawParam


class Abbrev(Span):
    def __init__(self, text='', title='', initialism=False, **kwargs):
        super(Abbrev, self).__init__(text, **kwargs)
        self.title = self.param(title, StringParam, 'Hover over title for the abbreviation')
        self.initialism = self.param(initialism, BooleanParam, 'Initialism: Make the text slightly smaller')
        self.add_attribute('title', self.title)
        self.add_class('initialism' if self.initialism else '')
        self.tag = 'abbr'


class Anchor(Object):
    def __init__(self, text=Default, url='', bss=ButtonStyle.default, size=Size.default, state=ButtonState.none, as_button=False, microdata=False, new_window=Default, **kwargs):
        self.init(kwargs)
        self.text = self.param(text, ObjectsParam, 'Text of the link', Objects())
        self.url = self.param(url, UrlParam, 'Action when clicked', '')
        self.bss = self.param(bss, ButtonStyle, 'Visual style of the button')
        self.size = self.param(size, Size, 'indicate size when used as button')
        self.state = self.param(state, ButtonState, 'indicates the button state when used as button')
        self.as_button = self.param(as_button, BooleanParam, 'Whether the anchor be used as button')
        self.microdata = self.param(microdata, BooleanParam, 'This anchor is part of a microdata html part.')
        self.new_window = self.param(new_window, BooleanParam, 'Open in a new window.', Default)

        if self.as_button:
            self.role = "button"
            self.add_class('btn {button_type}'.format(button_type='btn-' + ButtonStyle.name(self.bss)))
            if self.size:
                self.add_class('btn-' + Size.name(self.size))
            if self.state:
                if ButtonState.name(self.state) == 'active':
                    self.add_class('active')
                elif ButtonState.name(self.state) == 'disabled':
                    self.add_class('disabled')

    def get_html(self, renderer):
        if self.new_window == Default:
            self.new_window = self.url.url(renderer).find('://') >= 0 or self.url.url(renderer).startswith('//')

        if not self.microdata:
            renderer.append('<a' + self.url.href(renderer) + self.base_attributes + iif(self.new_window, ' target="_blank"') + '>')
            renderer.inline_render(self.text)
            renderer.append('</a>')
        else:
            renderer.append('<a itemprop="item"' + self.url.href(renderer) + self.base_attributes + iif(self.new_window, ' target="_blank"') + '><span itemprop="name">')
            renderer.inline_render(self.text)
            renderer.append('</span></a>')


class Heading(Object):
    """
    Adds headings of different sizes. The &lt;small&gt; tag can be used to create a sub-heading.
    """
    def __init__(self, text=Default, level=1, subtext=Default, **kwargs):
        self.init(kwargs)
        self.text = self.param(text, ObjectsParam, 'Text of the heading', Objects())
        self.level = self.param(level, IntegerParam, 'Size of the heading, 1 is largest')
        self.subtext = self.param(subtext, ObjectsParam, 'SubText of the heading', Objects())

    def get_html(self, html):
        html.append('<h' + str(self.level) + self.base_attributes + '>')
        html.inline_render(self.text)
        if self.subtext:
            html.append(' <small>')
            html.inline_render(self.subtext)
            html.append('</small>')
        html.append('</h' + str(self.level) + '>')

    @classmethod
    def example(cls):
        return Objects([
            Heading('Heading level 1', 1, 'SubText level 1'),
            Heading('Heading level 2', 2, 'SubText level 2'),
            Heading('Heading level 3', 3, 'SubText level 3'),
            Heading('Heading level 4', 4, 'SubText level 4'),
            Heading('Heading level 5', 5, 'SubText level 5'),
            Heading('Heading level 6', 6, 'SubText level 6')
        ])


class Small(Object):
    def __init__(self, text=None, **kwargs):
        self.init(kwargs)
        self.text = self.param(text, ObjectsParam, 'Small text')

    def get_html(self, html):
        html.append('<small' + self.base_attributes + '>')
        html.inline_render(self.text)
        html.append('</small>')


class Pre(Object):
    def __init__(self, text='', **kwargs):
        self.init(kwargs)
        self.text = self.param(text, StringParam, 'Text of the formatted paragraph')

    def get_html(self, html):
        html.append('<pre' + self.base_attributes + '>' + self.text + '</pre>')


class Code(Object):
    def __init__(self, text='', **kwargs):
        self.init(kwargs)
        self.text = self.param(text, StringParam, 'The code')

    def get_html(self, html):
        html.append('<code' + self.base_attributes + '>' + self.text + '</code>')


class Label(Object):
    def __init__(self, text='', button_style=ButtonStyle.default, **kwargs):
        self.init(kwargs)
        self.text = self.param(text, StringParam, 'Text of the formatted paragraph')
        self.button_style = self.param(button_style, ButtonStyle, 'Visual style of the label')
        self.add_class('label')
        if self.button_style != ButtonStyle.default:
            self.add_class('label-{}'.format(ButtonStyle.name(self.button_style)))

    def get_html(self, html):
        html.append('<span' + self.base_attributes + '>' + self.text + '</span>')


class Br(Object):
    """
    Adds a line break.
    """
    def __init__(self, **kwargs):
        self.init(kwargs)

    def get_html(self, html):
        html.append('<br' + self.base_attributes + '/>')

    @classmethod
    def example(cls):
        return Objects([
            'Line 1',
            Br(),
            'Line 2'
        ])


class Hr(Object):
    """
    Adds a horizontal divider.
    """
    def __init__(self, **kwargs):
        self.init(kwargs)

    def get_html(self, html):
        html.append('<hr' + self.base_attributes + '/>')

    @classmethod
    def example(cls):
        return Objects([
            Paragraph('Before the divider'),
            Hr(),
            Paragraph('After the divider')
        ])


class Blockquote(Object):
    """
    For quoting blocks of content from another source within your document.
    """
    def __init__(self, text='', source='', cite='', reverse=False, **kwargs):
        self.init(kwargs)
        self.text = self.param(text, MarkdownParam, 'The quotation text', '')
        self.source = self.param(source, StringParam, 'Source of the quote', '')
        self.cite = self.param(cite, StringParam, 'Citiation', '')
        self.reverse = self.param(reverse, BooleanParam, 'Specifying whether the quote is reversed', False)
        if self.reverse:
            self.add_class('blockquote-reverse')

    def get_html(self, html):
        html.append('<blockquote ' + self.base_attributes + '>')
        html.render('    ', self.text)
        if self.source:
            source_text = self.source + ((' in <cite title="{}">'.format(self.cite) + self.cite + '</cite>') if self.cite else '')
            html.render('    ', Footer(Raw(source_text), id=""))
        html.append('</blockquote>')

    @classmethod
    def example(cls):
        return Blockquote(
            'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer posuere erat a ante.',
            'Someone famous',
            'Source Title'
        )


class ObfuscateWithJavascript(Object):
    def __init__(self, raw='', **kwargs):
        self.init(kwargs)
        self.raw = self.param(raw, RawParam, 'Raw html to be encoded with Javascript so web scrapers have a harder time getting it.')

    def get_html(self, html):
        chars = list(set(self.raw))
        locs = []
        for char in self.raw:
            locs.append(str(chars.index(char)))

        html.append('<script type="text/javascript">')
        html.append('    var chars = [{}];'.format(','.join(['"{}"'.format(c.replace('\\', '\\\\').replace('"', '\\"')) for c in chars])))
        html.append('    var locs = [{}];'.format(','.join(locs)))
        html.append('    for(var i=0;i<locs.length;i++){document.write(chars[locs[i]]);}')
        html.append('</script>')
