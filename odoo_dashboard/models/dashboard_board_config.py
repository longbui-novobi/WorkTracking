# Copyright © 2021 odoo, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from ..utils.filter_config import get_filter_config
from ..utils.date_time_util import _get_date_period
import json
from datetime import date


class DashboardBoardConfig(models.Model):
    _name = "bi.dashboard.board.config"
    _inherit = ["bi.dashboard.filter"]
    _description = "Dashboard Board Configuration"

    name = fields.Char(string='Name', related='board_id.name')
    board_id = fields.Many2one('bi.dashboard.board', 'Origin Dashboard Board')
    board_item_config_ids = fields.One2many('bi.dashboard.item.config', 'board_config_id', string='Board Item Configs')
    filter_config = fields.Text(string="Filter Configuration", default="{}")
    active = fields.Boolean(string='Active?', default=True, required=True)
    # company_id = fields.Many2one('res.company', string='Company', required=True)
    custom_start_date = fields.Date(string="Custom Start Date")
    custom_end_date = fields.Date(string="Custom End Date")
    user_id = fields.Many2one('res.users', string='Owner', ondelete='cascade')
    # allowed_group_ids = fields.Many2many('res.groups', string='Allowed User Groups',
    #                                      related='board_id.allowed_group_ids', readonly=False)
    # allowed_user_ids = fields.Many2many('res.users', string='Allowed Users', related='board_id.allowed_user_ids',
    #                                     readonly=False)
    is_layout_updated = fields.Boolean(string='Is Updated?', default=False)

    def get_filter_config(self):
        self.ensure_one()
        filter_config = self.filter_config or {}
        if filter_config:
            try:
                filter_config = json.loads(filter_config)
            except (TypeError, ValueError):
                filter_config = {}
            for key in filter_config.keys():
                filter_config[key] = {
                    'select': filter_config[key]
                }
                filter_config[key].update(get_filter_config(self, key))
        return {
            'filters': filter_config,
            'board_config_id': self.id
        }

    def get_dashboard_item(self):
        self.ensure_one()
        item_configs = []
        sorted_item_config = self.board_item_config_ids.sorted(lambda c: (c.y_position, c.x_position))
        for item in sorted_item_config:
            res = item.get_dashboard_item_config()
            if res:
                item_configs.append(res)
        return item_configs

    def get_date_range_from_period(self, period):
        if period == 'custom_period':
            return [self.custom_start_date or date.today(), self.custom_end_date or date.today()]
        else:
            return _get_date_period(self, period)

    def update_dashboard_custom_filter(self, configs):
        self._update_dashboard_custom_filter(configs)

    def _update_dashboard_custom_filter(self, filters):
        if filters:
            self.update({
                "custom_start_date": filters.get('start') or date.today(),
                "custom_end_date": filters.get('end') or date.today(),
            })

    def update_dashboard_filter(self, configs):
        self._update_dashboard_general_filters(configs)

    def _update_dashboard_general_filters(self, filters):
        if filters:
            self.update({
                'filter_config': filters
            })

    @api.model
    def update_dashboard_item(self, configs):
        self._update_dashboard_item(configs)

    @api.model
    def _update_dashboard_item(self, configs):
        for item_config in configs:
            if item_config.get('cid', False) and isinstance(item_config['cid'], int):
                item_configuration = self.env['bi.dashboard.item.config'].browse(item_config.get('cid'))
                item_configuration.update_layout(item_config)

    def action_archive(self):
        res = super(DashboardBoardConfig, self).action_archive()
        # self.board_item_config_ids.action_archive()
        for config in self:
            users = config.board_id.archived_user_ids + config.user_id
            config.board_id.sudo().write({
                'archived_user_ids': [(6, 0, users.ids)]
            })
        return res

    def action_unarchive(self):
        res = super(DashboardBoardConfig, self).action_unarchive()
        # self.with_context(active_test=False).board_item_config_ids.action_unarchive()
        for config in self:
            users = config.board_id.archived_user_ids - config.user_id
            config.board_id.sudo().write({
                'archived_user_ids': [(6, 0, users.ids)]
            })
        return res

    def action_reset_board_with_base(self):
        self.ensure_one()
        self.is_layout_updated = False
        self.update_item_configs()
        
    def update_item_configs(self):
        self.ensure_one()
        self.board_item_config_ids.unlink()
        board_layout_id = self.board_id.board_layout_id
        if board_layout_id:
            for item in board_layout_id.board_item_config_ids:
                item.copy({
                    'user_id': self.user_id.id,
                    'board_config_id': self.id,
                    'item_id': item.item_id.id,
                })
    
    def unlink(self):
        for config in self:
            if config.user_id in config.board_id.archived_user_ids:
                users = config.board_id.archived_user_ids - config.user_id
                config.board_id.sudo().write({
                    'archived_user_ids': [(6, 0, users.ids)]
                })
        return super(DashboardBoardConfig, self).unlink()
