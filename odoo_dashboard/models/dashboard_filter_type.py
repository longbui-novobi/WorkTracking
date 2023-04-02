# Copyright © 2021 odoo, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class DashboardFilterType(models.Model):
    _name = "bi.dashboard.filter.type"
    _description = "Dashboard Filter Type"
    
    name = fields.Char(string='Name', required=True)
    type = fields.Char(string='Type', required=True)
    default_value = fields.Char(string='Default Value', required=True)
