# Copyright © 2021 odoo, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    bi_dashboard_reload_interval = fields.Integer(string='Refresh Time',
                                                  config_parameter='odoo_dashboard_builder.recompute_interval')
    bi_dashboard_date_range = fields.Integer(string='Days To Recompute',
                                             config_parameter='odoo_dashboard_builder.data_range')
    show_sample_data = fields.Boolean(string='Sample Data', related='company_id.show_sample_data',
                                    readonly=False)
    
    @api.constrains('bi_dashboard_reload_interval')
    def _validate_dashboard_reload_interval(self):
        if float_compare(self.bi_dashboard_reload_interval, 0, precision_rounding=2) <= 0:
            raise UserError(_("The Refresh Time should be a positive number."))
    
    @api.constrains('bi_dashboard_date_range')
    def _validate_dashboard_date_range(self):
        if float_compare(self.bi_dashboard_date_range, 0, precision_rounding=2) <= 0:
            raise UserError(_("The Days To Compute should be a positive number."))
    
    @api.model
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        cron_job = self.env.ref('odoo_dashboard_builder.recompute_summarized_data_cron')
        if cron_job:
            cron_job._try_lock_dashboard_cron()
            cron_job.sudo().update({'interval_number': self.bi_dashboard_reload_interval})
        return res
