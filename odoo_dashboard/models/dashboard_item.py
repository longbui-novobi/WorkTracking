# Copyright © 2021 odoo, LLC
# See LICENSE file for full copyright and licensing details.

from re import search
from threading import Thread
from logging import fatal, getLogger
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, registry, SUPERUSER_ID, _
from odoo.tools.float_utils import float_compare, float_is_zero
from odoo.exceptions import ValidationError, UserError
from ..utils.date_time_util import _get_date_period, _get_last_period, _get_date_group_by
from ..utils.image_processing import image_path_2_base64, find_vacancy_area
from ..utils.item_util import get_default_item_size, get_db_field_type
from ..utils.graph_config import get_chart_element_config, get_chart_title_config, get_chart_legend_config, \
    get_chart_config_from, get_chart_axis_config, get_chart_tooltip_config
from ..utils.color_util import get_team_color, get_team_demo_color
from ..utils.filter_config import detect_target
from ..utils.generate_table_demo import get_demo_data_for_custom_list_item
import datetime
import json
import random
from ast import literal_eval

_logger = getLogger(__name__)


class DashboardItem(models.Model):
    _name = "bi.dashboard.item"
    _description = "Dashboard Item"
    name = fields.Char(string='Name', required=True)
    board_ids = fields.Many2many('bi.dashboard.board', 'dashboard_board_item_rel', 'item_id', 'board_id',
                                 string="Dashboard Boards")
    width = fields.Float(string="Width", default=3, required=True)
    height = fields.Float(string="Height", default=3, required=True)
    min_width = fields.Float(string="Min Width", default=3, required=True)
    min_height = fields.Float(string="Min Height", default=3, required=True)
    x_position = fields.Float(string="X Coordination", default=0)
    y_position = fields.Float(string="Y Coordination", default=0)
    compute_function = fields.Char(string="Computed Function")
    active = fields.Boolean(string='Active?', default=True)
    kpi_img_src = fields.Char(string="KPI Image Source")
    kpi_img_b64 = fields.Binary(string="KPI Image", attachment=True)
    kpi_show_indicator = fields.Boolean(string='Show Trend Indicator?', default=True)
    format_style = fields.Selection(string="Display Unit",
                                    selection=[('currency', 'Currency'),
                                               ('decimal', 'Number'),
                                               ('percent', 'Percent'),
                                               ('custom', 'Other')
                                               ], default='decimal')
    custom_unit_style = fields.Char(string='Custom Unit', size=7)
    x_axes_format_style = fields.Selection(string="X-axes Unit",
                                           selection=[('decimal', 'Numeric'), ('currency', 'Currency'),
                                                      ('percent', 'Percent')])
    y_axes_format_style = fields.Selection(string="Y-axes Unit",
                                           selection=[('decimal', 'Numeric'), ('currency', 'Currency'),
                                                      ('percent', 'Percent')], default='decimal')
    description = fields.Text(string="Description")
    filter_config = fields.Text(string="Filter Configuration", default="{}")
    layout_template = fields.Selection(string='Type',
                                       selection=[('kpi', 'KPI Item'),
                                                  ('chart', 'Chart Item'),
                                                  ('mixed', 'Mixed Item'),
                                                  ('gauge_mixed', 'Gauge Item'),
                                                  ('list', 'List')], required=True)
    code = fields.Char(string='Code')
    allowed_user_ids = fields.Many2many('res.users', 'bi_dashboard_item_allowed_users', 'item_id', 'user_id',
                                        string='Allowed Users', compute='_compute_allowed_user_ids', store=True)
    # Fields for custom items
    summarized_table = fields.Char(string='Summarized Table', readonly=True)
    created_on_ui = fields.Boolean(string='Create On UI?', default=False)
    model_id = fields.Many2one('ir.model', string='Model',
                               domain="""[('transient', '=', False)]""")
    model_name = fields.Char(string='Model Name', related='model_id.model')
    measure_type = fields.Selection(string='Aggregate Method',
                                    selection=[('sum', 'Sum'),
                                               ('avg', 'Average'),
                                               ('count', 'Count'),
                                               ('min', 'Min'),
                                               ('max', 'Max'),
                                               ])
    date_field_id = fields.Many2one('ir.model.fields', string='Date Field',
                                    domain="""[('model_id', '=', model_id), ('store', '=', True),
                                            ('ttype', 'in', ['date', 'datetime'])
                                            ]""")
    # Field for KPI Item
    kpi_field_id = fields.Many2one('ir.model.fields', string='Measure Field',
                                   domain="""[('model_id', '=', model_id), ('store', '=', True),
                                            ('ttype', 'in', ['float', 'integer', 'monetary']),
                                            ('name', 'not in', ['id', 'active']),
                                            ]""")
    green_on_positive = fields.Boolean(string='Is Growth Good When Positive?', default=True)
    # Field for Chart Item
    chart_type = fields.Selection(string='Chart Type',
                                  selection=[
                                      ('line', 'Line Chart'),
                                      ('bar', 'Bar Chart'),
                                      ('pie', 'Pie Chart'),
                                      ('doughnut', 'Doughnut Chart'),
                                      ('polarArea', 'Polar Area Chart'),
                                      ('radar', 'Radar Chart')
                                  ])
    chart_field_ids = fields.Many2many('ir.model.fields',
                                       'bi_dashboard_item_chart_field_rel', 'item_id', 'field_id',
                                       string='Measure Fields',
                                       domain="""[('model_id', '=', model_id), ('store', '=', True),
                                            ('ttype', 'in', ['float', 'integer', 'monetary']),
                                            ('name', 'not in', ['id', 'active']),
                                            ]""")
    group_field_ids = fields.Many2many('ir.model.fields',
                                       'bi_dashboard_item_group_field_rel', 'item_id', 'field_id',
                                       string='Group By',
                                       domain="""[('model_id', '=', model_id), ('store', '=', True),
                                                ('ttype', 'not in', ['html', 'binary', 'boolean', 'many2one_reference',
                                                            'reference', 'many2many', 'one2many', 'job_serialized']),
                                                ('name', 'not in', ['id', 'active']),
                                                ]""")
    order_field_ids = fields.Many2many('ir.model.fields',
                                       'bi_dashboard_item_order_field_rel', 'item_id', 'field_id',
                                       string='Order By',
                                       domain="""[('model_id', '=', model_id), ('store', '=', True),
                                                ('ttype', 'not in', ['html', 'binary', 'boolean', 'many2one_reference',
                                                            'reference', 'many2many', 'one2many', 'job_serialized']),
                                                    ('name', 'not in', ['id', 'active']),
                                                    ]""")
    order_method = fields.Selection(string='Sort Order', selection=[('asc', 'Ascending'), ('desc', 'Descending')])
    item_domain = fields.Char(string="Domain")
    preview = fields.Integer(default=1, string="Item Preview")
    is_show_target = fields.Boolean(string='Show Target Value?', default=False)

    target_kpi_ids = fields.One2many('bi.dashboard.item.target', 'dashboard_item_id', string='Target List')

    list_field_ids = fields.One2many('bi.dashboard.item.custom.list', 'dashboard_item', string='List view options')
    list_pin_ids = fields.Text(string='List pinned', default='[]')

    @api.depends('board_ids', 'board_ids.allowed_user_ids', 'board_ids.allowed_group_ids',
                 'board_ids.allowed_group_ids.users')
    def _compute_allowed_user_ids(self):
        managers = self.env.ref('odoo_dashboard_builder.dashboard_group_manager').users
        for item in self:
            item.allowed_user_ids = item.board_ids.allowed_user_ids + item.board_ids.allowed_group_ids.users + \
                                    item.create_uid + managers

    @api.onchange('layout_template')
    def _onchange_layout_template(self):
        for item in self:
            default_size = get_default_item_size(item.layout_template)
            size_dimensions = ['width', 'height', 'min_width', 'min_height']
            for dimension in size_dimensions:
                setattr(item, dimension, default_size.get(dimension, 3))

    @api.onchange('model_id', 'layout_template')
    def _onchange_model_id(self):
        for item in self:
            # Reset selected fields
            item.kpi_field_id = False
            item.date_field_id = False
            item.group_field_ids = False
            item.chart_field_ids = False
            item.order_field_ids = False
            item.item_domain = ""

    @api.onchange('date_field_id', 'group_field_ids', 'chart_field_ids')
    def _onchange_order_fields(self):
        for item in self:
            available_fields = item.chart_field_ids | item.group_field_ids
            item.order_field_ids = item.order_field_ids.filtered(lambda i: i in available_fields)

    def generate_item_config(self, board_config_id, user_id=False):
        self.ensure_one()
        config_env = self.env['bi.dashboard.item.config']
        if board_config_id:
            item_config = config_env.sudo().search([('item_id', '=', self.id),
                                                    ('board_config_id', '=', board_config_id),
                                                    ('user_id', '=', user_id)], limit=1)
            if not item_config:
                item_config = config_env.sudo().create({
                    'user_id': user_id,
                    'item_id': self.id,
                    'board_config_id': board_config_id,
                    'filter_config': self.filter_config,
                    'active': True,
                    'x_position': self.x_position,
                    'y_position': self.y_position,
                    'width': self.width,
                    'height': self.height
                })
            return item_config
        return config_env

    def get_dashboard_item_config(self):
        item_config = {
            "id": self.id,
            "template": self.layout_template,
            "kpi_icon": self.kpi_img_b64,
            "layoutConfig": {
                'x': self.x_position,
                'y': self.y_position,
                'width': self.width,
                'height': self.height,
                'min_width': self.min_width,
                'min_height': self.min_height,
            },
            'filter': {},
            'info': {
                'title': self.name,
                'description': self.description,
            },
        }
        return item_config

    @api.model
    def get_dashboard_item_preview_layout_config(self, vals, model):
        if vals.get('id'):
            record = self.env[model].browse(vals['id'])
            if vals.get('layout_template') == record.layout_template:
                return record.get_dashboard_item_config()

        item_config = {
            "id": -1,
            "template": vals.get('layout_template', 'kpi'),
            'kpi_icon': vals.get('kpi_img_b64', ''),
            'layoutConfig': {
                'x': vals.get('x_position'),
                'y': vals.get('y_position'),
                'width': vals.get('width'),
                'height': vals.get('height'),
                'min_width': vals.get('min_width'),
                'min_height': vals.get('min_height'),
            },
            'filter': {},
            'info': {
                'title': vals.get('name', ''),
                'description': vals.get('description', ''),
            },
        }
        return item_config

    @api.model
    def get_preview_data(self, vals, filter_configs, editing):
        record = self.new(vals)
        if vals.get('layout_template') != 'kpi':
            data = record.get_data({"period": "preview", 'team': 0})
        else:
            return record.format_kpi_data(random.random() * 100, random.random() * 100, filter_configs)
        if data.get('kpiConfig', False):
            data['kpiConfig'] = record.format_kpi_data(random.random() * 100, random.random() * 100, filter_configs)
        return data

    @api.model
    def get_sales_team(self):
        query_stmt = """
                SELECT id, name
                FROM crm_team
                WHERE company_id={} OR company_id IS NULL
                ORDER BY id asc;
            """.format(self.env.company.id)
        self.env.cr.execute(query_stmt)
        team_dict = self.env.cr.dictfetchall()
        teams = {team['id']: team.get('name', '') for team in team_dict}
        teams.update({0: 'All Teams'})
        return teams

    @api.model
    def get_locations(self):
        # TODO: Get actual locations
        return {
            'world': 'World',
            "usa": "USA",
        }

    @api.model
    def action_controller(self, configs, extend):
        if 'action_type' not in configs:
            return False
        item_config = self.env['bi.dashboard.item.config'].browse(configs.get('config_id'))
        board_id = configs.get('new_board_id', False)
        board = board_id and self.env['bi.dashboard.board'].browse(board_id) or False
        board_config = board and board.get_dashboard_board_config(self.env.user.id).id or False
        item_config = getattr(self, 'action_%s' % configs['action_type'].lower())(item_config, board_config,
                                                                                  extend)
        is_remove = False
        if configs['action_type'].lower() in ['drop', 'move']:
            is_remove = True
        return [is_remove, item_config]

    # @api.model
    # def map_feature(self, board_config_id):
    #     board_config = self.env['bi.dashboard.board.config'].browse(board_config_id)
    #     items = []
    #     x_max = 0
    #     y_max = 0
    #     # TODO: In the future, if we save the grid we can optimize next following code.
    #     for item_config in board_config.board_item_config_ids:
    #         items.append({
    #             'x': int(item_config.x_position),
    #             'y': int(item_config.y_position),
    #             'w': int(item_config.width),
    #             'h': int(item_config.height)
    #         })
    #         horizon = item_config.x_position + item_config.width
    #         if horizon > x_max:
    #             x_max = horizon
    #         vertical = item_config.y_position + item_config.height
    #         if vertical > y_max:
    #             y_max = vertical
    #     extend = {
    #         "items": items,
    #         "columns": int(x_max),
    #         "rows": int(y_max)
    #     }
    #     return extend

    @api.model
    def get_new_position(self, item_config, target_board_id, extend):
        # TODO: Find available space to place the item
        # if not extend:
        #     extend = self.map_feature(target_board_id)
        # position_x, position_y = find_vacancy_area(extend, [item_config.width, item_config.height])
        position_x, position_y = 0, 10000
        return position_x, position_y

    @api.model
    def action_add(self, item_config_id, target_board_id, extend):
        if item_config_id and target_board_id:
            position_x, position_y = self.get_new_position(item_config_id, target_board_id, extend)
            item_config_id.copy({
                'board_config_id': target_board_id,
                'x_position': position_x,
                'y_position': position_y
            })
        return False

    @api.model
    def action_duplicate(self, item_config_id, target_board_id, extend):
        if item_config_id and target_board_id:
            position_x, position_y = self.get_new_position(item_config_id, target_board_id, extend)
            res = item_config_id.copy({
                'board_config_id': target_board_id,
                'x_position': position_x,
                'y_position': position_y
            })
            config = res.get_dashboard_item_config()
            return config
        return False

    @api.model
    def action_move(self, item_config_id, target_board_id, extend):
        if item_config_id and target_board_id:
            position_x, position_y = self.get_new_position(item_config_id, target_board_id, extend)
            item_config_id.write({
                'board_config_id': target_board_id,
                'x_position': position_x,
                'y_position': position_y})
        return False

    @api.model
    def action_drop(self, item_config_id, extend):
        item_config_id.action_archive()
        return False

    # DATA QUERY
    def get_data(self, filters={}, config_id=None):
        self.ensure_one()
        period = filters.get('period', '')
        if not getattr(self, self.compute_function, False) or not period:
            raise ValidationError(_('Cannot load the value for {}'.format(self.name)))
        start_date = end_date = None
        if period == 'custom_period' and isinstance(config_id, int):
            item_config = self.env['bi.dashboard.item.config'].sudo().browse(config_id)
            start_date = item_config.board_config_id.custom_start_date
            end_date = item_config.board_config_id.custom_end_date
        if period == 'preview':
            start_date = datetime.date.today() + relativedelta(years=100)
            end_date = start_date + relativedelta(weeks=1)
        if not start_date or not end_date:
            start_date, end_date = _get_date_period(self, period)
        data = {}
        if self.layout_template == 'kpi':
            data = self.get_kpi_data(start_date, end_date, filters=filters)
        elif self.layout_template == 'chart':
            data = self.get_chart_data(start_date, end_date, filters=filters)
        elif self.layout_template == 'mixed':
            data = self.get_mixed_chart_data(start_date, end_date, filters=filters)
        elif self.layout_template == 'gauge_mixed':
            data = self.get_mixed_chart_data(start_date, end_date, filters=filters)
        elif self.layout_template == 'list':
            data = self.get_list_data(start_date, end_date, filters=filters)
        return data

    def get_kpi_data(self, start_date, end_date, filters={}):
        if hasattr(self, self.compute_function):
            method = getattr(self, self.compute_function)
            last_start_date, last_end_date = _get_last_period(start_date, end_date, filters['period'])
            current_value = method(start_date, end_date, filters=filters)
            last_value = method(last_start_date, last_end_date, filters=filters) if self.kpi_show_indicator else 0
            return self.format_kpi_data(current_value, last_value, filters)
        return self.format_kpi_data(0.0, 0.0, filters)

    def get_chart_data(self, start_date, end_date, filters={}):
        if hasattr(self, self.compute_function):
            method = getattr(self, self.compute_function)
            chart_config = method(start_date, end_date, filters=filters)
            """
            chart_config: <<dictionary>> {
                additional_info: [ ->> optional
                    {
                        'title: ->> title of each tooltip,
                        'content: ->> content of each tooltip,
                        'format_style: ->> style to format the number: decimal, percent, currency,
                        'key: ->> provide key for the tooltip clickable
                    },...
                ],
                chart_config: {...} 
            },
            """
            additional_info = []
            if 'additional_info' in chart_config:
                additional_info = chart_config.pop('additional_info', {})
            return {
                'currency': self.env.company.currency_id.name,
                'chart_config': chart_config,
                'additional_info': additional_info,
                'format_style': self.format_style,
                'x_axes_format_style': self.x_axes_format_style,
                'y_axes_format_style': self.y_axes_format_style,
                'custom_unit': self.custom_unit_style
            }
        return {
            'currency': self.env.company.currency_id.name,
            'chart_config': {},
            'format_style': self.format_style,
            'x_axes_format_style': self.x_axes_format_style,
            'y_axes_format_style': self.y_axes_format_style,
            'custom_unit': self.custom_unit_style
        }

    def get_mixed_chart_data(self, start_date, end_date, filters={}):
        if hasattr(self, self.compute_function):
            method = getattr(self, self.compute_function)
            last_start_date, last_end_date = _get_last_period(start_date, end_date, filters['period'])
            current_value, chart_config = method(start_date, end_date, filters=filters)
            last_value, old_chart_config = method(last_start_date, last_end_date, filters=filters)
            kpi_config = self.format_kpi_data(current_value, last_value, filters)
        else:
            kpi_config = self.format_kpi_data(0.0, 0.0, filters)
            chart_config = {}
        return {
            'currency': self.env.company.currency_id.name,
            'kpiConfig': kpi_config,
            'chartConfig': chart_config,
            'format_style': self.format_style,
            'x_axes_format_style': self.x_axes_format_style,
            'y_axes_format_style': self.y_axes_format_style,
            'custom_unit': self.custom_unit_style
        }

    def format_kpi_data(self, current_value, last_value, filters={}):
        self.ensure_one()
        # Inherit this method and pass is good value if needed
        change_value = current_value - last_value
        change_value_percent = 0
        is_increase = float_compare(change_value, 0, precision_digits=4) >= 0
        if not float_is_zero(last_value, precision_digits=4):
            change_value_percent = change_value / last_value
        is_target, target_value = (detect_target(self, filters) if self.is_show_target else (False, 0))
        return {
            'thisPeriodValue': current_value,
            'lastPeriodValue': last_value,
            'trend': is_increase and 'increase' or 'decrease',
            'changeValue': change_value,
            'changeValuePercent': change_value_percent,
            'isGood': is_increase == self.green_on_positive or False,
            'formatStyle': self.format_style,
            'currency': self.env.company.currency_id.name,
            'showIndicator': self.kpi_show_indicator or False,
            'custom_unit': self.custom_unit_style,
            'isTarget': is_target,
            'target': target_value
        }


    def _get_sales_team_filter(self, team_id):
        if team_id and int(team_id):
            return 'team_id', 'team_id = {}'.format(team_id), 'team_id'
        return '', '', ''

    def get_list_data(self, start_date, end_date, filters):
        data = json.loads(self.filter_config).get('range')
        offset, limit = list(map(int, data.split('-'))) if data and len(data) > 1 else 0, 30
        if filters.get('period') == 'preview':
            compute_content = {
                'content': [],
                'options': {
                    'maximum': 0
                }
            }
        else:
            range_filter = filters.get('range', False)
            if range_filter:
                split_data = range_filter.split('-')
                if len(split_data) == 2:
                    offset = int(split_data[0]) - 1
                    limit = int(split_data[1]) - offset
            filters['offset'] = offset
            filters['limit'] = limit
            compute_content = getattr(self, self.compute_function)(start_date, end_date, filters)
        return self.format_list_data(compute_content, filters)


    def format_list_data(self, content, filters={}):
        column_visible = content['options'].get('visible_columns', False)
        list_field_ids = self.list_field_ids.sorted(key='sequence')
        if self.created_on_ui:
            if column_visible and len(column_visible) > 0:
                list_field_ids = list_field_ids.filtered(lambda x: x.field.name in column_visible)
            header = list_field_ids.field.mapped(lambda x: x.field_description)
            field = list_field_ids.field.mapped(lambda x: x.name)
            model_id = self.model_id.model
            ttype = {field.field.name: self._extract_ttype_from_field(field) for field in list_field_ids}
            external = {field.field.name: field.is_trigger_open for field in list_field_ids}
        else:
            if column_visible and len(column_visible) > 0:
                list_field_ids = list_field_ids.filtered(lambda x: x.field_raw in column_visible)
            header = list_field_ids.mapped(lambda x: x.field_name)
            field = list_field_ids.mapped(lambda x: x.field_raw)
            model_id = False
            ttype = {field.field_raw: self._extract_ttype_from_raw_field(field) for field in list_field_ids}
            external = {field.field_raw: field.is_trigger_open for field in list_field_ids}
        if content['options'].get('maximum', -1) == 0:
            content = get_demo_data_for_custom_list_item(self, ttype)
        res = {
            'model_id': model_id,
            'head': header,
            'field': field,
            'type': ttype,
            'external': external
            }
        res.update(content)
        return res

    @api.model
    def get_action_list_2_form(self, record_json):
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': record_json['model_id'],
            'views': [[False, 'form']],
            'res_id': record_json.get('record_id', -1), #Doing nothing if res_id = -1 when call from do_action
            'target': 'current'
        }

    # CUSTOM KPIs
    def get_data_for_custom_item(self, start_date, end_date, filters={}):
        self.ensure_one()
        method = 'get_data_for_custom_{}_item'.format(self.layout_template)
        if hasattr(self, method):
            return getattr(self, method)(start_date, end_date, filters)

    def query_data_for_custom_item(self, start_date, end_date, filters={}):
        """
                Get data for custom KPIs
                :param start_date: start date of the selected period
                :param end_date: end date of the selected period
                :param filters: board/item filter values
                :return: value of KPI for the period
                """
        # Return empty list to trigger mock data in the preview mode
        if filters.get('period', '') == 'preview':
            return []
        # Query real data
        self.ensure_one()
        if not self.model_id or not (self.kpi_field_id or self.chart_field_ids) or not self.summarized_table:
            raise ValidationError(_('Cannot load the value for {}'.format(self.name)))
        where_stmt = ""
        join_time_stmt = ""
        join_condition = ""
        time_table_field = 'date_field_ref'
        method = self.measure_type or 'sum'
        order_method = self.order_method or 'asc'
        measure_fields = self.kpi_field_id | self.chart_field_ids
        select_fields = []
        group_by_fields = []
        order_fields = []
        if self.date_field_id:
            where_stmt = """WHERE {field}::date >= '{start_date}'
                                        AND {field}::date <= '{end_date}'""".format(field=self.date_field_id.name,
                                                                                    start_date=start_date,
                                                                                    end_date=end_date)
        if 'company_id' in self.env[self.model_id.model]._fields:
            company_filter = "(company_id = {} or company_id IS NULL)".format(self.env.company.id)
            where_stmt = where_stmt and where_stmt + " AND {}".format(company_filter) or \
                         "WHERE {}".format(company_filter)
        for field in measure_fields:
            if method == 'avg':
                select_fields.append("COALESCE(sum({field})/COALESCE(sum(count), 1), 0) as {field}".format(
                    field=field.name))
            elif method == 'count':
                select_fields.append("COALESCE(sum({field}), 0) as {field}".format(field=field.name))
            else:
                select_fields.append(
                    "COALESCE({method}({field}), 0) as {field}".format(method=method, field=field.name))
        for field in self.group_field_ids.filtered(lambda f: f != self.date_field_id and f not in measure_fields):
            if field.ttype == 'datetime' or field.ttype == 'date':
                field_select_stmt, field_group_stmt, field_order_stmt = \
                    _get_date_group_by(self, filters.get('periodical', 'day'), field.name)
                select_fields.append(field_select_stmt)
                group_by_fields.append(field_group_stmt)
            else:
                select_fields.append(field.name)
                group_by_fields.append(field.name)
        for field in self.order_field_ids.filtered(lambda f: f != self.date_field_id):
            if field.ttype == 'datetime' or field.ttype == 'date':
                field_select_stmt, field_group_stmt, field_order_stmt = \
                    _get_date_group_by(self, filters.get('periodical', 'day'), field.name, order=order_method)
                order_fields.append(field_order_stmt)
            else:
                order_fields.append("{field} {order}".format(field=field.name, order=order_method))
        date_select_stmt, date_group_stmt, date_order_stmt = _get_date_group_by(self, filters.get('periodical', 'day'),
                                                                                time_table_field)
        if self.date_field_id in self.group_field_ids:
            group_by_fields.append(date_group_stmt)
            select_fields.append(date_select_stmt[:-len(time_table_field)] + self.date_field_id.name)
            join_time_stmt = """
                  (SELECT CAST(date_trunc('day', dd) as date) as {field}
                  FROM generate_series('{start_date}'::timestamp, '{end_date}'::timestamp,
                        '1 day'::interval) dd) as time_table LEFT JOIN
                  """.format(field=time_table_field, start_date=start_date, end_date=end_date)
            join_condition = "ON time_table.{time_table_field} = {summarized_table}.{date_field}".format(
                time_table_field=time_table_field, summarized_table=self.summarized_table,
                date_field=self.date_field_id.name)
        if self.date_field_id in self.order_field_ids:
            order_fields.append("{} {}".format(date_order_stmt, order_method))
        select_stmt = "SELECT {}".format(', '.join(select_fields))
        group_by_stmt = group_by_fields and "GROUP BY {}".format(', '.join(group_by_fields)) or ''
        order_stmt = order_fields and "ORDER BY {}".format(', '.join(order_fields)) or ''
        query_stmt = """
                    {select_stmt}
                    FROM
                        {join_time_stmt}
                        ( SELECT *
                          FROM {summarized_table}
                          {where_stmt}
                        ) as {summarized_table}
                        {join_condition}
                    {group_by_stmt}
                    {order_stmt};
                """.format(select_stmt=select_stmt, join_time_stmt=join_time_stmt,
                           summarized_table=self.summarized_table, where_stmt=where_stmt,
                           join_condition=join_condition,
                           group_by_stmt=group_by_stmt, order_stmt=order_stmt)
        try:
            self.env.cr.execute(query_stmt)
            result = self.env.cr.dictfetchall()
            return result
        except Exception:
            raise ValidationError(_('Cannot load the value for {}'.format(self.name)))

    def get_data_for_custom_kpi_item(self, start_date, end_date, filters={}):
        self.ensure_one()
        result = self.query_data_for_custom_item(start_date, end_date, filters)
        return len(result) > 0 and result[0].get(self.kpi_field_id.name, 0) or 0

    def get_data_for_custom_chart_item(self, start_date, end_date, filters={}):
        self.ensure_one()
        result = self.query_data_for_custom_item(start_date, end_date, filters)
        chart_config = self.get_chart_from_result(filters, result)
        return chart_config

    def get_data_for_custom_mixed_item(self, start_date, end_date, filters={}):
        self.ensure_one()
        result = self.query_data_for_custom_item(start_date, end_date, filters)
        # Pop value from the chart if we don't want to show
        if self.kpi_field_id in self.chart_field_ids:
            kpi_value = sum([period.get(self.kpi_field_id.name, 0) for period in result])
        else:
            kpi_value = sum([period.pop(self.kpi_field_id.name, 0) for period in result])
        chart_config = self.get_chart_from_result(filters, result)
        return kpi_value, chart_config

    def get_chart_from_result(self, filters, result=[]):
        get_unique = (lambda field: field.id.origin) if filters.get('period', '') == 'preview' else (
            lambda field: field.id)
        chart_elements = []
        x_axis_labels = []
        x_axis = []
        y_axis = []
        # Default 7 periods for demo data
        length = len(result) or 7
        need_demo_data = all(float_is_zero(sum(group.get(field.name, 0) for field in self.chart_field_ids),
                                           precision_digits=4) for group in result)
        chart_type = self.chart_type == 'line' and len(result) == 1 and 'bar' or self.chart_type or 'bar'
        is_one_element_chart = chart_type in ['pie', 'doughnut', 'polarArea', 'radar']
        color_ids = is_one_element_chart and chart_type != 'radar' and [i for i in range(0, length)] or \
                    self.chart_field_ids.ids
        element_colors = need_demo_data and get_team_demo_color(color_ids) or get_team_color(color_ids)
        maximum_size = self.layout_template == 'mixed' and 3 or 10
        should_hide_legend = is_one_element_chart and length > maximum_size

        for field in self.chart_field_ids:
            # Random demo data if needed
            if need_demo_data:
                values = [random.randint(1, 100) for i in range(0, length)]
                # Care about the sort order for demo data
                if field in self.order_field_ids:
                    values.sort(reverse=self.order_method == 'desc')
            else:
                values = [group.get(field.name, 0) for group in result]
            element_label = field.field_description or 'Unnamed'
            element_color = is_one_element_chart and list(element_colors.values()) or element_colors[get_unique(field)]
            chart_elements.append(get_chart_element_config(element_label, values, element_color, lineTension=0,
                                                           chart_type=chart_type, fill=is_one_element_chart))
        for group in range(0, length):
            axis_label = []
            for field in self.group_field_ids:
                record_name = ''
                # Prepare mock data
                if need_demo_data:
                    if field == self.date_field_id and group < len(result) - 1:
                        record_name = result[group].get(field.name)
                    if field.ttype in ['date', 'datetime'] and not record_name:
                        mock_date = datetime.date.today() - relativedelta(days=length - group - 1)
                        record_name = mock_date.strftime('%b %d')
                    if not record_name:
                        record_name = '{} {}'.format(field.field_description, group)
                # Prepare real data
                else:
                    field_value = result[group].get(field.name, False)
                    if field.ttype == 'many2one' and field_value:
                        record_name = hasattr(self.env[field.relation], 'name_get') and field.relation and \
                                      self.env[field.relation].sudo().browse(field_value).name_get()[0][1] or 'Noname'
                    elif field.ttype == 'selection' and field_value:
                        selection = self.env[field.model].sudo()._fields[field.name].selection
                        record_name = isinstance(selection, list) and dict(selection).get(
                            field_value, 'Noname') or ''
                    # elif (field.ttype == 'datetime' or field.ttype == 'date') and isinstance(field_value, datetime):
                    #     record_name = field_value and field_value.strftime('%d %b')
                    else:
                        record_name = str(field_value)
                axis_label.append(record_name)
            x_axis_labels.append(', '.join(axis_label))
        if not is_one_element_chart:
            x_axis.append(get_chart_axis_config(beginAtZero=True))
            y_axis.append(get_chart_axis_config(beginAtZero=True))
        title_config = get_chart_title_config(need_demo_data and "SAMPLE DATA" or self.name,
                                              fontColor='#FFB800', display=need_demo_data)
        # Only show legend if we have less than 10 elements, if too much, we should hide it
        legend_config = get_chart_legend_config(display=not should_hide_legend)
        tooltip_config = get_chart_tooltip_config(display_mode='index')
        chart_config = get_chart_config_from(chart_type=chart_type, element_configs=chart_elements,
                                             title_config=title_config, legend_config=legend_config,
                                             tooltip_config=tooltip_config, axis_labels=x_axis_labels,
                                             x_axis_configs=x_axis, y_axis_configs=y_axis)
        return chart_config

    def get_data_for_custom_gauge_mixed_item(self, start_date, end_date, filters={}):
        self.ensure_one()
        result = self.query_data_for_custom_item(start_date, end_date, filters)
        value = sum([period.get(self.kpi_field_id.name, 0) for period in result]) * 100
        element_config = get_chart_element_config(self.name,
                                                  [value,
                                                   float_compare(value, 100, precision_digits=4) > 1 and value or 100],
                                                  '#777777', backgroundColor=["#20c54c", "#FF9200"],
                                                  value=value,
                                                  chart_type='gauge', fill=True)
        element_config.pop('borderColor')
        element_configs = [element_config]
        title_config = get_chart_title_config(self.name, display=False)
        legend_config = get_chart_legend_config(display=False)
        chart_config = get_chart_config_from(chart_type='gauge', element_configs=element_configs,
                                             title_config=title_config, legend_config=legend_config)
        return value, chart_config

    def create_summarized_table_for_custom_item(self):
        """
        When users change the model, kpi_field_id or date_field_id, the structure of
        the summarized data will be changed also. So we need to create a new summarized data table for the KPI and
        drop the existing one.
        :return:
        """
        self.ensure_one()
        if not self.model_id or not (self.kpi_field_id or self.chart_field_ids) or not self.measure_type:
            raise ValidationError(_('You should define model, measure fields and aggregate method for this item'))
        # Assign date filter for items
        if self.date_field_id and self.date_field_id in self.group_field_ids and self.layout_template == 'chart':
            try:
                filter_config = json.loads(self.filter_config)
            except (TypeError, ValueError):
                filter_config = {}
            if not filter_config.get('periodical'):
                filter_config.update({'periodical': 'day'})
            self.filter_config = json.dumps(filter_config)
        else:
            self.filter_config = json.dumps({})
        # Assign summarized table's name for this item
        self.summarized_table = "bi_dashboard_data_for_item_{}".format(self.id)
        # Fields to summarize
        field_definitions = []
        chart_fields = self.kpi_field_id | self.chart_field_ids | self.date_field_id | self.group_field_ids
        for field in chart_fields:
            field_type = get_db_field_type(field.ttype)
            field_definitions.append('{} {}'.format(field.name, field_type))
        # Check if the method is average
        if self.measure_type == 'avg':
            field_definitions.append('count int')
        # Check if we should restrict company permission
        if 'company_id' in self.env[self.model_id.model]._fields:
            field_definitions.append('company_id int')
        fields = ', '.join(field_definitions)
        # Drop existing summarized table (if any) and create a new one
        create_stmt = """
            DROP TABLE IF EXISTS {table} CASCADE;
            CREATE TABLE {table} (
                            {fields}
            );
        """.format(table=self.summarized_table,
                   fields=fields)
        self.env.cr.execute(create_stmt)
        # Initialize data for new table
        try:
            query_stmt = self._get_recompute_for_custom_items(None, None)
            thread = Thread(target=self._run_recompute_dashboard_data_for_custom_kpi, args=(query_stmt,))
            thread.start()
        except Exception as e:
            _logger.warning(str(e))
            pass

    def _get_recompute_for_custom_items(self, start_date, end_date):
        query_stmt = ""
        items = self.filtered(lambda i: i.created_on_ui and i.summarized_table)
        for item in items:
            method = item.measure_type or 'sum'
            where_delete_stmt = ''
            where_stmt = ''
            select_fields = []
            group_by_fields = item.group_field_ids.mapped('name')
            measure_fields = item.kpi_field_id | item.chart_field_ids
            fields = (measure_fields | item.date_field_id | item.group_field_ids).mapped('name')
            # We should treat in an another way for average method
            for field in measure_fields:
                if method == 'avg':
                    select_fields.append(
                        'sum({measure_field}) as {measure_field}'.format(measure_field=field.name))

                else:
                    select_fields.append('{method}({measure_field}) as {measure_field}'.format(
                        method=method, measure_field=field.name))
            if item.date_field_id:
                select_fields.append('{date_field}::date as {date_field}'.format(date_field=item.date_field_id.name))
                group_by_fields.append('{}::date'.format(item.date_field_id.name))
                if start_date and end_date:
                    where_delete_stmt = """WHERE {date_field}::date >= '{start_date}'
                                                    AND {date_field}::date <= '{end_date}'""".format(
                        date_field=item.date_field_id.name, start_date=start_date, end_date=end_date)
                    where_stmt = where_delete_stmt

            for field in item.group_field_ids.filtered(lambda i: i != item.date_field_id and i not in measure_fields):
                select_fields.append(field.name)
            if method == 'avg':
                fields.append('count')
                select_fields.append('count(*) as count')
            if 'company_id' in self.env[item.model_id.model]._fields:
                fields.append('company_id')
                select_fields.append('company_id')
                group_by_fields.append('company_id')
            group_by_stmt = group_by_fields and 'GROUP BY {}'.format(', '.join(group_by_fields)) or ''
            # Query eligible records based on domains
            if item.item_domain and item.item_domain != '[]':
                domain = literal_eval(item.item_domain)
                if start_date and end_date and item.date_field_id:
                    domain = domain + [(f'{item.date_field_id.name}', '>=', f"'{start_date} 00:00:00'"),
                                       (f'{item.date_field_id.name}', '<=', f"'{end_date} 23:59:59'")]
                record_ids = self.env[item.model_id.model].search(domain).ids
                search_id_stmt = record_ids and "id IN ({})".format(
                    ', '.join(str(rid) for rid in record_ids)) or "id IS NULL"
                where_stmt = where_stmt and "{} AND {}".format(where_stmt, search_id_stmt) or "WHERE {}".format(
                    search_id_stmt)
            item_query_stmt = """
                DELETE FROM {summarized_table} {where_delete_stmt};
                INSERT INTO {summarized_table} ({fields})
                SELECT {select_fields}
                FROM {model_table}
                {where_stmt}
                {group_by_stmt};
            """.format(summarized_table=item.summarized_table, model_table=self.env[item.model_id.model]._table,
                       fields=','.join(fields), select_fields=','.join(select_fields), group_by_stmt=group_by_stmt,
                       where_delete_stmt=where_delete_stmt, where_stmt=where_stmt)
            query_stmt = query_stmt + item_query_stmt
        return query_stmt

    @api.model
    def _run_recompute_dashboard_data_for_custom_kpi(self, query_stmt):
        if query_stmt:
            # Commit before running to make sure the summarized table was created
            self.env.cr.commit()
            db_registry = registry(self.env.cr.dbname)
            _context = self._context
            with api.Environment.manage(), db_registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, _context)
                try:
                    cron = env.ref('odoo_dashboard_builder.recompute_summarized_data_cron')
                    if cron:
                        cron = cron.sudo()
                        cron._try_lock_dashboard_cron()
                    # Trigger cron to run manually
                    cr.execute(query_stmt)
                except Exception as e:
                    _logger.warning(str(e))

    def create_list_filter(self):
        return json.dumps({'search': '', 'range': '1-30'})

    def query_data(self, offset, limit, sort_obj, is_sort_store, domain):
        if sort_obj:
            if is_sort_store:
                records = self.env[self.model_name].search(domain, order="%s %s"%(sort_obj['key'],sort_obj["type"]),limit=limit, offset=offset)
            else:
                records = self.env[self.model_name].search(domain).sorted(sort_obj['key'], True if sort_obj['type'] == 'desc' else False)
                if (offset < len(records)):
                    records = records[offset:offset+limit] #Maximum bad case
        else:
            records = self.env[self.model_name].search(domain, order=self.date_field_id.name,limit=limit, offset=offset)
        return records

    def get_data_for_custom_list_item(self,start_date, end_date, filters={}):
        offset = filters.get('offset')
        limit = filters.get('limit')
        pinned_records = []
        pinned_ids = []
        is_pinned_data = False
        is_normal_data = False
        is_search_data = False
        is_search_store = False
        is_sort_store = False

        list_field_ids = self.list_field_ids
        domain = []
        if self.item_domain and self.item_domain != '[]':
            domain = literal_eval(self.item_domain)
        if start_date and end_date and self.date_field_id:
            domain = domain + [(f'{self.date_field_id.name}', '>=', f"'{start_date}'"),
                               (f'{self.date_field_id.name}', '<=', f"'{end_date}'")]
        model_field = {x.name: x.store for x in self.model_id.field_id}
        if filters.get('search') and len(filters['search']) > 0 and len(filters['search']['value']) > 0:
            is_search_data = True
            if model_field[filters['search']['name']]:
                is_search_store = True
                domain += [(filters['search']['name'], 'ilike', filters['search']['value'])]
            else:
                limit = 10000000000000000
                offset = 0
        sort_obj = filters.get('order', False)
        if sort_obj and model_field[sort_obj['key']]:
            is_sort_store = True
        pinned_list = json.loads(self.list_pin_ids)
        len_pinned = len(pinned_list)
        if len_pinned > 0 and offset < len_pinned:
            pinned_domain = domain + [('id', 'in', pinned_list)]
            pinned_records = self.query_data(offset, limit, sort_obj, is_sort_store, pinned_domain)
            real_pinned_length = len(pinned_records)
            pinned_ids = pinned_records.ids
            if real_pinned_length < (len_pinned - offset):
                if offset < real_pinned_length:
                    offset = 0
                    is_pinned_data = True
                else:
                    offset -= real_pinned_length
                    is_pinned_data = False
                self.list_pin_ids = str(pinned_ids)
            else:
                is_pinned_data = True
                offset = 0
            if isinstance(limit, int):
                limit -= real_pinned_length
        if limit > 0:
            normal_domain = domain.copy()
            if pinned_list:
                normal_domain += [('id', 'not in', pinned_list)]
            is_normal_data = True
            normal_records = self.query_data(offset, limit, sort_obj, is_sort_store, normal_domain)

        if is_pinned_data and is_normal_data:
            records = pinned_records + normal_records
        elif is_pinned_data:
            records = pinned_records
        elif is_normal_data:
            records = normal_records

        if is_search_data and not is_search_store:
            read_domain = [(filters['search']['name'], 'ilike', filters['search']['value'])]
            records = records.filtered_domain(read_domain)
            records_count = len(records)
            if (filters['offset'] < records_count):
                records = records[filters['offset']: filters['offset']+ filters['limit']]
        else:
            records_count = self.env[self.model_name].search_count(domain)

        if len(records) > 0:
            field_raw_name = list_field_ids.field.mapped(lambda x: x.name)
            field_widget_name = list_field_ids.related_field.mapped(lambda x: x.name)
            f_raw = self.__get_exact_data_function(list_field_ids.field, records[0])
            f_widget = self.__get_exact_data_function(list_field_ids.related_field, records[0])
            content = [{'id': r.id,
                        'data': {attr: f_raw[index](r, attr) for index, attr in enumerate(field_raw_name)},
                        'widget': {attr: f_widget[index](r, attr) for index, attr in enumerate(field_widget_name)},
                        'pinned': True if r.id in pinned_ids else False
                        } for r in records]
        else:
            content = []

        res = {
            'content': content,
            'options': {
                'maximum': records_count
            }
        }
        return res


    def toggle_pin_item(self, record_id, isPinned):
        pinned_list = json.loads(self.list_pin_ids)
        if isPinned:
            pinned_list.remove(record_id)
        else:
            pinned_list.append(record_id)
        self._cr.execute("UPDATE bi_dashboard_item SET list_pin_ids = '%s' WHERE id = %d"%(str(pinned_list), self.id))

    @api.model
    def _extract_ttype_from_field(self, field):
        lst = ['number' if field.field.ttype in ['float', 'integer', 'monetary'] else 'standard']
        lst.append(field.custom_widget or 'standard')
        if field.custom_widget == 'cell_monetary':
            lst.append(field.related_field.name if field.related_field else False)
        else:
            lst.append(field.related_field.name)
        return lst

    @api.model
    def _extract_ttype_from_raw_field(self, field):
        lst = ['number' if field.field_raw_is_number else 'standard']
        lst.append(field.custom_widget or 'standard')
        lst.append(field.field_related_raw)
        return lst

    @api.model
    def __get_exact_data_function(self, fields, first_record):
        lst = []
        # Lambda x, y -> x is the each record of list view and y is the attribute we want to select from this record
        for field in fields:
            if isinstance(first_record[field.name], models.Model):
                if field.ttype in ['one2many','many2many']:
                    lst.append(lambda x, y: len(x[y]) > 0 and f"{len(x[y])} record{len(x[y]) > 1 and 's' or ''}" or "")
                else:
                    lst.append(lambda x, y: x[y].name)
            elif field.ttype == 'selection':
                func = {x.value: x.display_name for x in field.selection_ids}
                lst.append(lambda x, y: func[x[y]])
            else:
                lst.append(lambda x, y: x[y])
        return lst

    # CUSTOM CHARTS
    # RECOMPUTE TO UPDATE SUMMARIZED DATA
    @api.model
    def _recompute_dashboard_data(self):
        params = self.env['ir.config_parameter'].sudo()
        has_intialize_data = params.get_param('odoo_dashboard_builder.has_initialized_data') == 'True'
        date_interval = params.get_param('odoo_dashboard_builder.data_range')
        date_interval = date_interval and int(date_interval) or 45
        if not has_intialize_data:
            query_stmt = self._get_recompute_statements(None, None)
        else:
            today = fields.Datetime.now()
            start_date = today - relativedelta(days=date_interval)
            query_stmt = self._get_recompute_statements(start_date.date(), today.date())
        if query_stmt:
            self.env.cr.execute(query_stmt)
        last_updated = fields.Datetime.now()
        params.set_param('odoo_dashboard_builder.last_updated', last_updated)
        self.env['ir.config_parameter'].sudo().set_param('odoo_dashboard_builder.has_initialized_data', True)

    @api.model
    def _get_recompute_statements(self, start_date, end_date):
        custom_kpi_items = self.env['bi.dashboard.item'].sudo().search(
            [('summarized_table', '!=', False), ('created_on_ui', '=', True)])
        return custom_kpi_items._get_recompute_for_custom_items(start_date, end_date)

    @api.model
    def _run_recompute_dashboard_data(self):
        db_registry = registry(self.env.cr.dbname)
        _context = self._context
        with db_registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, _context)
            try:
                cron = env.ref('odoo_dashboard_builder.recompute_summarized_data_cron')
                if cron:
                    cron = cron.sudo()
                    cron._try_lock_dashboard_cron()
                    # Trigger cron to run manually
                    cron.method_direct_trigger()
                    cron.update({
                        'nextcall': cron.lastcall + relativedelta(minutes=cron.interval_number or 0),
                    })
                else:
                    env['bi.dashboard.item']._recompute_dashboard_data()
                _logger.log(25, "Summarized Dashboard Data has been calculated.")
            except UserError as e:
                _logger.warning(str(e))
            except Exception:
                _logger.exception("Could not update summarized data for BI Dashboard")

    @api.model
    def force_recompute_dashboard_data(self):
        try:
            thread = Thread(target=self._run_recompute_dashboard_data)
            thread.start()
        except Exception:
            pass

    @api.model
    def check_update_status(self):
        cron = self.env.ref('odoo_dashboard_builder.recompute_summarized_data_cron')
        if cron:
            try:
                cron.sudo()._try_lock_dashboard_cron()
                return True
            except UserError:
                return False
        return False

    @api.model
    def check_item_size(self, vals):
        item_type = vals.get('layout_template', 'kpi')
        default_size = get_default_item_size(item_type)
        size_dimensions = ['width', 'height', 'min_width', 'min_height']
        for dimension in size_dimensions:
            vals.setdefault(dimension, default_size.get(dimension, 3))

    @api.model
    def create(self, vals):
        if 'kpi_img_src' in vals and vals.get('kpi_img_src'):
            vals['kpi_img_b64'] = image_path_2_base64(vals['kpi_img_src'])
        if vals.get('layout_template', False) == 'list' and vals.get('created_on_ui', False):
            vals['filter_config'] = self.create_list_filter()
        # Check width, height, min width, min height
        self.check_item_size(vals)
        res = super(DashboardItem, self).create(vals)
        # Create configuration if needed
        board_config = False
        if self.env.context.get('board_config_id'):
            board_config = self.env.context['board_config_id']
        if res.board_ids:
            res.board_ids.sudo().update_board_layout()
        # Initialize summarized data for custom items
        for item in res:
            if item.created_on_ui and item.layout_template != 'list':
                item.create_summarized_table_for_custom_item()
            if board_config:
                item.generate_item_config(board_config, self.env.user.id)
        return res

    def write(self, vals):
        # Check if users removed items from boards
        old_boards = self.board_ids
        # Check if users changed the icon for KPI
        if 'kpi_img_src' in vals and vals.get('kpi_img_src'):
            vals['kpi_img_b64'] = image_path_2_base64(vals['kpi_img_src'])
        res = super(DashboardItem, self).write(vals)
        # Check if users changed the way to calculate data for items
        config_fields = ['model_id', 'date_field_id', 'measure_type', 'kpi_field_id', 'chart_field_ids',
                         'group_field_ids', 'item_domain']
        for item in self:
            if item.created_on_ui and any([field in vals for field in config_fields]) and item.layout_template != 'list':
                item.create_summarized_table_for_custom_item()
        # Update board layout for item's boards if needed
        # Update layout for removed boards and new added boards
        updated_boards = (old_boards - self.board_ids) | (self.board_ids - old_boards)
        if updated_boards:
            updated_boards.sudo().update_board_layout()
        return res

    def unlink(self):
        for item in self:
            if item.created_on_ui and item.summarized_table:
                query_stmt = "DROP TABLE IF EXISTS {}".format(item.summarized_table)
                self.env.cr.execute(query_stmt)
        return super(DashboardItem, self).unlink()

    def get_detailed_view_info(self, config_id, filters={}):
        self.ensure_one()
        # Extract period and filters
        period = filters.get('period', '')
        if not period or period == 'preview':
            start_date = end_date = None
        elif period == 'custom_period' and isinstance(config_id, int):
            item_config = self.env['bi.dashboard.item.config'].sudo().browse(config_id)
            start_date = item_config.board_config_id.custom_start_date
            end_date = item_config.board_config_id.custom_end_date
        else:
            start_date, end_date = _get_date_period(self, period)
        team_id = filters.get('team', 0)
        team_id = team_id and int(team_id) or 0
        return start_date, end_date, team_id

    def get_detailed_view(self, config_id, filters={}, opts=False):
        return False

    def get_detail_view_from_key(self, config_id, filters={}, key=False):
        return False

    def _select_companies_rates(self):
        return """
            SELECT
                r.currency_id,
                COALESCE(r.company_id, c.id) as company_id,
                r.rate,
                r.name AS date_start,
                (SELECT name FROM res_currency_rate r2
                 WHERE r2.name > r.name AND
                       r2.currency_id = r.currency_id AND
                       (r2.company_id is null or r2.company_id = c.id)
                 ORDER BY r2.name ASC
                 LIMIT 1) AS date_end
            FROM res_currency_rate r
            JOIN res_company c ON (r.company_id is null or r.company_id = c.id)
        """

    def get_query_component(self, start_date, end_date, filters={}, date_field=''):
        date_field = date_field or 'date_order_ref'
        team_select_stmt, team_filter_stmt, team_order_stmt = self._get_sales_team_filter(
            filters.get('team', 0))
        period_select_stmt, period_group_stmt, period_order_stmt = _get_date_group_by(
            self, filters.get('periodical', ''), date_field)
        select_stmt = period_select_stmt and ', ' + period_select_stmt or ''
        group_stmt = period_group_stmt and 'GROUP BY ' + period_group_stmt or ''
        order_stmt = period_order_stmt and 'ORDER BY ' + period_order_stmt or ''
        where_stmt = "WHERE company_id={} ".format(self.env.company.id)
        where_stmt = team_filter_stmt and where_stmt + "AND {}".format(team_filter_stmt) or where_stmt
        if start_date and end_date:
            where_stmt = where_stmt + " AND date_order >= '{start_date}' AND date_order <= '{end_date}'".format(
                start_date=start_date, end_date=end_date)
        return select_stmt, where_stmt, group_stmt, order_stmt
