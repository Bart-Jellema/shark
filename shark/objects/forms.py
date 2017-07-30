import pickle

from collections import Iterable
from django.contrib.admin.utils import quote
from django.core import signing, validators
from django.core.exceptions import ValidationError, FieldDoesNotExist
from django.db.models import QuerySet, IntegerField
from shark.base import Object, objectify, Default, StringParam, BaseParamConverter
from shark.common import listify, attr, iif
from shark.param_converters import ObjectsParam, ModelParam, BooleanParam, IntegerParam, ListParam


class FieldError(Object):
    sub_classes = {}

    def __init__(self, field_name, **kwargs):
        self.init(kwargs)
        self.field_name = self.param(field_name, StringParam, 'Name of the field to show errors for')
        self.id_needed()

    def render_container(self, renderer):
        renderer.append('<ul' + self.base_attributes + '></ul>')

    def render_error(self, renderer, message):
        renderer.append('<li>')
        renderer.render('    ', message)
        renderer.append('</li>')

    def _render_error(self, renderer, message):
        self.render_error(renderer, objectify(message))

    def get_html(self, renderer):
        self.form = renderer.find_parent(Form)
        self.form.form_data['fld'][self.field_name]['err'] = (self.form.form_data_class(self.__class__), self.id)
        self.add_class('form-error')
        self.render_container(renderer)


class SpanBrFieldError(FieldError):
    def render_container(self, renderer):
        self.add_class('help-block with-errors')
        renderer.append('<span' + self.base_attributes + '></span>')

    def render_error(self, renderer, message):
        renderer.append('<span class="text-danger">')
        renderer.render('    ', objectify(message))
        renderer.append('</span><br>')


class FormError(Object):
    sub_classes = {}

    def __init__(self, form_id=None, **kwargs):
        self.init(kwargs)
        self.form_id = form_id

    def render_container(self, renderer):
        renderer.append('<ul' + self.base_attributes + '></ul>')

    def render_error(self, renderer, message):
        renderer.append('<li>')
        renderer.render('    ', message)
        renderer.append('</li>')

    def _render_error(self, renderer, message):
        self.render_error(renderer, ObjectsParam.convert(message))

    def get_html(self, renderer):
        self.form = renderer.find_parent(Form)
        self.form.error_object = self
        self.add_class('form-error')
        self.render_container(renderer)


class ParagraphFormError(FormError):
    def render_container(self, renderer):
        renderer.append('<span' + self.base_attributes +'></span>')

    def render_error(self, renderer, message):
        renderer.append('<p>')
        renderer.render('    ', message)
        renderer.append('</p>')


class SpanBrFormError(FormError):
    def render_container(self, renderer):
        renderer.append('<span' + self.base_attributes + '></span>')

    def render_error(self, renderer, message):
        renderer.append('<span class="text-danger">')
        renderer.render('    ', message)
        renderer.append('</span><br>')


class Validator:
    def __init__(self, message='Invalid input.'):
        self.message = message
        self.init()

    def init(self):
        pass

    def validate(self, value):
        pass

    def enable_live_validation(self, web_object):
        pass

    def serialize(self):
        return self.message

    def deserialize(self, value):
        self.message = value


class RequiredValidator(Validator):
    def init(self):
        if not self.message:
            self.message = 'This field is required'

    def validate(self, value):
        if not value:
            return self.message

    def enable_live_validation(self, field):
        field.add_attribute('required', 'required')
        field.add_attribute('data-required-error', self.message)


class EmailValidator(Validator):
    def validate(self, value):
        try:
            validators.EmailValidator()(value)
        except ValidationError:
            return self.message


