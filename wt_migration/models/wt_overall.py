import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import json
import logging

_logger = logging.getLogger(__name__)


class WtStatus(models.Model):
    _inherit = "wt.status"

    wt_key = fields.Char(string='Task Key')


class WtTimeLog(models.Model):
    _inherit = "wt.time.log"

    id_on_wt = fields.Integer(string='ID on Task')
    is_exported = fields.Boolean(string="Is Exported?", default=False)
    wt_create_date = fields.Datetime(string="Wt Create On")
    wt_write_date = fields.Datetime(string="Wt Update On")

    def batch_export(self, pivot_time):
        issue_ids = self.mapped('issue_id')
        issue_ids.write({'last_export': pivot_time})
        issue_ids.export_time_log_to_wt()

    def render_batch_update_wizard(self):
        action = self.env.ref("wt_migration.export_work_log_action_form").read()[0]
        action["context"] = {'default_time_log_ids': self.ids}
        return action

    def write(self, values):
        res = super().write(values)
        if 'is_exported' not in values:
            employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
            for record in self:
                if record.issue_id.wt_migration_id.auto_export_work_log and employee_id.auto_export_work_log:
                    try:
                        record.issue_id.wt_migration_id.export_specific_log(record.issue_id, record)
                        record.is_exported = True
                    except Exception as e:
                        _logger.error(e)
                        record.is_exported = False
                elif record.is_exported:
                    record.is_exported = False
        return res

    def force_export(self):
        issues = dict()
        for record in self:
            if record.issue_id in issues:
                issues[record.issue_id] |= record
            else:
                issues[record.issue_id] = record
        for issue in issues.keys():
            issue.wt_migration_id.export_specific_log(issue, issues[issue])
        self.is_exported = True
        return self

    def unlink(self):
        try:
            if self.id_on_wt:
                self.issue_id.wt_migration_id.delete_time_logs(self.issue_id, self)
        except:
            pass
        return super().unlink()
