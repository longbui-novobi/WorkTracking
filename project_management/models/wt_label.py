from datetime import datetime
from odoo import api, fields, models, _


class WtLabel(models.Model):
    _name = "wt.label"
    _description = "Label"

    name = fields.Char(string='Name', require=True)