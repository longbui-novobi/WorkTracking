odoo.define('odoo_dashboard.ListViewCell', function (require) {
    'use strict';
    /*
    Return a function
     */

    function _formatCurrencyValue(value, currency = 'USD', style = 'currency') {
        if (value !== null) {
            return value.toLocaleString("en-US", {
                style: style,
                currency: currency,
                minimumFractionDigits: 0,
                maximumFractionDigits: 2,
                notation: 'compact',
            })
        }
        return ""
    }

    async function Standard(data, key, relation, lineData) {
        if (relation[0] == 'number') {
            data = _formatCurrencyValue(data, 'USD', 'decimal')
        }
        let res = ((data === false || data === undefined || data === null)? (''): (data));
        return [`<td class="o_data_cell o_field_cell " title="${res}">${(res) ? (res) : ''}</td>`, String(data).length];
    }

    
    async function CellPercent(data, key, relation, lineData) {
        if (relation[0] == 'number') {
            data = _formatCurrencyValue(data, 'USD', 'percent')
        }
        return [`<td class="o_data_cell o_field_cell o_field_number" title="${data}">${(data) ? (data) : ''}</td>`, String(data).length]
    }

    async function CellMonetary(data, key, relation, lineData) {
        data = _formatCurrencyValue(data, lineData.widget[relation[2]]);
        return [`<td class="o_data_cell o_field_cell o_field_number" title="${data}">
                    <span class="o_field_monetary o_field_number">${data}</span>
                </td>`, String(data).length]
    }

    async function CellImage(data, key, relation, lineData) {
        let t = ''
        if (lineData.widget[relation[2]]) {
            t = `<span>
                <img src="data:image/png;base64,${lineData.widget[relation[2]]}" class="cell_sub_img"/>
            </span>`
        }
        return [`<td class="o_data_cell o_field_cell o_name_image_url_cell" title="${data}">
            ${t}
            ${data}
        </td>`, String(data).length + 2.5]
    }

    return {
        'standard': Standard,
        'cell_monetary': CellMonetary,
        'cell_image': CellImage,
        'cell_percent': CellPercent
    }

})