class Form(Object):
    def __init__(self, data=None, items=None, style='', **kwargs):
        self.init(kwargs)
        self.data = self.param(data, ModelParam, 'The model')
        self.items = self.param(items, ObjectsParam, 'Items in the form')
        self.style = self.param(style, StringParam, 'Form style: inline or horizontal')

        if self.style:
            self.add_class('form-' + self.style)

        self.error_object = None
        self.form_data = {'id': self.id, 'fld': {}, 'cls': []}
        if self.data:
            self.form_data['data'] = (self.data.__class__, self.data.id)
        self.form_data_classes = {}
        self.fields = {}
        self.errors = []

        self.id_needed()

    def form_data_class(self, cls):
        if not cls in self.form_data_classes:
            self.form_data['cls'].append(cls)
            self.form_data_classes[cls] = self.form_data['cls'].index(cls)
        return self.form_data_classes[cls]

    def get_html(self, renderer):
        renderer.append('<form' + self.base_attributes + ' role="form" data-toggle="validator" data-async>')
        renderer.append('    <input type="hidden" name="action" value="_form_post">')
        renderer.append('    <input type="hidden" name="sub_action" value="">')
        renderer.render('    ', self.items)
        if not self.error_object:
            self.error_object = SpanBrFormError()
            self.error_object._parent = self
            renderer.render('    ', self.error_object)

        self.form_data['err'] = self.form_data_class(self.error_object.__class__)

        form_data = signing.dumps(self.form_data, compress=True, serializer=lambda: pickle)
        renderer.append('    <input type="hidden" name="form_data" value="{}">'.format(form_data))
        renderer.append('</form>')


class FormGroup(Object):
    def __init__(self, items=Default, style='', **kwargs):
        self.init(kwargs)
        self.items = self.param(items, ObjectsParam, 'Items in the form group')
        self.add_class('form-group')
        self.add_class('has-feedback')

    def get_html(self, renderer):
        renderer.append('<div' + self.base_attributes + '>')
        renderer.render('    ', self.items)
        renderer.append('</div>')


def ensure_formgroup(func):
    def wrapper(self, renderer):
        formgroup = renderer.find_parent(FormGroup)
        if not formgroup:
            parent = self.parent
            formgroup = FormGroup(self)
            formgroup._parent = parent
            formgroup.get_html(renderer)
        else:
            func(self, renderer)

    return wrapper


class ValidatorListParam(BaseParamConverter):
    @classmethod
    def convert(cls, value, parent_object):
        if value is None:
            return []
        if isinstance(value, Validator):
            return [value]
        if isinstance(value, list):
            # TODO: Check that all items are of type Validator?
            return value
        if isinstance(value, Iterable):
            return list(value)

        raise TypeError('Parameter not a list of validators')


class BaseField(Object):
    def __init__(self, name=None, value=Default, required=False, min_length=None, max_length=None, form_validators=None, **kwargs):
        self.init(kwargs)
        self.name = self.param(name, StringParam, 'Name of the field')
        self.value = self.param(value, StringParam, 'Starting value of the field', Default)
        self.required = self.param(required, BooleanParam, 'Is this field required?')
        self.min_length = self.param(min_length, IntegerParam, 'Is this field required?')
        self.max_length = self.param(max_length, IntegerParam, 'Is this field required?')
        self.validators = self.param(form_validators, ValidatorListParam, 'Validator instance or a list of Validators.')

        self.display_name = self.name.replace('_', ' ').title()
        if self.required:
            self.validators.append(RequiredValidator())

        for validator in self.validators:
            validator.enable_live_validation(self)


class HiddenField(BaseField):
    def __init__(self,  name=None, value=Default, **kwargs):
        super().__init__(name, value, **kwargs)

    def get_html(self, renderer):
        renderer.append('<input type="hidden"' +
                    self.base_attributes +
                    attr('name', self.name) +
                    attr('value', '' if self.value == Default else self.value) +
                    '>')


