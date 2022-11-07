from odoo import api, fields, models, _
from datetime import datetime
import logging
from collections import defaultdict

_logger = logging.getLogger(__name__)


class WtProject(models.Model):
    _inherit = "wt.project"

    wt_migration_id = fields.Many2one("wt.migration", string="Task Migration Credentials")
    last_update = fields.Datetime("Last Update Cron")
    allow_to_fetch = fields.Boolean("Should Fetch?")
 
    @api.model
    def cron_fetch_issue(self, load_create=True):
        if not self:
            self = self.search([('allow_to_fetch', '=', True), ('wt_migration_id.active', '=', True)])
        latest_unix = int(self.env['ir.config_parameter'].get_param('latest_unix'))
        checkpoint_unix = datetime.now()
        allowed_user_ids = self.env['res.users'].search([]).token_exists()
        migration_dict = defaultdict(lambda: self.env['res.users'])
        new_projects_by_user = defaultdict(lambda: self.env['wt.project'])
        for project in self:
            user_ids = self.env['res.users']
            if not project.wt_migration_id.is_round_robin and project.wt_migration_id.admin_user_ids:
                user_ids = allowed_user_ids & project.wt_migration_id.admin_user_ids
            elif project.allowed_user_ids:
                user_ids = allowed_user_ids & project.allowed_user_ids
            if not (user_ids & migration_dict[project.wt_migration_id]) and user_ids:
                migration_dict[project.wt_migration_id] |= user_ids[0]
            if len(user_ids) == 0 and project.wt_migration_id:
                user_ids = project.wt_migration_id.admin_user_ids
            if (not project.last_update or project.last_update.timestamp() * 1000 < latest_unix) and user_ids and project.wt_migration_id:
                new_projects_by_user[user_ids[0]] |= project
            project.sudo().last_update = checkpoint_unix
        
        if new_projects_by_user:
            for user, projects in new_projects_by_user.items():
                projects.with_user(user).load_new_project()

        for wt in migration_dict.keys():
            wt.with_delay().update_projects(latest_unix, migration_dict[wt])
            wt.with_delay(eta=1).delete_work_logs_by_unix(latest_unix, migration_dict[wt])
            wt.with_delay(eta=2).load_work_logs_by_unix(latest_unix, migration_dict[wt])
        
        self.env['ir.config_parameter'].set_param('latest_unix', int(checkpoint_unix.timestamp() * 1000))

    def load_new_project(self):
        migration_dict = defaultdict(lambda: self.env['wt.project'])
        for new_project in self:
            migration_dict[new_project.wt_migration_id] |= new_project
        last_updated = datetime.now()
        for migration_id, projects in migration_dict.items():
            for project in projects:
                migration_id.with_delay()._update_project(project, project.last_update)
            migration_id.with_delay(eta=1).load_missing_work_logs_by_unix(0, self.env.user, projects)
            projects.sudo().last_update = last_updated

    def reset_state(self):
        for record in self:
            record.last_update = False

    @api.model_create_multi
    def create(self, value_list):
        res = super().create(value_list)
        _logger.info("NEW PROJECT: %s" % res.mapped('project_key'))
        return res
