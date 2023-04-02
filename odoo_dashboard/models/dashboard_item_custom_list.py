# Copyright © 2021 odoo, LLC
# See LICENSE file for full copyright and licensing details.

from logging import getLogger
from typing import Sequence
from odoo import api, fields, models, registry, SUPERUSER_ID, _

_logger = getLogger(__name__)


class DashboardItemCustomList(models.Model):
    _name = 'bi.dashboard.item.custom.list'
    _description = 'Bi Dashboard Item Custom List'

    sequence = fields.Integer(string='Sequence', required=True)
    dashboard_item = fields.Many2one('bi.dashboard.item', string="Field Name")
    field = fields.Many2one('ir.model.fields', string="Field")
    custom_widget = fields.Selection([
        ('cell_monetary', 'Monetary'), 
        ('cell_image', 'Image'),
        ('cell_percent', 'Percent')
        ], string="Widget")
    related_field = fields.Many2one('ir.model.fields', string="Relation with Field")
    compute_satisfy = fields.One2many('ir.model.fields', store=False, compute='_compute_satisfy_domain')
    
    field_name = fields.Text(string='Field Text') #Use for display on the header of table
    field_raw = fields.Text(string='Field Raw') #Use for search, analyze sort column, ...
    field_related_raw = fields.Text(string='Field Related') #Handle by code
    field_raw_is_number = fields.Boolean(string='Number Format?', default=False)

    is_trigger_open = fields.Boolean('Trigger Open', default=False)

    @api.onchange('custom_widget')
    def _onchange_relation(self):
        for record in self:
            if record.custom_widget == 'cell_monetary':
                record.related_field = self.env['ir.model.fields'].search(
                    [('model_id', '=', record.dashboard_item.model_id.id), ('name', '=', 'currency_id')])[0]
            elif not record.custom_widget:
                record.related_field = False

    @api.depends('custom_widget')
    def _compute_satisfy_domain(self):
        for record in self:
            base_condition = [('model_id', '=', record.dashboard_item.model_id.id)]
            if record.custom_widget == 'cell_monetary':
                base_condition.extend([('relation', '=', 'res.currency')])
            elif record.custom_widget == 'cell_image':
                base_condition.extend([('ttype', '=', 'binary')])
            record.compute_satisfy = self.env['ir.model.fields'].search(base_condition)

    