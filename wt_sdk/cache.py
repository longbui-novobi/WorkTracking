from uuid import getnode as getmac
from getpass import getuser
import os
from odoo.tools import config as odoo_config

default_token = 'odoo-token:long-bui'
odoo_config_token = odoo_config.get('wt_token', default_token)
token = os.getenv('WT_TOKEN', odoo_config_token)
identification_cpu = "%s-%s" % (token, getuser())
