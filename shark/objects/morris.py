from django.db.models import Model
from shark.base import Object, Default, StringParam
from shark.param_converters import ListParam, CssAttributeParam, DataTableParam


class Graph(Object):
    """
    Easy rendering of graphs using the Morris library. Currently only supports line graphs, more to be added.
    """
    def __init__(self, data=Default, x_column='', y_columns=Default, width='100%', height='250px', **kwargs):
        self.init(kwargs)
        self.data = self.param(data, DataTableParam, 'The dataset')
        self.x_column = self.param(x_column, StringParam, 'Name of the x column in the data')
        self.y_columns = self.param(y_columns, ListParam, 'Name of the y columns in the data', [])
        self.width = self.param(width, CssAttributeParam, 'Graph width')
        self.height = self.param(height, CssAttributeParam, 'Graph height')
        self.id_needed()

    def get_html(self, renderer):
        renderer.add_resource('//cdnjs.cloudflare.com/ajax/libs/raphael/2.1.0/raphael-min.js', 'js', 'morris', 'raphael')
        renderer.add_resource('//cdnjs.cloudflare.com/ajax/libs/morris.js/0.5.1/morris.min.js', 'js', 'morris', 'main')
        renderer.add_resource('//cdnjs.cloudflare.com/ajax/libs/morris.js/0.5.1/morris.css', 'css', 'morris', 'main')

        data_points = []
        series_names = set()

        field_column_map = {field_name: i for i, field_name in enumerate(self.data[0])}

        for row in self.data[1]:
            x_value = row[field_column_map[self.x_column]]

            values = ''
            series_name = 'a'
            for y_column in self.y_columns:
                series_names.add(series_name)
                #TDOD: Escape data for output
                values += ',' + series_name + ':"' + str(row[field_column_map[y_column]]) + '"'
                series_name = chr(ord(series_name) + 1)

            data_points.append('{x:"' + str(x_value) + '"' + values + '}')

        renderer.append('<div id="' + self.id + '" style="height:' + self.height + ';width:' + self.width + ';"></div>')
        renderer.append_js("""
                Morris.Line({
                    element: '""" + self.id + """',
                    data: [""" + ','.join(data_points) + """],
                    xkey: 'x',
                    ykeys: [""" + ', '.join(["'" + series_name + "'" for series_name in series_names]) + """],
                    labels: [""" + ', '.join(["'" + series_name + "'" for series_name in series_names]) + """],
                    pointSize: 0,
                    smooth: true,
                    hideHover: true,
                    xLabelAngle: 45,
                    axes: true,
                    grid: true
                    });
            """)

    @classmethod
    def example(self):
        data = [
            {'year': 2011, 'wheat': 10.4, 'corn': 14.2},
            {'year': 2012, 'wheat': 8.2, 'corn': 12.4},
            {'year': 2013, 'wheat': 9.8, 'corn': 7.2},
            {'year': 2014, 'wheat': 14.2, 'corn': 8.4},
            {'year': 2015, 'wheat': 14.0, 'corn': 12.3}
        ]
        return Graph(data, 'year', ['wheat', 'corn'])
