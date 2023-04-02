# Copyright © 2021 odoo, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import json


class DashboardBoard(models.TransientModel):
    _name = "bi.dashboard.initial"
    _description = 'This model is used to redirect user in the first launch when data is not ready'
    
    def action_cancel(self):
        return False
    
    def action_accept(self):
        self.env['bi.dashboard.item'].force_recompute_dashboard_data()
        board_id = self.env.context.get('dashboard_id', False)
        if board_id:
            board = self.env['bi.dashboard.board'].sudo().browse(board_id)
            return {
                'type': 'ir.actions.client',
                'name': board.name,
                'tag': 'odoo_dashboard',
                'params': {'dashboard_id': board_id},
            }
        return True
