# Copyright © 2021 odoo, LLC
# See LICENSE file for full copyright and licensing details.

from odoo.tools import formatLang


def format_currency(self, value):
    currency = self.env.company.currency_id
    return_value = formatLang(self.env, currency.round(value) + 0.0, currency_obj=currency)
    return return_value


def get_chart_element_config(name, dataset, color, order=0, chart_type='bar', **kwargs):
    """
    Get the configuration for rendering an element on the chart
    :param name: the name of the element
    :param dataset: the dataset for the element
    :param color: the color to fill on the element
    :param order: the order to draw on chart
    :param chart_type: the type of element to render
                    Options: bar, horizontalBar, line, radar, pie, doughnut,
                    polarArea, bubble, scatter, gauge, choropleth
    :param kwargs: backgroundColor (str), borderColor (str), borderWidth (float),
                    hoverBackgroundColor (str), hoverBorderColor (str), hoverBorderWidth (float),
                    xAxisID (str, to determine which x axis the element will be draw on),
                    xAxisID (str, to determine which y axis the element will be draw on),
                    fill (bool, Color the region limit by the border of the element)

    :return: a dictionary contains the configuration for the chart element
    """
    
    element_cfg = {
        'label': name or '',
        'data': isinstance(dataset, list) and dataset or [],
        'order': isinstance(order, int) and order or False,
        'type': chart_type or 'bar',
        'fill': False if chart_type == 'line' else True,
        'backgroundColor': color or '#00A09D',
        'borderColor': color or '#00A09D',
    }
    element_cfg.update(kwargs)
    return element_cfg


def get_chart_title_config(title='', display=True, position='top', **kwargs):
    """
    Get options for showing title of the chart
    :param title: str, the name of the chart
    :param display: bool, whether the chart will show title or not
    :param position: str, the place to put the legend, 4 options: top, bottom, left, right
    :param kwargs: padding (int, padding top and bottom), fontColor (str), fontStyle (str),
                    fontSize (float), fontFamily (str)
    :return: a dictionary contains the configuration for the chart title
    """
    title_cfg = {
        'display': title and display or False,
        'text': title,
        'position': position
    }
    title_cfg.update(kwargs)
    return title_cfg


def get_chart_legend_config(display=True, position='top', reverse=False, **kwargs):
    """
    Get options for showing legend of the chart
    :param display: bool, whether chart should show legend or not
    :param position: str, the place to put the legend, 4 options: top, bottom, left, right
    :param reverse: bool, whether the order of elements in the legend should be reversed
                    to the order when drawing or not
    :param kwargs: options for labels: usePointStyle (bool), fontColor (str), fontStyle (str), fontSize (float), fontFamily (str)
    :return: a dictionary contains the configuration for the chart legend
    """
    legend_cfg = {
        'display': display,
        'position': position,
        'reverse': reverse,
        'labels': kwargs
    }
    legend_cfg['labels'].update(kwargs)
    return legend_cfg


def get_chart_tooltip_config(display=True, display_mode='nearest', **kwargs):
    """
    Get options for showing tooltips of the chart
    :param display: bool, whether chart should show legend or not
    :param display_mode: str, the mode that the tooltips will be shown in.
                        6 options: point, nearest, index, dataset, x, y
    :param kwargs: backgroundColor (str), borderColor (str), borderWidth (float),
                    titleFontFamily (str), titleFontSize (float), titleFontStyle (str), titleFontColor (str),
                    bodyFontFamily (str), bodyFontSize (float), bodyFontStyle (str), bodyFontColor (str),
                    footerFontFamily (str), footerFontSize (float), footerFontStyle (str), footerFontColor (str)
    :return: a dictionary contains the configuration for the chart tooltips
    """
    tooltip_cfg = {
        'enabled': display,
        'mode': display_mode,
    }
    tooltip_cfg.update(kwargs)
    return tooltip_cfg


def get_chart_layout_config(padding_top=0, padding_right=0, padding_bottom=0, padding_left=0):
    """
    Get configuration for layout of the chart content
    :param padding_top: float, padding to top
    :param padding_right: float, padding to right
    :param padding_bottom: float, padding to bottom
    :param padding_left: float, padding to left
    :return: a dictionary contains the configuration for the chart layout
    """
    return {
        'padding': {
            'top': padding_top,
            'right': padding_right,
            'bottom': padding_bottom,
            'left': padding_left,
        }
    }


