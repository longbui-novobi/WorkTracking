# Copyright © 2021 odoo, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = "res.company"
    
    show_sample_data = fields.Boolean(string='Sample Data', default=True)
