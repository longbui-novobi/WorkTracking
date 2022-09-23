from odoo import models, fields, _
from odoo.tools import ormcache


class ResUsers(models.Model):
    _inherit = "res.users"

    @ormcache('self')
    def get_jira_token(self):
        return self.env['token.storage'].get_token("jira_" + str(self.login or self.partner_id.email))

    def set_jira_token(self, value):
        self.env['token.storage'].set_token("jira_" + str(self.login or self.partner_id.email), value)

    def token_exists(self):
        existing_token_users = self.env['res.users']
        for user in self:
            try:
                user.get_jira_token()
                existing_token_users |= user
            except:
                continue
        return existing_token_users
