# Copyright © 2021 odoo, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.addons.base.models.res_users import is_selection_groups


class ResGroup(models.Model):
    _inherit = 'res.groups'
    
    bi_dashboard_ids = fields.Many2many('bi.dashboard.board',
                                        'bi_board_config_groups_rel', 'group_id', 'board_config_id',
                                        string='Dashboard Boards')
    
    def write(self, vals):
        res = super(ResGroup, self).write(vals)
        if vals.get('users') and self.bi_dashboard_ids:
            self.bi_dashboard_ids.sudo().update_board_group_users()
        return res


class ResUsers(models.Model):
    _inherit = 'res.users'
    
    is_dashboard_user = fields.Boolean(string='Is dashboard user?', compute='_compute_dashboard_user', store=True)
    # dashboard_board_config_ids = fields.One2many('bi.dashboard.board.config', 'user_id',
    #                                              string='Dashboard Item Configurations')
    # dashboard_item_config_ids = fields.One2many('bi.dashboard.item', 'user_id',
    #                                             string='Dashboard Item Configurations')
    
    @api.depends('groups_id')
    def _compute_dashboard_user(self):
        for user in self:
            if user.has_group('odoo_dashboard.dashboard_group_user'):
                user.is_dashboard_user = True
            else:
                user.is_dashboard_user = False
    
    def write(self, vals):
        is_update_groups = any(True for k in vals if is_selection_groups(k))
        bi_dashboard_boards = self.env['bi.dashboard.board']
        # Get dashboard from current groups
        if vals.get('groups_id') or is_update_groups:
            bi_dashboard_boards |= self.groups_id.bi_dashboard_ids
        # Call super method
        res = super(ResUsers, self).write(vals)
        # Get dashboard from new groups
        bi_dashboard_boards |= self.groups_id.bi_dashboard_ids
        # Check existing dashboards
        bi_dashboard_boards |= self.env['bi.dashboard.board.config'].with_context(active_test=False).sudo().search(
            [('user_id', 'in', self.ids)]).board_id
        if bi_dashboard_boards:
            bi_dashboard_boards.sudo().update_board_group_users()
        return res
