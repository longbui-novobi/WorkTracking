# Copyright © 2021 odoo, LLC
# See LICENSE file for full copyright and licensing details.

QUOTATION_COLOR = '#38DF64'
QUOTATION_DEMO_COLOR = 'rgba(224,224,224,0.6)'
SALES_ORDER_COLOR = '#27AE60'
SALES_ORDER_DEMO_COLOR = 'rgba(200,200,200,0.6)'
SALE_ORDER_BG_COLOR = 'rgba(39,174,96,0.5)'
SALES_ORDER_DEMO_COLOR = 'rgba(189,189,189,0.6)'
SALE_ORDER_DEMO_BG_COLOR = 'rgba(224,224,224,0.6)'
CANCELED_ORDER_COLOR = '#FF9200'
CANCELED_ORDER_DEMO_COLOR = 'rgba(160,160,160,0.6)'
SHIPPING_COST_COLORS = ['#FF9200', '#3F92D2', '#ffcc00', '#BDBDBD']
SHIPPING_COST_DEMO_COLORS = ['rgba(224,224,224,0.6)', 'rgba(200,200,200,0.6)', 'rgba(189,189,189,0.6)',
                             'rgba(150,150,150,0.6)']
CUSTOMER_FREQUENCY_COLORS = ['#0094d2', '#00a3a0', '#00c243', '#00e28c']
CUSTOMER_FREQUENCY_DEMO_COLORS = ['rgba(224,224,224,0.6)', 'rgba(200,200,200,0.6)', 'rgba(189,189,189,0.6)',
                                  '#cacaca', '#c0c0c0']

SHOPIFY_COLORS = ['#64DF85', '#00BF32', '#248F40', '#6FCF97', '#007C21']
BIGCOMMERCE_COLORS = ['#66A3D2', '#0B61A4', '#033E6B', '#56CCF2', '#2F80ED']
TEAM_COLORS = ['#38DF64', '#3F92D2', '#FF9200', '#F2C94C', '#00BF32', '#0B61A4', '#FFC373', '#FF8373', '#2F80ED',
               '#007C21', '#D8FA3F', '#21825B', '#F26D93', '#AC2B50', '#36D695']
TEAM_DEMO_COLORS = ['rgba(224,224,224,0.6)', 'rgba(200,200,200,0.6)', 'rgba(180,180,180,0.6)', 'rgba(160,160,160,0.6)',
                    'rgba(150,150,150,0.6)', 'rgba(140,140,140,0.4)', 'rgba(130,130,130,0.4)', 'rgba(120,120,120,0.4)',
                    'rgba(110,110,110,0.4)', 'rgba(100,100,100,0.4)', 'rgba(90,90,90,0.4)', 'rgba(80,80,80,0.4)',
                    'rgba(70,70,70,0.4)', 'rgba(60,60,60,0.4)', 'rgba(50,50,50,0.4)']


def get_team_color(sales_team_ids):
    colors = {}
    for index, team_id in enumerate(sales_team_ids):
        colors[team_id] = TEAM_COLORS[index % len(TEAM_COLORS)]
    return colors


def get_team_demo_color(sales_team_ids):
    colors = {}
    for index, team_id in enumerate(sales_team_ids):
        colors[team_id] = TEAM_DEMO_COLORS[index % len(TEAM_DEMO_COLORS)]
    return colors
