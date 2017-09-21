import logging
from collections import Iterable
from inspect import isclass, isroutine, getmembers

from shark.common import Default
from shark.dependancies import escape_url, escape_html


class BaseParamConverter(object):
    @classmethod
    def convert(cls, value, parent_object):
        return value


class EnumerationMeta(type):
    @property
    def value_map(cls):
        if not cls.__value_map:
            obj = cls()
            cls.__value_map = {
                obj.__getattribute__(name): name
                for name in dir(cls)
                if name not in dir(Enumeration) and isinstance(obj.__getattribute__(name), int)
            }

        return cls.__value_map

    @property
    def str_map(cls):
        if not cls.__str_map:
            cls._str_map = {value: key for key, value in cls.value_map.items()}
            obj = cls()
            cls.__str_map = {
                name: obj.__getattribute__(name)
                for name in dir(cls)
                if name not in dir(Enumeration) and isinstance(obj.__getattribute__(name), int)
                }
    
        return cls.__str_map


class Enumeration(BaseParamConverter, metaclass=EnumerationMeta):
    __value_map = None
    __str_map = None

    @classmethod
    def name(cls, value):
        if value in cls.value_map:
            return cls.value_map[value]
        else:
            raise ValueError()

    @classmethod
    def names(cls):
        return cls.value_map.values()

    @classmethod
    def from_str(cls, value):
        if value in cls.str_map:
            return cls.str_map[value]
        else:
            raise ValueError()

    @classmethod
    def convert(cls, value, parent_object):
        if value is None or isinstance(value, int):
            return value
        elif str(value) in cls.str_map:
            try:
                value = cls.from_str(value)
                if value is not None:
                    return value
            except ValueError:
                pass

        raise TypeError('Parameter isn\'t of type {}'.format(cls.__name__))

    @classmethod
    def choices(cls):
        members = getmembers(cls, lambda m: not(isroutine(m)))
        props = [m for m in members if not(m[0][:1] == '_')]
        choices = tuple([(p[1], p[0]) for p in props])
        return choices


class Value(object):
    """
    Values passed into Shark Objects as parameters or attributes can have special conversion before passed to Shark.
    Any object passed into Shark derived from Value will not be used directly, but result from the as_param and
    as_attr functions will be used.
    """
    def as_param(self):
        return self

    # noinspection PyUnusedLocal
    def set_attr(self, obj, name):
        return name + "='" + escape_url(str(self)) + "'"


class StringParam(BaseParamConverter):
    """
    Turns the value into an html-safe str.
    None will become the empty string.
    To other objects the str() method will be applied.
    """
    @classmethod
    def convert(cls, value, parent_object):
        if value is not None:
            if isinstance(value, str):
                return escape_html(value)
            else:
                return escape_html(str(value))

        return ''


class BaseObject(object):
    """

    """


