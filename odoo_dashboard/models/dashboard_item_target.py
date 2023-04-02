# Copyright © 2021 odoo, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import json


class DashboardItemTarget(models.Model):
    _name = "bi.dashboard.item.target"
    _description = "Dashboard Item Target"

    period = fields.Char(string='Raw Period')
    period_id = fields.Many2one('bi.dashboard.item.target.period', string='Period', required=True)
    target = fields.Float(string='Target', default=0.0, required=True)
    dashboard_item_id = fields.Many2one('bi.dashboard.item', string='Dashboard Item')
    remaining_period_option_ids = fields.One2many('bi.dashboard.item.target.period',
                                                  compute='_compute_remaining_period', store=False)

    @api.depends('dashboard_item_id')
    def _compute_remaining_period(self):
        for record in self:
            record.remaining_period_option_ids = [(6, 0, 
            record.dashboard_item_id.target_kpi_ids.filtered(lambda x: x.period_id).mapped('period_id').ids)]

    def write(self, vals):
        res = super(DashboardItemTarget, self).write(vals)
        if 'period_id' in vals:
            for record in self:
                    record.period = record.period_id.period
        return res

    @api.model
    def create(self, vals):
        res = super(DashboardItemTarget, self).create(vals)
        if 'period_id' in vals:
            res.period = res.period_id.period
        return res


class DashboardItemTargetPeriod(models.Model):
    _name = "bi.dashboard.item.target.period"
    _description = "Dashboard Item Target Period"
    _rec_name = 'period_name'

    period_name = fields.Char(string='Name')
    period = fields.Char(string='RAW')
