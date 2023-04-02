# Copyright © 2021 odoo, LLC
# See LICENSE file for full copyright and licensing details.

from odoo import fields
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re


def _get_date_group_by(self, period_type, field, order=''):
    group_by_stmt = ''
    select_stmt = ''
    order_stmt = ''
    if period_type == 'day':
        group_by_stmt = "date_part('day', {field}), date_part('month', {field}), date_part('year', {field})".format(
            field=field)
        select_stmt = "CONCAT(TO_CHAR(TO_DATE(date_part('month', {field})::text, 'MM'), 'Mon'), ' ', date_part('day', {field})) as {field}".format(
            field=field)
        order_stmt = "date_part('year', {field}) {order}, date_part('month', {field}) {order}, date_part('day', {field}) {order}".format(
            field=field, order=order)
    elif period_type == 'week':
        week_start = -(int(self.env['res.lang']._lang_get(self.env.user.lang).week_start) % 7) + 1
        group_by_stmt = "date_trunc('week', {field}::date + {week_start})::date - {week_start}".format(field=field,
                                                                                                       week_start=week_start)
        select_stmt = "CONCAT(TO_CHAR(TO_DATE(date_part('month', date_trunc('week', {field}::date + {week_start})::date - {week_start})::text, 'MM'), 'Mon'), ' ', date_part('day', date_trunc('week', {field}::date + {week_start})::date - {week_start})) as {field}".format(
            field=field, week_start=week_start)
        order_stmt = "date_trunc('week', {field}::date + {week_start})::date - {week_start} {order}".format(field=field,
                                                                                                            week_start=week_start,
                                                                                                            order=order)
    elif period_type == 'month':
        group_by_stmt = "date_part('month', {field}), date_part('year', {field})".format(field=field)
        select_stmt = "CONCAT(TO_CHAR(TO_DATE(date_part('month', {field})::text, 'MM'), 'Mon'), ' ', date_part('year', {field})) as {field}".format(
            field=field)
        order_stmt = "date_part('year', {field}) {order}, date_part('month', {field}){order}".format(field=field,
                                                                                                     order=order)
    elif period_type == 'quarter':
        group_by_stmt = "date_part('quarter', {field}), date_part('year', {field})".format(field=field)
        select_stmt = "CONCAT('Q',date_part('quarter', {field}), ' ', date_part('year', {field})) as {field}".format(
            field=field)
        order_stmt = "date_part('year', {field}) {order}, date_part('quarter', {field}) {order}".format(field=field,
                                                                                                        order=order)
    elif period_type == 'year':
        group_by_stmt = "date_part('year', {field})".format(field=field)
        select_stmt = "date_part('year', {field}) as {field}".format(field=field)
        order_stmt = "date_part('year', {field}) {order}".format(field=field, order=order)
    
    return select_stmt, group_by_stmt, order_stmt


def _get_date_period(self, period):
    start_date, end_date = _get_date_time_period(self, period)
    return start_date.date(), end_date.date()


