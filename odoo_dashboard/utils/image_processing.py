# Copyright © 2021 odoo, LLC
# See LICENSE file for full copyright and licensing details.

import base64
import odoo.modules as module


def image_path_2_base64(path):
    if path:
        rear = path.split('/')[1: ]
        if len(rear) > 0:
            front = module.get_module_path(rear[0])
            if front:
                with open(front + "/" + "/".join(rear[1:]), "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read())
                return encoded_string
    return ''


def find_vacancy_area(configs, new_items):
    x_max = configs.get("columns")
    y_max = configs.get("rows")
    items = configs.get('items')
    new_w = int(new_items[0])
    new_h = int(new_items[1])
    
    layer = [[0 for col in range(x_max)] for row in range(y_max)]
    for item in items:
        x0, y0, w, h = item.values()
        for x in range(w):
            for y in range(h):
                layer[y0 + y][x0 + x] = 1
    y = 0
    while y < y_max - new_h + 1:
        x = 0
        while x < x_max - new_w + 1:
            if layer[y][x] == 0:
                b2 = True
                for px in range(new_w):
                    for py in range(new_h):
                        if layer[y + py][x + px] == 1:
                            b2 = False
                            break
                if b2:
                    return [x, y]
                if (y + new_h) < y_max:
                    y += new_h
                    x = 0
                else:
                    y = y_max
                    break
            x += 1
        y += 1
    return [0, y_max + 1]
