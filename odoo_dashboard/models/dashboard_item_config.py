# Copyright © 2021 odoo, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from ..utils.filter_config import get_filter_config
import json


class DashboardItemConfig(models.Model):
    _name = "bi.dashboard.item.config"
    _description = "Dashboard Item Configuration"
    
    item_id = fields.Many2one('bi.dashboard.item', 'Origin Dashboard Item', required=True, ondelete='cascade')
    board_config_id = fields.Many2one('bi.dashboard.board.config', 'Board Configuration',
                                      required=True, ondelete='cascade')
    name = fields.Char(string='Name', related='item_id.name', store=True)
    min_width = fields.Float(string="Min Width", related='item_id.min_width')
    min_height = fields.Float(string="Min Height", related='item_id.min_height')
    kpi_img_src = fields.Char(string="KPI Image Source", related='item_id.kpi_img_src')
    kpi_img_b64 = fields.Binary(string="KPI Image", related='item_id.kpi_img_b64')
    kpi_show_indicator = fields.Boolean(string='Show Trend Indicator?', related='item_id.kpi_show_indicator')
    description = fields.Text(string='Description', related='item_id.description')
    layout_template = fields.Selection(string='Layout Template', related='item_id.layout_template')
    
    filter_config = fields.Text(string='Filter Configurations', default='{}')
    active = fields.Boolean('Active?', required=True, default=True, store=True)
    x_position = fields.Float('X Coordination')
    y_position = fields.Float('Y Coordination')
    width = fields.Float(string="Width", default=2, required=True)
    height = fields.Float(string="Height", default=2, required=True)
    # company_id = fields.Many2one('res.company', 'Company', store=True, required=True)
    user_id = fields.Many2one('res.users', string='Owner', ondelete='cascade')
    
    def update_layout(self, configs):
        if configs:
            self._update_layout(configs)
    
    def _update_layout(self, item_config):
        self.ensure_one()
        config = item_config.get('layoutConfig')
        self.update({
            'active': 1 if item_config.get('active', True) else 0,
            'x_position': config.get('x'),
            'y_position': config.get('y'),
            'width': config.get('width'),
            'height': config.get('height'),
        })
    
    def update_filter(self, config):
        if config:
            self._update_filter(config)
    
    def _update_filter(self, filters):
        self.update({
            'filter_config': filters or self.filter_config
        })
    
    def get_dashboard_item_config(self):
        self.ensure_one()
        item_config = {
            "id": self.item_id.id,
            "config_id": self.id,
            "template": self.layout_template,
            "kpi_icon": self.kpi_img_b64,
            "layoutConfig": self.get_layout_config(),
            'filter': self.get_filters_config(),
            'info': self.get_chart_info(),
        }
        return item_config
    
    def get_filters_config(self):
        self.ensure_one()
        filter_config = self.filter_config or {}
        if filter_config:
            try:
                filter_config = json.loads(filter_config)
            except (TypeError, ValueError):
                filter_config = {}
            for key in filter_config.keys():
                filter_config[key] = {
                    'select': filter_config[key]
                }
                filter_config[key].update(get_filter_config(self, key))
        return filter_config
    
    def get_layout_config(self):
        self.ensure_one()
        return {
            'x': self.x_position,
            'y': self.y_position,
            'width': self.width,
            'height': self.height,
            'min_width': self.min_width,
            'min_height': self.min_height,
        }
    
    def get_chart_info(self):
        self.ensure_one()
        return {
            'title': self.name,
            'description': self.description,
        }