class TextField(BaseField):
    def __init__(self,  name=None, label='', placeholder='', auto_focus=False,
                 help_text='', value=Default, **kwargs):
        super().__init__(name, value, **kwargs)
        self.label = self.param(label, StringParam, 'Text of the label')
        self.placeholder = self.param(placeholder, StringParam, 'Placeholder if input is empty')
        self.auto_focus = self.param(auto_focus, BooleanParam, 'Place the focus on this element')
        self.help_text = self.param(help_text, StringParam, 'help text for the input field')
        self.type = 'text'
        self.add_class('form-control')

    @ensure_formgroup
    def get_html(self, renderer):
        for validator in self.validators:
            if isinstance(validator, EmailValidator):
                self.type = 'email'

        renderer.add_resource('https://cdnjs.cloudflare.com/ajax/libs/1000hz-bootstrap-validator/0.10.1/validator.min.js', 'js', 'validator', 'main')

        form = renderer.find_parent(Form)
        form.form_data['fld'][self.name] = {
            'cls': form.form_data_class(self.__class__),
            'valid': [(form.form_data_class(validator.__class__), validator.serialize()) for validator in self.validators]
        }

        if self.value == Default and form.data:
            try:
                field = form.data._meta.get_field(self.name)
                self.value = form.data.__getattr__(self.name)
            except FieldDoesNotExist:
                pass


        if self.label or self.display_name:
            renderer.append('<label for="{}">{}</label>'.format(self.id, self.label or self.display_name))

        renderer.append('<input type="' + self.type + '"' +
                    self.base_attributes +
                    attr('name', self.name) +
                    attr('value', '' if self.value == Default else self.value) +
                    attr('placeholder', self.placeholder) +
                    iif(self.auto_focus, ' data-autofocus') +
                    '>')
        renderer.append('<span class="glyphicon form-control-feedback" aria-hidden="true"></span>')

        field_error = SpanBrFieldError(self.name)
        renderer.append('<span class="help-block">')
        field_error.get_html(renderer)
        renderer.append('    ' + self.help_text)
        renderer.append('</span>')


class BooleanField(BaseField):
    def __init__(self,  name=None, label='', value=Default, **kwargs):
        super().__init__(name, value, **kwargs)
        self.label = self.param(label, StringParam, 'Text of the label')

    @ensure_formgroup
    def get_html(self, renderer):
        renderer.add_resource('https://cdnjs.cloudflare.com/ajax/libs/1000hz-bootstrap-validator/0.10.1/validator.min.js', 'js', 'validator', 'main')

        form = renderer.find_parent(Form)
        form.form_data['fld'][self.name] = {
            'cls': form.form_data_class(self.__class__),
            'valid': [(form.form_data_class(validator.__class__), validator.serialize()) for validator in self.validators]
        }

        if self.value == Default and form.data:
            try:
                field = form.data._meta.get_field(self.name)
                self.value = form.data.__getattribute__(self.name)
            except FieldDoesNotExist:
                pass

        if self.value:
            self.add_attribute('checked', 'checked')

        field_error = SpanBrFieldError(self.name)
        renderer.append('<div class="checkbox">')
        renderer.append('    <label>')
        renderer.append('        <input type="checkbox"' + self.base_attributes + attr('name', self.name) + '>')
        renderer.append('        ' + self.label)
        renderer.append('    </label>')
        field_error.get_html(renderer)
        renderer.append('</div>')


class EmailField(TextField):
    def __init__(self,  name=None, label='', placeholder='', auto_focus=False,
                 help_text='', value=Default, **kwargs):
        super().__init__(name, label, placeholder, auto_focus, help_text, value, **kwargs)

        validator_found = False
        for validator in self.validators:
            if isinstance(validator, EmailValidator):
                validator_found = True

        if not validator_found:
            self.validators.append(EmailValidator('Not a valid email address.'))


class TwoColumnDataParam(BaseParamConverter):
    @classmethod
    def convert(cls, value, parent_object):
        if value is None:
            return []
        elif isinstance(value, list):
            return value
        elif isinstance(value, QuerySet):
            fieldname_1 = value._fields[0]
            fieldname_2 = value._fields[1]
            return [(record[fieldname_1], record[fieldname_2]) for record in value]
        elif isinstance(value, Iterable) and not isinstance(value, str):
            return value

        raise TypeError("Parameter is not a list of tuples of a QuerySet with two columns")


