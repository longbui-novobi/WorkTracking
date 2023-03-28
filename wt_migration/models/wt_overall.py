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
    export_state = fields.Integer(string="Export State", default=0)
        # (0, "Unexported"),
        # (1, "Exported"),
        # (2, "Exported But Description Change"),
        # (3, "Exported But Duration Change"),
        # (4, "Exported But Start Date Change"),
        # (5, "Exported But All Changes"),
        # (6, "Exported But Duration + Start Date Changes"),
        # (7, "Exported But Duration + Description Changes"),
        # (8, "Exported But Description + Start Date Changes"),

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
        if 'start_date' in values and 'description' in values and 'duration' in values:
            return 5
        if 'start_date' in values and 'duration' in values:
            return 6
        if 'start_date' in values and 'description' in values:
            return 8
        if 'description' in values and 'duration' in values:
            return 7
        if 'start_date':
            return 4
        if 'duration' in values:
            return 3
        if 'description' in values:
            return 2

    def write(self, values):
        res = super().write(values)
        if not self._context.get("bypass_exporting_check"):
            log_by_employee = defaultdict(lambda: self.env['wt.time.log'])
            processed_records = self.env['wt.time.log']
            for log in self:
                log_by_employee[log.employee_id] |= log
            for employee, logs in log_by_employee.items():
                if employee.auto_export_work_log:
                    for log in logs:
                        if log.issue_id.wt_migration_id.auto_export_work_log:
                            try:
                                log.issue_id.wt_migration_id.export_specific_log(log.issue_id, log)
                                log.export_state = 1
                                processed_records |= log
                            except Exception as e:
                                _logger.error(e)
            exported_logs = (self-processed_records).filtered(lambda r: r.export_state >= 1)
            log_by_state = defaultdict(lambda: self.env['wt.time.log'])
            for log in exported_logs:
                state = log._get_export_state(values)
                log_by_state[state] |= log
            for state, logs in log_by_state.items():
                log.update({'export_state': state})
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
        self.export_state = 1
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
            domain = expression.AND([[('export_state', '=', 1)], domain])
        if self._context.get('tracking') == "exported":
            domain = expression.AND([[('export_state', '!=', 1)], domain])
        return domain