class Object(BaseObject, BaseParamConverter):
    """
    Objects are the main building blocks in Shark. Trees of classes derived from Object get rendered into
    html, js, etc.
    """

    # Every class derived from Object keeps a counter to create unique html ids for the objects
    object_number = 0

    # noinspection PyAttributeOutsideInit
    def init(self, kwargs):
        """
        Called with the kwargs of the custom __init__ function of any subclass. This function must be called.
        :param kwargs: The kwargs that were passed into the __init__ function. Don't prepend the **, just pass the
                       kwargs dictionary. The following kwargs are available:
        :return: None
        """
        self._id = kwargs.pop('id', None)
        self._attributes = {}
        self._parent = None

        self._variables = {}

        for key, value in kwargs.items():
            key = key.strip('_')
            if isinstance(value, Value):
                value.set_attr(self, key)
            else:
                self._attributes[key] = value

    def __str__(self):
        return '<{} - {}>'.format(self.__class__.__name__, self._id)

    def __repr__(self):
        return '<{} - {}>'.format(self.__class__.__name__, self._id)

    @classmethod
    def convert(cls, value, parent_object):
        if value is None or isinstance(value, cls):
            return value
        else:
            raise TypeError('Parameter not of class {}'.format(cls.__name__))

    # noinspection PyAttributeOutsideInit
    @property
    def id(self):
        """
        The id gets created when it's first requested. Elements for which the id is never requested, don't have an id.
        :return: The created or existing html id
        """
        if not self._id:
            self.__class__.object_number += 1
            self._id = '%s_%s' % (self.__class__.__name__, self.__class__.object_number)

        return self._id

    def id_needed(self):
        return self.id

    @property
    def parent(self):
        return self._parent

    # noinspection PyUnusedLocal
    def param(self, value, converter, description='', default=None):
        """
        Converts a parameter passed in a Shark Object
        :param value: Value of the parameter
        :param converter: How to treat the input, pass in a subclass of BaseParamConverter
        :param description: This is used for documentation purposes
        :param default: The default value used if the Default class is passed in
        :return: The supplied value converted according to the type.
        """
        if value == Default:
            value = default

            # If Default is the default value you can detect whether or not this parameter was provided or not in
            # your rendering code.
            if value == Default:
                return Default

        # If a Value object was passed in, get the actual value.
        if isinstance(value, Value):
            value = value.as_param()

        if isclass(converter) and issubclass(converter, BaseParamConverter):
            return converter.convert(value, self)
        else:
            raise TypeError('type should be derived from BaseParamConverter')

    @property
    def base_attributes(self):
        output = []
        if self._id:
            output.append('id="{}"'.format(self.id))
        for attr, value in self._attributes.items():
            output.append('{}="{}"'.format(attr, value))

        if output:
            return ' ' + ' '.join(output)
        else:
            return ''

    def add_class(self, class_names):
        new_classes = class_names.split()
        existing_classes = self._attributes.setdefault('class', '').split()
        for class_name in new_classes:
            if class_name not in existing_classes:
                self._attributes['class'] += ' ' + class_name

        self._attributes['class'] = self._attributes['class'].strip()

    def add_style(self, style):
        old_style = self._attributes.setdefault('style', '')
        self._attributes['style'] = old_style + ('' if old_style.endswith(';') else ';') + style

    # noinspection PyAttributeOutsideInit
    def add_attribute(self, key, value):
        if key in self._attributes:
            logging.warning('"{}" attribute already set, overridden'.format(key))
        self._attributes[key] = value

    def add_variable(self, web_object):
        name = self.id.lower() + '_' + str(len(self._variables) + 1)
        self._variables[name] = objectify(web_object)
        return name

    def get_html(self, renderer):
        pass

    def serialize(self):
        return {'class_name': self.__class__.__name__, 'id': self.id}

    def __add__(self, other):
        obj = objectify(other)
        if obj is None:
            return self
        elif isinstance(obj, Object):
            return Objects([self, obj])

        return NotImplemented

    def __radd__(self, other):
        obj = objectify(other)
        if obj is None:
            return self
        elif isinstance(obj, Object):
            return Objects([obj, self])

        return NotImplemented

    def __iadd__(self, other):
        obj = objectify(other)
        if obj is None:
            return self
        elif isinstance(obj, (Object, Objects)):
            if 'items' in dir(self):
                if self.items is None:
                    self.items = Objects()

                self.items += obj

                return self
        else:
            raise NotImplementedError("{} does not have 'items'".format(self.__class__.__name__))


    @property
    def jq(self):
        from shark.actions import JQ
        return JQ("$('#{}')".format(self.id), self)

    @classmethod
    def example(cls):
        return NotImplemented


class Objects(list, BaseObject):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.append(*args)

        self._parent = None

    def __repr__(self):
        original = list.__repr__(self)
        return "{}({})".format(self.__class__.__name__, original)

    def get_html(self, html):
        if self._parent and isinstance(self._parent, Object):
            html.parent_tree.insert(0, self._parent)
            for web_object in self:
                html.render('', web_object)
            html.parent_tree.pop(0)
        else:
            for web_object in self:
                html.render('', web_object)

    def append(self, *objects):
        for obj in objects:
            if obj is not None:
                if isinstance(obj, Iterable) and not isinstance(obj, str):
                    self.append(*obj)
                else:
                    obj = objectify(obj)
                    super().append(obj)
                    obj._parent = self

    def __add__(self, other):
        self.append(objectify(other))
        return self

    def __iadd__(self, other):
        self.append(objectify(other))
        return self


class PlaceholderWebObject(BaseObject):
    def __init__(self, handler, object_id, class_name):
        self.handler = handler
        self.id = object_id
        self.class_name = class_name
        self.variables = {}
        self.jqs = []

    @property
    def jq(self):
        from shark.actions import JQ
        jq = JQ("$('#{}')".format(self.id), self)
        self.jqs.append(jq)
        return jq

    def add_variable(self, web_object):
        name = self.id.lower() + '_' + str(len(self.variables) + 1)
        self.variables[name] = objectify(web_object)
        return name

    def replace(self, web_object):
        self.jq.html(web_object)

    # TODO: Support calling methods on the original class, like Image().src()
    def src(self, src):
        return self.jq.attr('src', src)


class Text(Object):
    """
    Just plain text.
    """
    def __init__(self, text='', **kwargs):
        self.init(kwargs)
        self.text = self.param(text, StringParam, 'The text')

    def get_html(self, html):
        html.append(self.text)

    def __str__(self):
        return self.text or ''

    @classmethod
    def example(cls):
        return Text('Hello world!')


def objectify(obj):
    if isinstance(obj, Object) or obj is None:
        return obj
    elif isinstance(obj, Iterable) and not isinstance(obj, str):
        return Objects(obj)
    elif isinstance(obj, Objects):
        return None
    else:
        return Text(str(obj))



