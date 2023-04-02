# Copyright © 2021 odoo, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import json


class DashboardFilter(models.AbstractModel):
    _name = "bi.dashboard.filter"
    _description = "Dashboard Filter"
    
    filter_config = fields.Text(string="Filter Configuration", default="{}")
    filter_type_ids = fields.Many2many('bi.dashboard.filter.type', string='Filters')
    
    def update_filters(self):
        for filter in self:
            try:
                filter_config = json.loads(filter.filter_config)
            except (TypeError, ValueError):
                filter_config = {}
            updated_filter_config = {}
            for filter_type in filter.filter_type_ids:
                key = filter_type.type
                updated_filter_config.update({key: filter_config.get(key, filter_type.default_value)})
            try:
                config = json.dumps(updated_filter_config)
                filter.filter_config = config
            except (TypeError, ValueError):
                filter.filter_config = {}
    
    @api.model
    def create(self, vals):
        res = super(DashboardFilter, self).create(vals)
        res.update_filters()
        return res
    
    def write(self, vals):
        res = super(DashboardFilter, self).write(vals)
        if 'filter_type_ids' in vals:
            self.update_filters()
        return res
