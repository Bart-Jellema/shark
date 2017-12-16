from collections import Iterable
from django.db.models import Model

from shark.base import Enumeration, Object, Default, Objects, StringParam
from shark.param_converters import ObjectsParam, UrlParam, IntegerParam


class TableStyle(Enumeration):
    default = 0
    striped = 1
    bordered = 2
    hover = 3
    condensed = 4


class TableContextualStyle(Enumeration):
    default = 0
    active = 1
    success = 2
    info = 3
    warning = 4
    danger = 5


class Table(Object):
    """
    Creates the table element.

    You can construct tables out of all the elements, but more commonly you would use the create_table shortcut.
    """
    def __init__(self, head=None, rows=Default, table_style=None, **kwargs):
        self.init(kwargs)
        self.head = self.param(head, TableHead, 'Table Header')
        self.rows = self.param(rows, ObjectsParam, 'Rows in the table', Objects())
        self.table_style = self.param(table_style, TableStyle, 'Style for the table')
        self.add_class('table')
        if isinstance(self.table_style, str):
            self.add_class('table-' + self.table_style)
        elif isinstance(self.table_style, Iterable):
            for s in self.table_style:
                if not s == TableStyle.default:
                    self.add_class('table-' + TableStyle.name(s))
        elif isinstance(self.table_style, int):
            if not self.table_style == TableStyle.default:
                self.add_class('table-' + TableStyle.name(self.table_style))

    def get_html(self, html):
        html.append('<table' + self.base_attributes + '>')
        html.render('    ', self.head)
        html.append('    <tbody>')
        html.render('    ', self.rows)
        html.append('    </tbody>')
        html.append('</table>')

    @classmethod
    def example(cls):
        return Table(
            TableHead([
                TableHeadColumn('Jedi'),
                TableHeadColumn('Action'),
                TableHeadColumn('Outcome')
            ]), [
                TableRow([
                    TableColumn('Luke'),
                    TableColumn('Try'),
                    TableColumn('Fail')
                ]),
                TableRow([
                    TableColumn('Yoda'),
                    TableColumn('Do'),
                    TableColumn('Success')
                ])
            ]
        )

class TableHead(Object):
    def __init__(self, columns=Default, **kwargs):
        self.init(kwargs)
        self.columns = self.param(columns, ObjectsParam, 'Columns in the table', Objects())

    def get_html(self, html):
        html.append('<thead ' + self.base_attributes + '><tr>')
        html.render('    ', self.columns)
        html.append('</tr></thead>')


class TableHeadColumn(Object):
    def __init__(self, items=Default, colspan=0, rowspan=0, **kwargs):
        self.init(kwargs)
        self.items = self.param(items, ObjectsParam, 'Content of the column', Objects())
        self.colspan = self.param(colspan, StringParam, 'Columns the cell spans')
        self.rowspan = self.param(rowspan, StringParam, 'Rows the cell spans')

        self.add_attribute('colspan', self.colspan)
        self.add_attribute('rowspan', self.rowspan)

    def get_html(self, html):
        html.append('<th' + self.base_attributes + '>')
        html.render('    ', self.items)
        html.append('</th>')


class TableRow(Object):
    def __init__(self, columns=Default, action=None, **kwargs):
        self.init(kwargs)
        self.columns = self.param(columns, ObjectsParam, 'Columns in the table', Objects())
        self.url = self.param(action, UrlParam, 'Action to do when clicked')

    def get_html(self, html):
        data_href = ' data-href="{}"'.format(self.url) if self.url else ''
        html.append('<tr' + self.base_attributes + data_href + '>')
        html.render('    ', self.columns)
        html.append('</tr>')


class TableColumn(Object):
    def __init__(self, items=Default, colspan=0, rowspan=0, align='', **kwargs):
        self.init(kwargs)
        self.items = self.param(items, ObjectsParam, 'Content of the column', Objects())
        self.colspan = self.param(colspan, IntegerParam, 'Span number of columns')
        self.rowspan = self.param(rowspan, IntegerParam, 'Span number of rows')
        self.align = self.param(align, StringParam, 'Align left, right or center')

        if self.colspan:
            self.add_attribute('colspan', self.colspan)
        if self.rowspan:
            self.add_attribute('rowspan', self.rowspan)
        if self.align:
            self.add_style('text-align: {};'.format(self.align))

    def get_html(self, html):
        html.append('<td' + self.base_attributes + '>')
        html.render('    ', self.items)
        html.append('</td>')



def create_table(data, columns, transforms = None, include_header = True, row_actions = None, table_style = None):
    transforms = transforms or []
    table = Table(table_style=table_style)
    if data:
        if include_header:
            table.head = TableHead()

        field_names = []
        for column_name in columns:
            if '=' in column_name:
                column_name, field_name = column_name.split('=')
            else:
                field_name = column_name
            field_names.append(field_name)

            if include_header:
                table.head.columns.append(TableHeadColumn(column_name))

        if len(data)>0 and isinstance(data[0], Model):
            in_function = lambda row: dir(row)
            get_function = lambda row, key: row.__getattribute__(key)
        else:
            in_function = lambda row:row
            get_function = lambda row, key: row[key]

        for row in data:
            if row_actions:
                table_row = TableRow(action=row_actions(row))
            else:
                table_row = TableRow()

            for field_name in field_names:
                if field_name in transforms:
                    table_row.columns.append(TableColumn(transforms[field_name](row)))
                elif field_name.lower() in in_function(row):
                    value = get_function(row, field_name.lower())
                    if value is None:
                        value = ''
                    if not isinstance(value, str):
                        value = str(value)
                    table_row.columns.append(TableColumn(value))
            table.rows.append(table_row)

    return table
