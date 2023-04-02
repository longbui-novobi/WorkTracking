# Copyright © 2021 odoo, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError


class DashboardBoard(models.Model):
    _name = "bi.dashboard.board"
    _inherit = ["bi.dashboard.filter"]
    _description = "Dashboard Board"
    
    name = fields.Char(string='Name', required=True)
    dashboard_item_ids = fields.Many2many('bi.dashboard.item', 'dashboard_board_item_rel', 'board_id', 'item_id',
                                          string='Dashboard Items')
    filter_config = fields.Text(string="Filter Configuration", default="{}")
    active = fields.Boolean(string='Active?', default=True, required=True)
    menu_sequence = fields.Integer(string='Menu Sequence', default=100, required=True)
    parent_menu_id = fields.Many2one('ir.ui.menu', string='Parent Menu', required=True)
    action_id = fields.Many2one('ir.actions.client', string='Action')
    menu_id = fields.Many2one('ir.ui.menu', string='Menu Item')
    menu_name = fields.Char(string='Menu Name', required=True)
    board_group_id = fields.Many2one('res.groups', string='Dashboard Groups')
    allowed_group_ids = fields.Many2many('res.groups', 'bi_board_config_groups_rel', 'board_config_id', 'group_id',
                                         string='Allowed User Groups')
    allowed_user_ids = fields.Many2many('res.users', string='Allowed Users')
    archived_user_ids = fields.Many2many('res.users', 'dashboard_board_archieved_users', 'dashboard_id', 'user_id',
                                         string='Archived Users')
    board_config_ids = fields.One2many('bi.dashboard.board.config', 'board_id', string='Board Configurations')
    board_layout_id = fields.Many2one('bi.dashboard.board.config', string='Board Layout',
                                      ondelete='cascade')
    
    is_updated = fields.Boolean(string='Is Updated?', default=False)
    is_floating_layout = fields.Boolean(string='Floating Layout?', default=False)
    is_show_last_updated = fields.Boolean(string='Showing Last Updated?', default=True)

    def create_config(self, user_id=None):
        self.ensure_one()
        if not user_id:
            user_id = self.env.user.id
        board_config = self.env['bi.dashboard.board.config']
        if self.board_layout_id:
            board_config = self.board_layout_id.copy({
                'user_id': user_id,
                'board_id': self.id,
            })
            for item in self.board_layout_id.board_item_config_ids:
                item.copy({
                    'user_id': user_id,
                    'board_config_id': board_config.id,
                    'item_id': item.item_id.id,
                })
        return board_config
    
    def create_board_layout(self):
        for board in self:
            board_layout = self.env['bi.dashboard.board.config'].create({
                'filter_config': board.filter_config or {},
                'filter_type_ids': [(6, 0, board.filter_type_ids.ids)]
            })
            board.board_layout_id = board_layout
        self.update_board_layout()
    
    def update_board_layout(self):
        personal_dashboard = self.env.context.get('create_from_personal_dashboard', False)
        for board in self:
            board.update_board_config_items(board.board_layout_id)
            if personal_dashboard:
                board.update_items_on_create(uid=self.env.user.id)
        self.__update_board_config_status()
    
    def update_items_on_create(self, uid=None):
        for board in self:
            config_board = board.get_dashboard_board_config(uid)
            if config_board:
                config_board.update_item_configs()

    def update_board_config_items(self, config):
        self.ensure_one()
        if not config:
            return
        for item in self.dashboard_item_ids:
            item.generate_item_config(config.id, config.user_id.id)
        removed_items = config.board_item_config_ids.filtered(lambda i: i.item_id not in self.dashboard_item_ids)
        removed_items.unlink()
    
    def get_dashboard_board_config(self, uid, create=False):
        self.ensure_one()
        if self.env.context.get('preview_layout', False):
            board_config = self.board_layout_id
        else:
            board_config = self.board_config_ids.filtered(
                lambda c: c.user_id.id == uid)
        if not board_config and create:
            board_config = self.create_config(uid)
        return board_config
    
    def get_dashboard_item(self):
        self.ensure_one()
        board_config = self.get_dashboard_board_config(self.env.user.id)
        # TODO: Check multiple configs
        return board_config and board_config.get_dashboard_item() or []
    
    def get_filters_config(self):
        self.ensure_one()
        board_config = self.get_dashboard_board_config(self.env.user.id)
        if not board_config:
            raise UserError(_("Cannot load the requested dashboard."))
        return board_config.get_filter_config()
    
    def create_board_group(self):
        self.ensure_one()
        if not self.board_group_id:
            user_ids = self.allowed_user_ids.ids + self.allowed_group_ids.users.ids
            self.board_group_id = self.env['res.groups'].sudo().create({
                'name': "Group for {} - {}(Omni Dashboard)".format(self.id, self.name),
                'users': [(6, 0, user_ids)],
                'category_id': self.env.ref('base.module_category_hidden').id,
            })
        self.update_board_group_users()
        return self.board_group_id
    
    def update_board_group_users(self):
        boards = self.filtered(lambda b: b.board_group_id)
        for board in boards:
            existing_user_ids = board.board_group_id.users | board.archived_user_ids
            allowed_users = board.allowed_user_ids | board.allowed_group_ids.users
            valid_users = allowed_users.filtered(
                lambda u: u.has_group('odoo_dashboard.dashboard_group_user'))
            removed_users = existing_user_ids.filtered(lambda u: u.id not in valid_users.ids)
            valid_users = valid_users - board.archived_user_ids
            # Check if allowed users already has dashboard config
            for uid in valid_users.ids:
                board.get_dashboard_board_config(uid, create=True)
            # Delete existing config of removed users
            for user in removed_users:
                config = board.with_context(active_test=False).get_dashboard_board_config(user.id, create=False)
                if config:
                    config.unlink()
            # Update list of allowed users
            board.board_group_id.sudo().write({'users': [(6, 0, valid_users.ids)]})
    
    def update_menu_item(self):
        for board in self:
            if board.menu_id:
                board.menu_id.sudo().update({
                    'name': board.menu_name,
                    'sequence': board.menu_sequence,
                    'parent_id': board.parent_menu_id,
                })
    
    def update_filters_for_layout(self):
        personal_dashboard = self.env.context.get('create_from_personal_dashboard', False)
        for board in self:
            board.board_layout_id.update({
                'filter_config': board.filter_config or {},
                'filter_type_ids': [(6, 0, board.filter_type_ids.ids)]
            })
            if personal_dashboard:
                config = board.get_dashboard_board_config(self.env.user.id)
                if config:
                    config.update({
                        'filter_config': board.filter_config or {},
                        'filter_type_ids': [(6, 0, board.filter_type_ids.ids)]
                    })
    
    @api.model
    def create(self, vals):
        current_user = self.env.user
        if self.env.context.get('create_from_personal_dashboard', False) and \
                current_user.has_group('odoo_dashboard.dashboard_group_user'):
            vals['allowed_user_ids'] = vals.get('allowed_user_ids', []) + [(4, current_user.id)]
        res = super(DashboardBoard, self).create(vals)
        # Create board layout
        res.create_board_layout()
        # Create group for dashboard board
        board_group = res.create_board_group()
        action_id = {
            'name': res.name,
            'res_model': 'bi.dashboard.board',
            'tag': 'odoo_dashboard',
            'params': {'dashboard_id': res.id},
        }
        action = self.env['ir.actions.client'].sudo().create(action_id)
        
        # Create menu item
        menu_item = self.env['ir.ui.menu'].sudo().create({
            'name': res.menu_name,
            'active': res.active,
            'parent_id': res.parent_menu_id and res.parent_menu_id.id,
            'action': "ir.actions.client," + str(action.id),
            'groups_id': [(6, 0, board_group.ids)],
            'sequence': res.menu_sequence or 100,
        })
        res.action_id = action
        res.menu_id = menu_item
        return res
    
    def write(self, vals):
        res = super(DashboardBoard, self).write(vals)
        if 'menu_sequence' in vals or 'parent_menu_id' in vals or 'menu_name' in vals:
            self.update_menu_item()
        if 'dashboard_item_ids' in vals:
            self.update_board_layout()
        if 'filter_type_ids' in vals:
            self.update_filters_for_layout()
        if 'allowed_group_ids' in vals or 'allowed_user_ids' in vals or 'archived_user_ids' in vals:
            self.update_board_group_users()
        return res
    
    def unlink_dashboard_components(self):
        self_sudo = self.sudo()
        self_sudo.action_id.unlink()
        self_sudo.menu_id.unlink()
        self_sudo.board_group_id.unlink()
        self_sudo.board_config_ids.unlink()
        self_sudo.board_layout_id.unlink()
    
    def unlink(self):
        self.unlink_dashboard_components()
        return super(DashboardBoard, self).unlink()
    
    @api.model
    def get_last_updated_time(self):
        last_updated = self.env['ir.config_parameter'].sudo().get_param('odoo_dashboard.last_updated')
        try:
            last_updated = last_updated and fields.datetime.strptime(last_updated, DEFAULT_SERVER_DATETIME_FORMAT) or ''
            return last_updated
        except ValueError:
            return ''
    
    @api.model
    def check_manager(self):
        role = self.env.user.has_group('odoo_dashboard.dashboard_group_manager')
        return role
    
    @api.model
    def get_dashboard_data_initialize(self, board_id):
        if not board_id:
            return False
        is_initialized_data = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_dashboard.has_initialized_data') == 'True'
        action = False
        if not is_initialized_data:
            action = self.env.ref('odoo_dashboard.action_dashboard_initial').read()[0]
            if action:
                action['context'] = {'dashboard_id': board_id}
        return action
    
    def __update_board_config_status(self):
        self.is_updated = True
        self.board_config_ids.update({
            'is_layout_updated': True
        })

    def update_dashboard_layout(self, board_config_id, configs):
        if self.board_layout_id.id == board_config_id:
            self.__update_board_config_status()
        self.env['bi.dashboard.board.config'].update_dashboard_item(configs)
    
    def action_apply_layout(self):
        self.is_updated = False
        users = self.allowed_user_ids | self.allowed_group_ids.users
        for user in users:
            self.update_items_on_create(user.id)

    def action_preview_board_layout(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'odoo_dashboard',
            'target': 'current',
            'params': {'dashboard_id': self.id},
            'context': {'preview_layout': True, 'preview_name': self.name}
        }

    def get_floating_layout(self):
        self.ensure_one()
        return {
            'is_floating_layout': self.is_floating_layout,
            'is_show_last_updated': self.is_show_last_updated,
        }
