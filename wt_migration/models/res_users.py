import logging
from datetime import datetime

from odoo import models, fields, _
from odoo.tools import ormcache
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = "res.users"

    account_id = fields.Char(string="account ID")

    @ormcache('self')
    def get_jira_token(self):
        return self.env['token.storage'].get_token("jira_" + str(self.login or self.partner_id.email))

    def set_jira_token(self, value):
        self.env['token.storage'].set_token("jira_" + str(self.login or self.partner_id.email), value)
        self.env['token.storage'].clear_caches()
        self.load_jira_projects()

    def load_jira_projects(self):
        to_fetch_projects = self.env['wt.project']
        fetch_ok = False
        for migration in self.env['wt.migration'].sudo().search([]):
            try:
                migration._get_permission()
                to_fetch_projects |= migration.load_projects()
                fetch_ok = True
            except Exception as e:
                _logger.warning("TOKEN UPDATE %s : %s"% (self.env.user.__str__(), str(e)))
                continue
        if fetch_ok:
            to_fetch_projects and to_fetch_projects.sudo().load_new_project()
        else:
            raise UserError(_("The Token is invalid, please check again"))
        self.env['ir.config_parameter'].sudo().set_param('latest_unix', int(datetime.now().timestamp() * 1000))

    def token_exists(self):
        existing_token_users = self.env['res.users']
        for user in self:
            try:
                user.get_jira_token()
                existing_token_users |= user
            except:
                continue
        return existing_token_users 
