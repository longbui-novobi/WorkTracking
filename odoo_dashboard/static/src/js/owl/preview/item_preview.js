odoo.define('odoo_dashboard_builder.DashboardItemPreview', function (require) {
    "use strict";

    var registry = require('web.field_registry');
    var AbstractField = require('web.AbstractField');
    var core = require('web.core');
    var field_utils = require('web.field_utils');
    var session = require('web.session');
    var utils = require('web.utils');
    var BasicModel = require('web.BasicModel')

    var ItemOwl = require('odoo_dashboard_builder.DashboardItem')

    class PreviewItemOwl extends ItemOwl {
        constructor(parent, params, generalFilters = {}, status = false) {
            super(null, params, generalFilters, status);
            this.parent = parent;
        }

        onItemMounted() {
            this.updateItemContent(this.parent.__getRawData())
        }

        updateItemContent(rawMaterial) {
            var self = this;
            if (!rawMaterial){
                rawMaterial = this.parent.__getRawData()
            }
            this.requestContent(rawMaterial).then(function (data) {
                if (data != false) {
                    self.content.updateContent(data);
                    self.el.style.display = 'inline-block';
                }
            });
        }

        requestContent(rawMaterials) {
            return this.rpc({
                model: 'bi.dashboard.item',
                method: 'get_preview_data',
                args: rawMaterials
            })
        }
    }

    const defaultTemplateSize = {
        'kpi': { width: 3, height: 5 },
        'chart': { width: 6, height: 10 },
        'mixed': { width: 5, height: 8 },
        'gauge_mixed': { width: 6, height: 10 },
        'list': { width: 6, height: 10 },
        'default': { width: 3, height: 5 }
    }
    var OmniItemPreview = AbstractField.extend({
        resetOnAnyFieldChange: true,
        noLabel: true,
        template: "odoo_dashboard_builder.ItemPreview",

        jsLibs: [
            '/web/static/lib/Chart/Chart.js',
            '/odoo_dashboard_builder/static/lib/js/chartjs-plugin-datalabels.min.js',
            '/odoo_dashboard_builder/static/lib/js/Chart.Geo.min.js',
            '/odoo_dashboard_builder/static/lib/js/gauge.js',
        ],
        init: function (parent, params) {
            this._super.apply(this, arguments);
            this.isLoaded = false;
            this.config = {};
            this.onEdit = ((this.mode === 'readonly') ? false : true);
        },
        start: function () {
            this._super.apply(this, arguments);
        },
        _getNewRecordInfo: function(virtualData){
            let outputVirtual = [];
            for (let record of virtualData) {
                let insideData = record.data;
                let insideControl = record.fields;
                if (typeof (record.ref) === 'string') {
                    let outputData = {};
                    for (let insideKey in insideData) {
                        if (insideControl[insideKey].store !== false) {
                            if (insideData[insideKey].constructor === Object) {
                                outputData[insideKey] = insideData[insideKey].ref
                            }
                            else {
                                outputData[insideKey] = insideData[insideKey]
                            }
                        }
                    }
                    outputVirtual.push([0, record.ref, outputData])
                }
                else {
                    outputVirtual.push([4, record.ref, false])
                }
            }
            return outputVirtual
        },
        __extractDataToNew(vals) {
            for (let key in vals) {
                if (vals[key].constructor === Object) {
                    let data = vals[key]
                    if (data.type === 'list') {
                        if (data.res_ids.some((element) => typeof (element) === "string")) {
                            vals[key] = this._getNewRecordInfo(data.data);
                        }
                        else {
                            vals[key] = [[6, false, data.res_ids]]
                        }
                    }
                    else if (data.type === 'record') {
                        vals[key] = data.res_id;
                    }
                }
            }
            return vals
        },
        __getRawData() {
            let vals = JSON.parse(JSON.stringify(this.recordData));
            return [
                this.__extractDataToNew(vals),
                { 'period': 'this_month' },
                this.onEdit
            ]
        },

        __intersectConfig: function (now, org) {
            this.config.isTitleChange = false;
            this.config.isKpiImageChange = false;
            this.isContentChange = false;
            if (now.layout_template === 'kpi' && now.kpi_img_b64 != this.config.kpi_icon) {
                this.config.isKpiImageChange = true;
                if (!utils.is_bin_size(now.kpi_img_b64)) {
                    this.config.kpi_icon = now.kpi_img_b64;
                }
            }
            if (now.layout_template !== org.layout_template) {
                this.config.layoutConfig = defaultTemplateSize[now.layout_template] || defaultTemplateSize['default'];
            } else {
                this.config.layoutConfig = org.layoutConfig;
            }
            this.config.template = now.layout_template;
            if (now.name != this.config.info.title || now.description != this.config.info.description) {
                this.config.isTitleChange = true;
                this.config.info = now;
            }
            this.el.style.height = (this.config.layoutConfig.height * 40 || 200) + 'px';
        },
        _render: function () {
            this.el.classList.remove('o_field_widget');
            if (this.isLoaded && this.recordData.layout_template === this.config.template) {
                this.__intersectConfig(this.recordData, this.baseConfig);
                this._reloadItemContent();
            } else {
                this.renderPreviewItem();
            }
        },
        _reloadItemContent: function () {
            if (this.config.isTitleChange || this.config.isKpiImageChange)
                this.item.updateItemState(this.config);
            this.item.updateItemContent(this.__getRawData());
        },
        renderPreviewItem() {
            if (this.recordData.layout_template) {
                this.isLoaded = true;
                if (this.item) this.item.unmount()
                let self = this;
                this._rpc(
                    {
                        model: 'bi.dashboard.item',
                        method: 'get_dashboard_item_preview_layout_config',
                        args: [self.recordData, self.model],
                    })
                    .then(async default_value => {
                        self.baseConfig = default_value;
                        self.config = _.clone(default_value);
                        self.el.style.height = (default_value.layoutConfig.height * 40 || 200) + 'px';
                        self.item = new PreviewItemOwl(self, default_value, { 'period': 'this_month' }, false);
                        await self.item.mount(self.el)
                        self.item.el.style.display = 'inline-block';
                        self.$el.attr('class', 'preview show ' + self.recordData.layout_template)
                    });
            }
        }
    })


    registry.add('omni_dashboard_preview', OmniItemPreview);

    return {
        OmniItemPreview: OmniItemPreview
    };
})
