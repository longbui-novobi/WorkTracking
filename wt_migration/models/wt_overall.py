import datetime
from collections import defaultdict
import json
import logging

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.exceptions import UserError

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
    export_state = fields.Selection([
        (0, "Unexported"),
        (1, "Exported"),
        (2, "Exported But Description Change"),
        (3, "Exported But Duration Change"),
        (4, "Exported But Start Date Change"),
    ], string="Export State")

    def batch_export(self, pivot_time):
        issue_ids = self.mapped('issue_id')
        issue_ids.write({'last_export': pivot_time})
        issue_ids.export_time_log_to_wt()

    def render_batch_update_wizard(self):
        action = self.env.ref("wt_migration.export_work_log_action_form").read()[0]
        action["context"] = {'default_time_log_ids': self.ids}
        return action
    
    def _get_export_state(self, values):
        self.ensure_one()
        if 'description' in values:
            return 2
        if 'duration' in values:
            return 3
        if 'start_date' in values:
            return 4

    def write(self, values):
        user = self.env.user
        other_logs = self.filtered(lambda log: log.user_id != user)
        if other_logs:
            raise UserError("You cannot update work log of other user")
        res = super().write(values)
        if 'export_state' not in values and not self._context.get("bypass_exporting_check"):
            processed_records = self.env['wt.time.log']
            employee = self.env.user.employee_id
            if employee.auto_export_work_log:
                for log in self:
                    if log.issue_id.wt_migration_id.auto_export_work_log:
                        try:
                            log.issue_id.wt_migration_id.export_specific_log(log.issue_id, log)
                            processed_records |= log
                        except Exception as e:
                            _logger.error(e)
            processed_records.with_context(bypass_exporting_check=True).write({'export_state': 2})
            exported_logs = (self-processed_records).filtered(lambda r: r.export_state == 2)
            if exported_logs:
                log_by_state = defaultdict(lambda: self.env['wt.time.log'])
                for log in exported_logs:
                    state = log._get_export_state(values)
                    log_by_state[state] |= log
                for state, logs in log_by_state.items():
                    logs.update({'export_state': state})
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
        self.export_state = 2
        return self

    def unlink(self):
        try:
            if self.id_on_wt:
                self.issue_id.wt_migration_id.delete_time_logs(self.issue_id, self)
        except:
            pass
        return super().unlink()

    def load_history_domain(self):
        domain = super().load_history_domain()
        if self._context.get('tracking') == "unexported":
            domain = expression.AND([[('export_state', '=', 2)], domain])
        if self._context.get('tracking') == "exported":
            domain = expression.AND([[('export_state', '!=', 2)], domain])
        return domain
