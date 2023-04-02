# Copyright © 2021 odoo, LLC
# See LICENSE file for full copyright and licensing details.

from os.path import join, dirname
import json

geo_file_location = {
    'usa': '../static/src/json/states-10m.json',
    'world': '../static/src/json/countries-50m.json',
}


def get_geo_file_location(view_mode='usa'):
    file_path = geo_file_location.get(view_mode)
    if not file_path:
        file_path = geo_file_location.get('world', '')
    return file_path


def get_projection_mode(view_mode='usa'):
    if view_mode == 'usa':
        return 'albersUsa'
    return 'equalEarth'


def load_location_json(file_path):
    if not file_path:
        return {}
    path = join(dirname(__file__), file_path)
    try:
        file = open(path, 'rb')
        data = json.load(file)
        file.close()
        return data
    except Exception:
        return {}
