from odoo import api, fields, models, _


class CloneToMigration(models.TransientModel):
    _name = 'clone.to.migration'
    _description = 'Clone To Migration'

    wt_migration_id = fields.Many2one('wt.migration', string='Migration', required=True)
    project_id = fields.Many2one("wt.project", string="Project", domain="[('wt_migration_id', '=', wt_migration_id)]")
    epic_id = fields.Many2one("wt.issue", string="Epic", domain="[('project_id', '=', project_id), ('epic_ok', '=', True)]")
    sprint_id = fields.Many2one("agile.sprint", string="Sprint", domain="[('project_id', '=', project_id)]")
    label_ids = fields.Many2many("wt.label", string="Labels")
    auto_export = fields.Boolean(string="Export to Destination Server?")
    assignee_id = fields.Many2one("res.users", string="Assign To", domain="[('account_id','!=', False)]")
    issue_ids = fields.Many2many('wt.issue', string="Issues")

    def confirm(self):
        self.ensure_one()
        self.issue_ids.action_clone_to_server(self.wt_migration_id, self)
