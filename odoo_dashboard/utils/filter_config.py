# Copyright © 2021 odoo, LLC
# See LICENSE file for full copyright and licensing details.

FILTER_2_TARGET = {
    'today': 'daily',
    'yesterday': 'daily',
    'this_week': 'weekly',
    'last_week': 'weekly',
    'last_7_days': 'weekly',
    'this_month': 'monthly',
    'last_month': 'monthly',
    'last_30_days': 'monthly',
    'this_quarter': 'quarterly',
    'last_quarter': 'quarterly',
    'last_90_days': 'quarterly',
    'this_year': 'annually',
    'last_year': 'annually',
    'custom_period': False
}


def detect_target(self, filters={}):
    period = FILTER_2_TARGET.get(filters.get('period', False), False)
    is_target, target_value = False, False
    if period and isinstance(self.id, int):
        target_id = self.target_kpi_ids.filtered(
            lambda x: x.period == period)
        if len(target_id) > 0:
            is_target = True
            target_value = target_id.target
    return is_target, target_value


def get_filter_config(self, type):
    config = {}
    if type == 'team':
        config = get_team_filter_config(self)
    elif type == 'period':
        config = get_period_filter_config(self)
    elif type == 'periodical':
        config = get_periodical_filter_config(self)
    elif type == 'location':
        config = get_location_filter_config(self)
    elif type == 'revenue':
        config = get_revenue_filter_config(self)
    elif type == 'team_break':
        config = get_team_break_filter_config(self)
    elif type == 'product_by':
        config = get_product_by_filter_config(self)
    elif type == 'product_segment':
        config = get_product_segment_filter_config(self)
    elif type == 'customer_segment':
        config = get_customer_segment_filter_config(self)
    return config


def get_team_filter_config(self):
    return {
        'line_icon': False,
        'options': self.env['bi.dashboard.item'].get_sales_team(),
        'icon': 'fa-university',
    }


def get_period_filter_config(self):
    return {
        'line_icon': False,
        'options': {
            'today': 'Today',
            'this_week': 'This Week',
            'this_month': 'This Month',
            'this_quarter': 'This Quarter',
            'this_year': 'This Year',
            'hrl#1': '',
            'yesterday': 'Yesterday',
            'last_week': 'Last Week',
            'last_month': 'Last Month',
            'last_quarter': 'Last Quarter',
            'last_year': 'Last Year',
            'hrl#2': '',
            'last_7_days': 'Last 7 Days',
            'last_30_days': 'Last 30 Days',
            'last_90_days': 'Last 90 Days',
            'hrl#3': '',
            'custom_period': 'Custom Period'
        },
        'icon': 'fa-calendar',
    }


def get_periodical_filter_config(self):
    return {
        'line_icon': False,
        'options': {
            'day': 'By Day',
            'week': 'By Week',
            'month': 'By Month',
            'quarter': 'By Quarter',
            'year': 'By Year'
        },
        'icon': 'fa-calendar',
    }


def get_location_filter_config(self):
    return {
        'line_icon': False,
        'options': self.env['bi.dashboard.item'].get_locations(),
        'icon': 'fa-map-marker',
    }


def get_revenue_filter_config(self):
    return {
        'line_icon': False,
        'options': {
            'team': 'By Sales Team',
            'product': 'By Product',
            'product_category': 'By Product Category',
            'location': 'By Location',
        },
        'icon': 'fa-filter',
    }


def get_team_break_filter_config(self):
    return {
        'line_icon': False,
        'options': {
            'team': 'By Sales Team',
            'total': 'By Total',
        },
        'icon': 'fa-filter',
    }


def get_product_by_filter_config(self):
    return {
        'line_icon': False,
        'options': {
            'revenue': 'By Revenue',
            'quantity': 'By Units Sold',
        },
        'icon': 'fa-filter',
    }


def get_product_segment_filter_config(self):
    return {
        'line_icon': False,
        'options': {
            'revenue': 'High Sales Revenue',
            'unit_sold': 'High Units Sold',
            'margin': 'High Sales Margin',
            'order': 'Most Ordered',
            'discount': 'Most Discounted'
        },
        'icon': 'fa-filter',
    }


def get_customer_segment_filter_config(self):
    return {
        'line_icon': False,
        'options': {
            'new': 'New Customers',
            'returning': 'Returning Customers',
            'lost': 'Lost Customers',
            'recent_purchase': 'Recent Purchase',
            'lov_aov': 'Low AOV Customers',
            'high_aov': 'High AOV Customers',
        },
        'icon': 'fa-filter',
    }