def get_chart_axis_config(display=True, axis_name='', display_grid=True,
                          stacked=False, circular=False, position='left', identification='', **kwargs):
    """
    Get configuration for an axis of the chart content
    :param display: bool, whether the axis should be shown or not
    :param display_grid: bool, whether the grid lines should be shown or not
    :param stacked: bool, whether the axis values should be stacked
    :param circular: bool, true for radar chart
    :param kwargs: beginAtZero (bool, whether the axis should begin from 0),
                    min (float), max (float), minRotation (float), maxRotation (float)
    :return:
    """
    axis_cfg = {
        'display': display,
        'stacked': stacked,
        'circular': circular,  # true for radar, otherwise it's false
        'ticks': kwargs,
        'position': position,
        'gridLines': {
            'display': display_grid,
        },
    }
    if identification:
        axis_cfg['id'] = identification
    if axis_name:
        axis_cfg['scaleLabel'] = {
            'display': True,
            'labelString': axis_name,
        }
    return axis_cfg


def get_chart_config(chart_type='bar', chart_title='', datasets={}, colors=[], axis_labels=[], stacked=False):
    """
    Get normal configuration for rendering chart
    :param chart_type: str, type of chart.
            Options: bar, horizontalBar, line, radar, pie, doughnut,
                    polarArea, bubble, scatter, gauge, choropleth
    :param chart_title: str, Title of the chart
    :param datasets: dict, format: {element_name_1: list of element 1 data, element_name_2: list of element 2 data,...}
    :param colors: list of str, list of color for each element
    :param axis_labels: list of str, labels for displaying on the axis
    :param stacked: bool, whether the axes should be stacked or not
    :return: dict contains configuration for rendering chart
    """
    # if chart_type == 'bar':
    ele_cfgs = []
    color_index = 0
    for name, dataset in datasets.items():
        color = colors and colors[color_index % len(colors)] or '#00A09D'
        ele_cfgs.append(get_chart_element_config(name, dataset, color, chart_type=chart_type))
        color_index += 1
    title_cfg = get_chart_title_config(chart_title)
    legend_cfg = get_chart_legend_config()
    tooltip_cfg = get_chart_tooltip_config()
    x_axis = get_chart_axis_config(stacked=stacked)
    y_axis = get_chart_axis_config(stacked=stacked)
    chart_config = get_chart_config_from(chart_type=chart_type, element_configs=ele_cfgs,
                                         title_config=title_cfg, legend_config=legend_cfg,
                                         tooltip_config=tooltip_cfg, x_axis_configs=x_axis,
                                         y_axis_configs=y_axis, axis_labels=axis_labels)
    return chart_config


def get_chart_config_from(chart_type='bar', element_configs=[], title_config={}, legend_config={}, tooltip_config={},
                          layout_config={}, x_axis_configs=[], y_axis_configs=[], axis_labels=[]):
    """
    Get configuration for rendering chart
    :param chart_type: chart_type: str, type of chart.
            Options: bar, horizontalBar, line, radar, pie, doughnut,
                    polarArea, bubble, scatter, gauge, choropleth
    :param element_configs: list of dict, see format of dict: get_chart_element_config
    :param title_config: dict, see format: get_chart_title_config
    :param legend_config: dict, see format: get_chart_legend_config
    :param tooltip_config: dict, see format: get_chart_tooltip_config
    :param layout_config: dict, see format: get_chart_layout_config
    :param x_axis_configs: list of dict, contains x axes, see dict format: get_chart_axis_config
    :param y_axis_configs: list of dict, contains y axes, see dict format: get_chart_axis_config
    :param axis_labels: list of str, contains labels for displaying on the axis
    :return: dict contains configuration for rendering chart
    """
    scale_config = {}
    if x_axis_configs or y_axis_configs:
        scale_config = {
            'scales': {
                'xAxes': isinstance(x_axis_configs, list) and x_axis_configs or [x_axis_configs],
                'yAxes': isinstance(y_axis_configs, list) and y_axis_configs or [y_axis_configs],
            }
        }
    config = {
        'type': chart_type,
        'data': {
            'labels': axis_labels,
            'datasets': element_configs,
        },
        'options': {
            'title': title_config or get_chart_title_config(),
            'legend': legend_config or get_chart_legend_config(),
            'tooltips': tooltip_config or get_chart_tooltip_config(),
            'layout': layout_config or get_chart_layout_config(),
            'maintainAspectRatio': False,
        },
    }
    config['options'].update(scale_config)
    return config


def get_geo_chart_config(values, geo_data={}, mode='albersUsa'):
    if not values:
        values = []
    return {
        'type': 'choropleth',
        'values': values,
        'mode': mode,
        'geoData': geo_data
    }