class RadioField(BaseField):
    def __init__(self, name=None, radio_value='', description=None, value=Default, sub_section=None, **kwargs):
        super().__init__(name, value, **kwargs)
        self.radio_value = self.param(radio_value, StringParam, "The value for this radio button")
        self.description = self.param(description, ObjectsParam, "The description")
        self.sub_section = self.param(sub_section, ObjectsParam, "Control under this radiobutton that become visible when this radio is selected")

    def get_html(self, renderer):
        form = renderer.find_parent(Form)
        form.form_data['fld'][self.name] = {
            'cls': form.form_data_class(self.__class__),
            'valid': [(form.form_data_class(validator.__class__), validator.serialize()) for validator in self.validators]
        }

        if self.value == Default and form.data:
            try:
                field = form.data._meta.get_field(self.name)
                self.value = str(form.data.__getattribute__(self.name))
            except FieldDoesNotExist:
                pass

        self.add_class("radio")
        self.id_needed()
        self.add_attribute('data-hassection', "true" if self.sub_section else "")
        renderer.append('<div{}>'.format(self.base_attributes))
        renderer.append('    <label>')
        renderer.append('        <input{} type="radio" name="{}" value="{}" {}>'.format(
            self.base_attributes,
            self.name,
            self.radio_value,
            'checked' if self.radio_value == self.value else ''
        ))
        renderer.render('        ', self.description)
        renderer.append('    </label>')
        if self.sub_section:
            renderer.append('    <div id="{}"{}>'.format(
                self.id + "_section",
                ' style="display:none;"' if self.radio_value != self.value else ''
            ))
            renderer.render('        ', self.sub_section)
            renderer.append('    </div>')

            renderer.append_js("""
$('#""" + self.id + """').click(function() {
    $('#""" + self.id + """_section').slideDown()
})
            """)

        renderer.append('</div>')
        renderer.append_js("""
$("input[name='""" + self.name + """']").each(function () {
    if ((this.id != '""" + self.id + """') && this.dataset.hassection) {
        var section_id = '#' + this.id + '_section';
        $('#""" + self.id + """').click(function() {
            $(section_id).slideUp()
        })
    }
});
        """)


class DropDownField(BaseField):
    def __init__(self,  name=None, choices=None, label='', auto_focus=False,
                 help_text='', value=Default, **kwargs):
        super().__init__(name, value, **kwargs)
        self.choices = self.param(choices, ListParam, 'List of choices (value, name)')
        self.label = self.param(label, StringParam, 'Text of the label')
        self.auto_focus = self.param(auto_focus, BooleanParam, 'Place the focus on this element')
        self.help_text = self.param(help_text, StringParam, 'help text for the input field')
        self.add_class('form-control')

    @ensure_formgroup
    def get_html(self, renderer):
        renderer.append('<select' + self.base_attributes + ' name="{}">'.format(self.name))
        for choice in self.choices:
            renderer.append('<option value="{}"{}>{}</option>'.format(
                quote(choice[0]),
                ' selected="selected"' if self.value == str(choice[0]) else '',
                quote(choice[1])
            ))
        renderer.append('</select>')


class Submit(Object):
    def __init__(self, action='', **kwargs):
        self.init(kwargs)
        self.action = self.param(action, StringParam, 'Action to run when the form is submitted with this button')

    @ensure_formgroup
    def get_html(self, renderer):
        on_click = '$("#" + this.form.id + " .form-error").children().remove();'
        on_click += '$("#" + this.form.id).find("[name=sub_action]").attr("value", "{}");'.format(self.action)
        # on_click += 'send_action($(this.form).serialize());'
        on_click += '$(this.form).submit());'
        renderer.append('<button type="submit" class="btn btn-primary" onclick=\'{};return false;\'>Submit</button>'.format(on_click))
