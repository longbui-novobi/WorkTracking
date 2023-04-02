# Copyright © 2021 odoo, LLC
# See LICENSE file for full copyright and licensing details.


def get_default_item_size(item_type):
    if item_type == 'kpi':
        width = min_width = 3
        height = min_height = 5
    elif item_type == 'chart' or item_type == 'list':
        width = 6
        height = 10
        min_width = 4
        min_height = 7
    else:
        width = 5
        height = 7
        min_width = 3
        min_height = 5
    return {
        'width': width,
        'height': height,
        'min_width': min_width,
        'min_height': min_height,
    }


def get_db_field_type(ttype):
    db_type = ttype
    if ttype == 'many2one' or ttype == 'boolean':
        db_type = 'integer'
    elif ttype == 'datetime':
        db_type = 'date'
    elif ttype == 'selection' or ttype == 'char':
        db_type = 'varchar'
    elif ttype == 'monetary':
        db_type = 'float'
    return db_type
