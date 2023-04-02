# Copyright © 2021 odoo, LLC
# See LICENSE file for full copyright and licensing details.

{
    'name': 'odoo: Dashboard',
    'summary': 'odoo: Dashboard',
    'category': 'Dashboard/Omni Dashboard',
    "author": "odoo",
    "website": "https://www.odoo.com/",
    'depends': [
        'base',
        'web',
        'digest'
    ],
    "data": [
        'security/dashboard_security.xml',
        'security/ir.model.access.csv',
        
        'data/ir_config_parameter_data.xml',
        'data/ir_cron.xml',
        'data/dashboard_filter_data.xml',
        'data/dashboard_item_target_data.xml',
        'data/digest_data.xml',
        
        # 'views/assets.xml',
        'views/dashboard_settings.xml',
        'views/dashboard_views.xml',
        'views/dashboard_config_views.xml',
        'views/dashboard_digest_email_views.xml',
        'views/dashboard_menu.xml',
        'views/digest_view.xml',
        
        'wizard/initial_dashboard.xml',
    ],
    "application": True,
    "installable": True,
    "uninstall_hook": "uninstall_hook",
    'assets': {
        'web.assets_backend': [
            'odoo_dashboard/static/src/css/dashboard_style.scss',
            'odoo_dashboard/static/src/css/item_style.scss',
            'odoo_dashboard/static/src/css/dashboard_action_popup_style.scss',
            'odoo_dashboard/static/src/js/owl/dashboard_owl.js',
            'odoo_dashboard/static/src/js/owl/dashboard_item_filter_owl.js',
            'odoo_dashboard/static/src/js/owl/dashboard_item_subcomponents_owl.js',
            'odoo_dashboard/static/src/js/owl/dashboard_item_template_owl.js',
            'odoo_dashboard/static/src/js/owl/dashboard_item_owl.js',
            'odoo_dashboard/static/src/js/owl/dashboard_grid_owl.js',
            'odoo_dashboard/static/src/js/owl/basic_view_inherit.js',
            'odoo_dashboard/static/src/js/hook/custom_filter_hook.js',
            'odoo_dashboard/static/src/js/owl/list_view_header_button.js',
            'odoo_dashboard/static/src/js/hook/custom_popup.js',
            'odoo_dashboard/static/src/js/owl/preview/item_preview.js',
            'odoo_dashboard/static/src/js/hook/list_view_cell.js'
        ],
        'web.assets_qweb': [
            'odoo_dashboard/static/src/xml/*.xml',
            'odoo_dashboard/static/src/xml/preview/*.xml'
        ],
    },
    'license': 'LGPL-3',
}
