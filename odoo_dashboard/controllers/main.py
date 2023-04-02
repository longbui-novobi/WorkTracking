# Copyright © 2021 odoo, LLC
# See LICENSE file for full copyright and licensing details.

import io
from odoo import http, fields, _
from odoo.http import request, content_disposition
import json
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
try:
    import xlrd

    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None


class ListViewItemExport(http.Controller):

    @http.route(['/dashboard_builder/list_view/extract'], type='http', methods=['POST'])
    def download_xlsx(self, data):
        data = json.loads(data)
        item_id = data.get('item_id',0) or 0
        dashboard_item = request.env['bi.dashboard.item'].browse(item_id)
        time_range = ""
        if isinstance(data.get('config_id', 0) or 0, int):
            item_config = request.env['bi.dashboard.item.config'].sudo().browse(data.get('config_id', 0) or 0)
            period = data.get('filter_configs', "").get('period','')
            start_date, end_date = item_config.board_config_id.get_date_range_from_period(period)
            time_range = f"{start_date} - {end_date}"
        report_name = f"{dashboard_item.name}, {time_range}.xlsx"
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', content_disposition(report_name))
            ]
        )
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(dashboard_item.name)
        header_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'top',
            'bold': True,
            'align': 'center'
        })
        text_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'top'
        })
        content = self.load_content(data, dashboard_item)
        self.make_xlsx(sheet, header_format, text_format, content)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
        return response

    def load_content(self, data, dashboard_item):
        config_id = data.get('config_id', 0) or 0
        filter_configs = data.get('filter_configs', "") or ""
        if 'current_page' not in data and 'range' in filter_configs:
            filter_configs['range'] = '1-100000000000'
        return dashboard_item.get_data(filter_configs, config_id)

    def make_xlsx(self, sheet, header_format, text_format, content):
        headers = content.get('head', [])
        fields = content.get('field', [])
        field_type = content.get('type', {})
        body = content.get('content')
        func_dict = {}

        for field in fields:
            if field_type.get(field, '')[1] == 'cell_monetary':
                symbol = u'{symbol}'.format(symbol=request.env.company.currency_id.symbol or '')
                pre = request.env.company.currency_id.position == 'before'
                post = symbol if not pre else ''
                pre = symbol if pre else ''
                func_dict[field] = lambda x, prefix=pre, postfix=post: u'{pre}{data:.2f}{post}'.format(data=(x or 0.0), pre=prefix, post=postfix)
            elif field_type.get(field, '')[1] == 'cell_percent':
                func_dict[field] = (lambda x: "{percent:.2f}%".format(percent=100*(x or 0.0)))
            else:
                func_dict[field] = lambda x: x

        for index, header in enumerate(headers):
            sheet.write(0, index, header, header_format)

        for row_index, row in enumerate(body):
            for col_index, column in enumerate(fields):
                data = func_dict[column](row['data'].get(column, ''))
                sheet.write(row_index+1, col_index, data, text_format)
        return sheet