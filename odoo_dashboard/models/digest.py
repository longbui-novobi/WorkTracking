# Copyright © 2021 odoo, LLC
# See LICENSE file for full copyright and licensing details.

from werkzeug.urls import url_join
from datetime import datetime
from odoo.exceptions import UserError
from odoo import fields, models, _, api
from odoo.addons.odoo_dashboard_builder.utils.date_time_util import _get_date_period
from odoo.tools import float_compare, format_decimalized_number


PARSER = {
    "daily": ('today', 'yesterday'),
    "weekly": ('this_week', 'last_week'),
    "monthly": ('this_month', 'last_month'),
    'quarterly': ('this_quarter', 'last_quarter')
}


class Digest(models.Model):
    _inherit = 'digest.digest'

    kpi_omni_dashboard = fields.Boolean('Summary Dashboard KPIs')

    @api.model
    def currency_conversion(self, value, format, currency, custom_unit):
        value = abs(value)
        if format == 'percent':
            converted_amount = format_decimalized_number(value * 100, decimal=2)
            return str(converted_amount).upper() + "%"
        converted_amount = format_decimalized_number(value, decimal=2)
        return_val = ''
        if format == 'decimal':
            return_val = str(converted_amount)
        elif format == 'currency':
            return_val = self._format_currency_amount(converted_amount, currency)
        elif format == 'custom':
            return f"{converted_amount} {custom_unit}"
        return return_val.upper()

    @api.model
    def _compute_timeframes_periodicity(self, company, periodicity):
        params = PARSER.get(periodicity)
        if not params:
            params = PARSER.get('daily')
        lst = [_get_date_period(self, x) for x in params]
        return lst

    def action_send(self):
        self.ensure_one()
        if not self.kpi_omni_dashboard:
            return super(Digest, self).action_send()
        else:
            is_initialized_data = self.env['ir.config_parameter'].sudo().get_param(
                'odoo_dashboard_builder.has_initialized_data') == 'True'
            if is_initialized_data:
                return self.mail_create_and_send()
            else:
                raise UserError(_('Omni Dashboard have not initialize data yet.'))

    @api.model
    def _get_group_field_format(self):
        category = self.env.ref('base.module_category_dashboard_omni_dashboard')
        groups = self.env['res.groups'].search([('category_id', '=', category.id)], order='id')
        return groups

    @api.model
    def minify_board_data(self):
        boards = self.env['bi.dashboard.board'].search([])
        minify_boards = []
        for board in boards:
            minify_boards.append({
                'board_name': board.name,
                'action_id': board.action_id,
                'menu_id': board.menu_id,
                'group': (board.allowed_user_ids | board.allowed_group_ids.users).ids,
                'items': board.dashboard_item_ids.filtered_domain([('layout_template', '=', 'kpi')])
            })
        return minify_boards

    def minify_user_data(self):
        users = self.user_ids
        minify_users = []
        for user in users:
            minify_users.append({
                'company_ids': user.company_ids.ids,
                'id': user.id,
                'email_formatted': user.email_formatted
            })
        return minify_users

    @api.model
    def check_user_group(self, user_id, group_user_ids):
        return True if user_id in group_user_ids else False

    @api.model
    def query_data_source(self, minify_boards, periodicity):
        board_data = []
        for board in minify_boards:
            mail_data = []
            for item in board.get('items'):
                content = item.get_data({"period": PARSER.get(periodicity)[0], 'team': 0})
                content['name'] = item.name
                mail_data.append(content)
            board_data.append({
                'name': board.get('board_name'),
                'group': board.get('group'),
                'content': mail_data,
                'open_url': '/web#action=%d&menu_id=%d' % (board['action_id'], board['menu_id'])
            })
        return board_data

    @api.model
    def mail_create_and_send(self):
        list_company = self.env['res.company'].search([])
        periodicity = self.periodicity
        saving_company = self.env.company
        periodicity_display = periodicity[0].upper() + periodicity[1:]
        minify_boards = self.minify_board_data()
        last_updated = self.env['bi.dashboard.board'].get_last_updated_time().strftime('%b %d, %H:%M %p')
        minify_users = self.minify_user_data()
        for company in list_company:
            self.env.company = company
            recently, previously = self._compute_timeframes_periodicity(company, periodicity)
            mail_content = self.query_data_source(minify_boards, periodicity)
            time = '%s - %s' % (
                recently[0].strftime('%m/%d/%Y'), recently[1].strftime('%m/%d/%Y')) if periodicity != 'daily' else recently[0].strftime('%m/%d/%Y')
            content = {
                'time': time,
                "mail_content": mail_content,
                'title': 'Omni Dashboard',
                'periodicity': periodicity_display
            }
            self._bi_send_mail_to_user(minify_users, company, content, last_updated)
        self.env.company = saving_company

    def _generate_mail_content(self, user, company, content, last_updated):
        web_base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        currency = self.env.company.currency_id
        rendered_body = self.env['mail.render.mixin']._render_template(
            'odoo_dashboard_builder.bi_dashboard_digest_email',
            'bi.dashboard.item',
            self.ids,
            engine='qweb',
            add_context={
                'mail_content': content.get("mail_content"),
                'title': content.get('title'),
                'periodicity': content.get('periodicity'),
                'top_button_url': url_join(web_base_url, '/web/login'),
                'unsubscribe_id': self.id,
                'company': company.name,
                'sub_title': self.name,
                'last_updated': last_updated,
                'formatted_date': datetime.now().strftime('%b %d, %H:%M %p'),
                'check_user_group': lambda x: self.check_user_group(user.get('id'), x),
                'currency_conversion': lambda value, format='percent', custom_unit='': self.currency_conversion(value, format, currency, custom_unit)
            },
            post_process=True
        )[self.id]
        full_mail = self.env['mail.render.mixin']._render_encapsulate(
            'odoo_dashboard_builder.bi_dashboard_digest_layout',
            rendered_body,
            add_context={
                'company': company,
            },
        )
        mail_template = full_mail
        return mail_template

    def _bi_send_mail_to_user(self, minify_users, company, content, last_updated):
        for user in minify_users:
            if company.id not in user.get('company_ids'):
                continue
            mail_template = self._generate_mail_content(user, company, content, last_updated)
            self._bi_send_mail(user, company, mail_template, content.get('time'))

    def _bi_send_mail(self, user, company, full_mail, time):
        mail_values = {
            'subject': '%s: %s (%s)' % (company.name, self.name, time),
            'email_from': company.partner_id.email_formatted,
            'email_to': user['email_formatted'],
            'body_html': full_mail,
            'auto_delete': True,
        }
        mail = self.env['mail.mail'].sudo().create(mail_values)
        mail.send(raise_exception=False)
        return True
