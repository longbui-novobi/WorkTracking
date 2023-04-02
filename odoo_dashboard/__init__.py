# Copyright © 2021 odoo, LLC
# See LICENSE file for full copyright and licensing details.

from . import models
from . import wizard
from . import controllers

from odoo import SUPERUSER_ID, api

def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['bi.dashboard.item'].search([]).unlink()
    env['bi.dashboard.board'].search([]).unlink()