def _get_date_time_period(self, period):
    today = fields.Datetime.now()
    quarter = int((today.month - 1) / 3) + 1
    start_date = today
    end_date = today
    if period == 'today':
        return start_date, end_date
    elif period == 'yesterday':
        yesterday = today - relativedelta(days=1)
        return yesterday, yesterday
    elif period == 'this_week':
        week_start = -(int(self.env['res.lang']._lang_get(self.env.user.lang).week_start) % 7) + 1
        base_date = today + relativedelta(days=week_start)
        start_date = base_date - relativedelta(days=base_date.weekday() + week_start)
        end_date = start_date + relativedelta(days=6)
    elif period == 'last_week':
        week_start = -(int(self.env['res.lang']._lang_get(self.env.user.lang).week_start) % 7) + 1
        base_date = today + relativedelta(days=week_start)
        start_date = base_date - relativedelta(days=base_date.weekday() + 7 + week_start)
        end_date = start_date + relativedelta(days=6)
    elif period == 'this_month':
        start_date = datetime.strptime('{}/01/{}'.format(today.month, today.year), '%m/%d/%Y')
        end_date = start_date + relativedelta(months=1, days=-1)
    elif period == 'last_month':
        start_date = datetime.strptime('{}/01/{}'.format(today.month, today.year), '%m/%d/%Y') - relativedelta(
            months=1)
        end_date = start_date + relativedelta(months=1, days=-1)
    elif period == 'this_quarter':
        start_date = datetime(today.year, 3 * quarter - 2, 1)
        end_date = start_date + relativedelta(days=-1, months=3)
    elif period == 'last_quarter':
        start_date = datetime(today.year, 3 * quarter - 2, 1) - relativedelta(months=3)
        end_date = start_date + relativedelta(days=-1, months=3)
    elif period == 'this_year':
        start_date = datetime.strptime('01/01/{}'.format(today.year), '%m/%d/%Y')
        end_date = start_date + relativedelta(months=12, days=-1)
    elif period == 'last_year':
        start_date = datetime.strptime('01/01/{}'.format(today.year - 1), '%m/%d/%Y')
        end_date = start_date + relativedelta(months=12, days=-1)
    elif period == 'last_7_days':
        start_date = today + relativedelta(days=-6)
    elif period == 'last_30_days':
        start_date = today + relativedelta(days=-29)
    elif period == 'last_90_days':
        start_date = today + relativedelta(days=-89)
    elif period == 'last_12_months':
        start_date = today + relativedelta(years=-1)
    return start_date, end_date


def _get_last_period(start_date, end_date, period):
    if not (start_date and end_date):
        return '', ''
    last_end_date = start_date - relativedelta(days=1)
    if 'year' in period:
        last_start_date = start_date - relativedelta(years=1)
    elif 'month' in period:
        last_start_date = start_date - relativedelta(months=1)
    elif 'week' in period:
        last_start_date = start_date - relativedelta(weeks=1)
    elif 'quarter' in period:
        last_start_date = start_date - relativedelta(months=3)
    elif 'day' in period:
        result = re.search('last_(.*)_days', period)
        num_days = result and result.group(1) and int(result.group(1)) or 1
        last_start_date = start_date - relativedelta(days=num_days)
    else:
        interval_days = (end_date - start_date).days
        last_start_date = start_date - relativedelta(days=interval_days + 1)
    return last_start_date, last_end_date


def _get_interval_selection(start_date, end_date, period):
    number_of_days = (end_date - start_date).days
    interval = []
    if number_of_days <= 7 or period in ['this_week', 'last_week', 'last_7_days']:
        interval.extend([('day', 1)])
    elif number_of_days <= 30 or period in ['this_month', 'last_month', 'last_30_days']:
        interval.extend([('day', 1), ('week', 1)])
    elif number_of_days <= 90 or period in ['this_quarter', 'last_quarter', 'last_90_days']:
        interval.extend([('week', 1), ('month', 1)])
    elif number_of_days <= 365 or period in ['this_year', 'last_year', 'last_12_months']:
        interval.extend([('week', 1), ('month', 1), ('month', 3)])
    else:
        interval.extend([('week', 1), ('month', 1), ('month', 3), ('day', 365)])

    labels = []
    for segment in interval:
        pretag = "At least once "
        if len(segment) == 2:
            if segment[0] == 'day':
                if segment[1] == 1:
                    labels.append("Everyday")
                if segment[1] == 365:
                    labels.append(pretag + "a Year")
            elif segment[0] == 'week':
                labels.append(pretag + "a Week")
            elif segment[0] == 'month':
                if segment[1] == 1:
                    labels.append(pretag + "a Month")
                if segment[1] == 3:
                    labels.append(pretag + "a Quater")
            else:
                labels.append("Others")
        else:
            labels.append("Others")
    labels.append("Others")
    return interval, labels
