odoo.define('odoo_dashboard_builder.DashboardItemTemplate', function (require) {
    "use strict";

    const { Component } = owl;
    const { useState, useRef } = owl.hooks;

    var ItemListCell = require('odoo_dashboard_builder.ListViewCell')
    var ItemSubComponents = require('odoo_dashboard_builder.DashboardItemSubcomponents');
    var ItemTitleFrame = ItemSubComponents.ItemTitleFrame;
    var ItemNavigation = ItemSubComponents.ItemNavigation;
    var ItemTitle = ItemSubComponents.ItemTitle;

    class GridElementContentBase extends Component {
        state = useState(this.props);

        constructor(parent, props) {
            super(parent, props);
            this.parent = parent;
            this.props = props;
            this.state.lastUpdated = this.env.lastUpdated;
            this.baseWidth = parent.layoutConfig.width || 3;
            this.baseHeight = parent.layoutConfig.height || 5;
            this.state['formatStyle'] = 'decimal';
            this.state['currency'] = 'USD';
            this.state['xAxesFormatStyle'] = 'none';
            this.state['yAxesFormatStyle'] = 'decimal';
            this.state['customUnitStyle'] = '';
            this.initParameter(props);
            this.__appendBase(parent);
        }

        mounted() {
            super.mounted();
            this.trigger('item-mounted');
        }

        initParameter(params) {
            this.chart = false;
        }

        updateContent(data) {
            // this.state.lastUpdated = this.env.lastUpdated;
        }

        updateSalesTeam(team) {
            this.state['team'] = team;
        }

        __appendBase(parent) {
            let gridElement = $(parent.el);
            gridElement.attr('b-w', this.baseWidth || 3);
            gridElement.attr('b-h', this.baseHeight || 5);
        }

        _formatCurrencyValue(value, style = 'currency', currency = 'USD', notation = 'compact') {
            var minimumFractionDigits = 0;
            var maximumFractionDigits = 2;
            switch (style) {
                case 'currency':
                    minimumFractionDigits = 2;
                case 'decimal':
                case 'percent':
                    return value.toLocaleString("en-US", {
                        style: style,
                        currency: this.state.currency,
                        minimumFractionDigits: minimumFractionDigits,
                        maximumFractionDigits: maximumFractionDigits,
                        notation: notation,
                    });
                case 'custom':
                    return value.toLocaleString("en-US", {
                        style: 'decimal',
                        currency: this.state.currency,
                        minimumFractionDigits: minimumFractionDigits,
                        maximumFractionDigits: maximumFractionDigits,
                        notation: notation,
                    }) + " " + this.state.customUnitStyle;
            }
        }

        formatChartConfig(config) {
            if (config.type == 'choropleth') {
                config = this.formatGeoChart(config);
            } else if (config.type == 'gauge') {
                return this.formatGaugeChart(config);
            }
            return this.formatChartValue(config);
        }

        formatChartValue(config) {
            let self = this;
            let tooltip = {
                custom: (tooltipModel) => {
                    let legend = config && config.options && config.options.legend || {};
                    if (legend && legend.reverse && Array.isArray(tooltipModel.body) && Array.isArray(tooltipModel.labelColors)) {
                        tooltipModel.body.reverse();
                        tooltipModel.labelColors.reverse();
                    }
                },
                callbacks: {
                    title: (tooltipItems, data) => {
                        var axis_label;
                        try {
                            axis_label = config.options.scales.xAxes[0].scaleLabel.labelString ? config.options.scales.xAxes[0].scaleLabel.labelString + ": " : ""
                        } catch (err) {
                            axis_label = ''
                        }
                        var title = config.type === 'horizontalBar' ? tooltipItems[0].label : tooltipItems[0].xLabel;
                        return title ? axis_label + title : title;
                    },
                    label: (tooltipItem, data) => {
                        var label = '';
                        var value = 0;
                        if (config.type == 'choropleth') {
                            label = data.labels[tooltipItem.index] + ': ';
                            value = data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index]['value'] || 0;
                        } else if (config.type == 'pie' || config.type == 'doughnut') {
                            label = data.labels[tooltipItem.index] + ': ';
                            value = data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index] || 0;
                        } else if (config.type == 'polarArea') {
                            label = data.labels[tooltipItem.index] + ': ';
                            value = data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index] || 0;
                        } else {
                            label = data.datasets[tooltipItem.datasetIndex].label + ': ';
                            value = data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index] || 0;
                        }

                        let sum = data.datasets[tooltipItem.datasetIndex].data.reduce((a, b) => a + b);
                        let percentage = (value * 100 / sum).toFixed(2);
                        value = self._formatCurrencyValue(value, self.state.formatStyle, self.state.currency);
                        return (config.type == 'pie' || config.type == 'doughnut') ? label + value + ' (' + percentage + '%)' : label + value;
                    }
                }
            };

            if (!config.options) {
                config['options'] = {};
            }
            if (!config.options.tooltips) {
                config.options['tooltips'] = {};
            }
            config.options.tooltips['callbacks'] = tooltip.callbacks;
            config.options.tooltips['custom'] = tooltip.custom;
            let xAxisFormatStyle = config.type == 'horizontalBar' && this.state.xAxesFormatStyle || this.state.formatStyle;
            let yAxisFormatStyle = config.type == 'horizontalBar' && this.state.yAxesFormatStyle || this.state.formatStyle;
            let x_axis_config = {
                callback: (value, index, values) => {
                    if (!isNaN(parseFloat(value))) {
                        return self._formatCurrencyValue(value, xAxisFormatStyle, self.state.currency);
                    }
                    if (typeof value == 'string') {
                        let label = value.length > 20 ? value.substring(0, 20) + "..." : value;
                        return label
                    }
                    return value;
                }
            };

            let y_axis_config = {
                callback: (value, index, values) => {
                    if (!isNaN(parseFloat(value))) {
                        return self._formatCurrencyValue(value, yAxisFormatStyle, self.state.currency);
                    }
                    if (typeof value == 'string') {
                        let label = value.length > 20 ? value.substring(0, 20) + "..." : value;
                        return label
                    }
                    return value;
                }
            };
            if (!['pie', 'doughnut', 'choropleth', 'polarArea', 'radar'].includes(config.type)) {
                if (!config.options.scales) {
                    config.options['scales'] = {
                        'xAxes': [{ display: true }],
                        'yAxes': [{ display: true }]
                    }
                }
                var x_axes = config.options.scales.xAxes || [];
                var y_axes = config.options.scales.yAxes || [];
                for (var axis of x_axes) {
                    if (xAxisFormatStyle != 'none') {
                        if (axis.ticks) {
                            axis.ticks['callback'] = x_axis_config.callback;
                        } else {
                            axis.ticks = {
                                callback: x_axis_config.callback
                            }
                        }
                    }
                }
                for (var axis of y_axes) {
                    if (yAxisFormatStyle != 'none') {
                        if (axis.ticks) {
                            axis.ticks['callback'] = y_axis_config.callback;
                        } else {
                            axis.ticks = {
                                callback: y_axis_config.callback
                            }
                        }
                    }
                }
            }
            if (config.type == 'radar') {
                config.options['scale'] = {
                    ticks: {
                        callback: function (value, index, values) {
                            if (!isNaN(parseFloat(value))) {
                                return self._formatCurrencyValue(value, yAxisFormatStyle, self.state.currency);
                            }
                            return value;
                        }
                    }
                }
            }
            return config
        }

        formatGeoChart(config) {
            let self = this;
            var chartConfig = {};
            let us = config && config.geoData || {};
            if (config && us) {
                try {
                    let state_name = Object.keys(config.values);
                    var states = {};
                    var nation = {};
                    if (config.mode == 'albersUsa') {
                        nation = ChartGeo.topojson.feature(us, us.objects.nation).features[0];
                        states = ChartGeo.topojson.feature(us, us.objects.states).features;
                    } else if (config.mode == 'equalEarth') {
                        states = ChartGeo.topojson.feature(us, us.objects.countries).features;
                    }
                    chartConfig = {
                        type: 'choropleth',
                        data: {
                            labels: states.map((d) => d.properties.name),
                            datasets: [{
                                // outline: nation,
                                data: states.map((d) => {
                                    let name = d.properties.name;
                                    var value = 0;
                                    if (state_name.length > 0) {
                                        let bestMatch = stringSimilarity.findBestMatch(name, state_name);
                                        value = bestMatch.bestMatch.rating > 0.67 && config.values[bestMatch.bestMatch.target] || 0;
                                    }

                                    return {
                                        feature: d,
                                        value: value
                                    };
                                }),
                            }]
                        },
                        options: {
                            legend: {
                                display: false
                            },
                            scale: {
                                projection: config.mode,
                            },
                            geo: {
                                colorScale: {
                                    display: true,
                                    position: 'bottom',
                                    quantize: 5,
                                    legend: {
                                        position: 'bottom-right',
                                    },
                                },
                            },
                            title: {
                                display: false,
                            },
                            maintainAspectRatio: false,
                        },
                    };
                    if (nation) {
                        chartConfig.data.datasets['outline'] = nation;
                    }
                } catch (e) {
                    chartConfig = {};
                }
            }
            return chartConfig;
        }

        formatGaugeChart(config) {
            let self = this;
            config['options'] = {
                needle: {
                    radiusPercentage: 2,
                    widthPercentage: 4.2,
                    lengthPercentage: 90,
                    color: '#a6a6a6'
                },
                valueLabel: {
                    display: true,
                    formatter: (value) => {
                        value = self._formatCurrencyValue(value / 100, 'percent');
                        return value; // Display the value of the needle
                    },
                    color: 'rgba(255, 255, 255, 1)',
                    backgroundColor: '#a6a6a6',
                    borderRadius: 5,
                    padding: {
                        top: 10,
                        bottom: 10
                    }
                },
                maintainAspectRatio: false,
                title: {
                    display: false,
                },
            };
            return config;
        }

        formatChartDefault() {
            Chart.defaults.global.defaultFontColor = '#333';
            Chart.plugins.unregister(ChartDataLabels);
            // Chart.scaleService.updateScaleDefaults('category', {
            //
            // });
        }

    }

    class GridChartElement extends GridElementContentBase {
        canvasRef = useRef("canvas");

        initParameter(params) {
            super.initParameter(params);
            this.baseWidth = 6;
            this.baseHeight = 10;
        }

        constructor(parent, props) {
            super(parent, props);
        }

        mounted() {
            super.mounted(...arguments);
            // let context = this.canvasRef.el.getContext("2d");
            // this.chart = new Chart(context,);
            this.formatChartDefault();
        }

        updateContent(data) {
            super.updateContent(...arguments);
            this.updateChartData(data);
        }

        updateChartData(data) {
            let context = this.canvasRef.el.getContext("2d");
            var config = {};
            if (data) {
                config = data.chart_config;
                this.state.currency = data.currency || 'USD';
                this.state.formatStyle = data.format_style || 'decimal';
                this.state.xAxesFormatStyle = data.x_axes_format_style || 'none';
                this.state.yAxesFormatStyle = data.y_axes_format_style || 'decimal';
                this.state.customUnitStyle = data.custom_unit || '';
                if (data.additional_info){
                    for (let i = 0; i < data.additional_info.length; i++){
                        data.additional_info[i].content = this._formatCurrencyValue(data.additional_info[i].content, data.additional_info[i].format_style || 'decimal', this.state.currency, 'standard');
                    }
                    this.state.additional_info = data.additional_info;
                }
            }
            if (this.chart) {
                this.chart.destroy();
            }
            var chartConfig = this.formatChartConfig(config);
            this.chart = new Chart(context, chartConfig);
        }

        openChartEventFromKey(evt){
            let key = evt.currentTarget.getAttribute('key')
            if (key){
                this.trigger('open-chart-tooltip', key);
            }
        }
    }

    GridChartElement.template = 'GridChartElement';
    GridChartElement.components = { ItemTitleFrame };

    class GridKPIElement extends GridElementContentBase {
        kpiState = useState({
            'thisPeriodValue': '',
            'lastPeriodValue': '',
            'changeValue': '',
            'changeValuePercent': '',
            'trend': 'increase',
            'isGood': true,
            'formatStyle': 'decimal',
            'currency': 'USD',
            'showIndicator': false,
            'iconURL': this.iconUrl
        });

        initParameter(params) {
            super.initParameter(params);
            this.baseWidth = 3;
            this.baseHeight = 5;
        }

        constructor(parent, params) {
            super(parent, params);
            // this.iconUrl = parent.iconUrl;
            this.kpiState.iconUrl = parent.iconUrl;
            this.formatDisplayValue();
        }

        mounted() {
            super.mounted(...arguments);
        }

        updateContent(data) {
            super.updateContent(...arguments);
            this.updateContentData(data);
        }

        updateKpiImage(img) {
            this.kpiState.iconUrl = img;
        }

        updateContentData(data) {
            this.kpiState.thisPeriodValue = data['thisPeriodValue'] || 0;
            this.kpiState.lastPeriodValue = data['lastPeriodValue'] || 0;
            this.kpiState.changeValue = data['changeValue'] || 0;
            this.kpiState.changeValuePercent = data['changeValuePercent'] || 0;
            this.kpiState.trend = data['trend'] || 'increase';
            this.kpiState.isGood = data['isGood'];
            this.kpiState.showIndicator = data['showIndicator'];
            this.kpiState.target = data['target'];
            this.kpiState.isTarget = data['isTarget'];
            this.state.formatStyle = data['formatStyle'] || 'decimal';
            this.state.currency = data['currency'] || 'USD';
            this.state.customUnitStyle = data['custom_unit'] || '';

            if (data['isTarget']) {
                this.kpiState.targetClass = ((data['thisPeriodValue'] > data['target']) ? 'over' : 'under');
                this.targetRatio = (data['thisPeriodValue'] / data['target']) % 100;
            }
            if (this.kpiState.changeValuePercent < 0) {
                this.kpiState.changeValuePercent *= -1;
            }
            this.formatDisplayValue();
        }

        formatDisplayValue() {
            if (this.kpiState.lastPeriodValue != 0) {
                this.kpiState['changeValuePercent'] = this._formatCurrencyValue(this.kpiState.changeValuePercent, 'percent', this.state.currency);
            } else {
                this.kpiState['changeValuePercent'] = '--';
            }
            if (this.kpiState.isTarget) {
                this.kpiState.targetRatio = this._formatCurrencyValue(this.targetRatio, 'percent', this.state.currency);
                this.kpiState.target = this._formatCurrencyValue(this.kpiState.target, this.state.formatStyle, this.state.currency);
            }
            this.kpiState['displayValue'] = this._formatCurrencyValue(this.kpiState.thisPeriodValue, this.state.formatStyle, this.state.currency);
        }

        onClickKPIValue(ev) {
            this.trigger("kpi-value-click");
        }
    }

    GridKPIElement.template = 'GridKPIElement';
    GridKPIElement.components = { ItemNavigation, ItemTitle };


    class GridMixedElement extends GridKPIElement {
        canvasRef = useRef("canvas");

        initParameter(params) {
            super.initParameter(params);
            this.baseWidth = 4;
            this.baseHeight = 7;
        }

        mounted() {
            super.mounted(...arguments);
            this.formatChartDefault();
        }

        updateContent(data) {
            let kpiConfig = data['kpiConfig'] || {};
            super.updateContent(kpiConfig);
            this.updateChartData(data);
        }

        updateChartData(data) {
            data = data || {};
            var config = data.chartConfig || {};
            this.state.formatStyle = data.format_style || 'decimal';
            this.state.xAxesFormatStyle = data.x_axes_format_style || 'none';
            this.state.yAxesFormatStyle = data.y_axes_format_style || 'decimal';
            this.state.customUnitStyle = data.custom_unit || '';
            let context = this.canvasRef.el.getContext("2d");
            if (this.chart) {
                this.chart.destroy();
            }
            var chartConfig = this.formatChartConfig(config);
            this.chart = new Chart(context, chartConfig);
        }
    }

    GridMixedElement.template = 'GridMixedElement';
    GridMixedElement.components = { ItemTitleFrame };

    class GridGaugeElement extends GridKPIElement {
        canvasRef = useRef("canvas");

        initParameter(params) {
            super.initParameter(params);
            this.baseWidth = 4;
            this.baseHeight = 7;
        }

        mounted() {
            super.mounted(...arguments);
            this.formatChartDefault();
        }

        updateContent(data) {
            let kpiConfig = data['kpiConfig'] || {};
            super.updateContent(kpiConfig);
            this.updateChartData(data);
        }

        updateChartData(data) {
            if (data.chartConfig) {
                let context = this.canvasRef.el.getContext("2d");
                if (this.chart) {
                    this.chart.destroy();
                }
                var chartConfig = this.formatChartConfig(data.chartConfig);
                this.chart = new Chart(context, chartConfig);
            }
        }
    }

    GridGaugeElement.template = 'GridGaugeElement';
    GridGaugeElement.components = { ItemTitleFrame };

    class GridListElement extends GridElementContentBase {
        contentRef = useRef("content");
        headerRef = useRef('header');
        noDataRef = useRef('nodata');
        listView = useRef('listview')
        static components = { ItemTitleFrame }

        constructor(parent, props) {
            super(parent, props);
            this.order = false;
            this.nowSort = false;
        }

        updateContent(data) {
            super.updateContent(...arguments);
            this.updateListData(data);
        }

        updateListViewController(max, searchRaw, searchName, demoData) {
            this.state['range'] = { "value": max, 'isDemo': demoData }
            this.state['search'] = { "value": searchRaw, text: searchName }
        }

        resetOrder(){
            this.nowSort = {};
        }

        async updateListData(data) {
            if (data) {
                this.isDemoData = data.options.isDemo;
                this.model = ((data.options.model_id) ? data.options.model_id : data.model_id);
                await this.updateTableData(data.content, data.field, data.type, data.external);
                this.updateHead(data.head, data.field, data.type, data.external);
                this.toggleListStatus(data.options.isDemo);
                if (data.field[0])
                    this.updateListViewController(data.options.maximum, data.field[0], data.head[0], data.options.isDemo)
            }
        }

        toggleListStatus(isDemo) {
            if (isDemo) {
                this.noDataRef.el.classList.remove('o_hidden');
                $(this.listView.el).find('.o_data_row').addClass('o_sample_data_disabled');
            } else {
                this.noDataRef.el.classList.add('o_hidden');
            }
        }


        updateHead(text, raw, type, external) {
            // Text and raw is the list with the same size.
            // Type is the json contain style should be for each text. {raw: [type, widget, relation]}
            // let perEm = document.getElementById('grid-content')
            // perEm = ((!perEm) ? 14 : perEm.style.fontSize);
            // let coeff = 0.5 * parseFloat(perEm);
            // coeff = ((coeff > 6) ? coeff : 6);
            let total = 3.0;
            for (let i = 0; i < raw.length; i++) {
                // let column = type[raw[i]];
                // if (this.headerWidth.noContent) {
                let column_width = 0.0;
                if (this.headerWidth[raw[i]][1] === this.headerWidth[raw[i]][2]){
                    column_width = this.headerWidth[raw[i]][0];
                }
                else{
                    column_width = 0.5*(text[i].length+this.headerWidth[raw[i]][0]);
                }
                total += column_width;
                this.headerWidth[raw[i]] = column_width;
                // } else {
                //     let pivot = this.headerWidth[raw[i]][0];
                //     let isNumber = false;
                //     if (column[0] == 'number' || ['cell_monetary', 'cell_percent'].includes(column[1])) {
                //         pivot = 8;
                //         isNumber = true;
                //     }
                //     let max = ((pivot > text[i].length) ? pivot : text[i].length);
                //     this.headerWidth[raw[i]] = coeff * max;
                //     if (external[raw[i]] && !isNumber) {
                //         this.headerWidth[raw[i]] *= 1.5;
                //     }
                // }
            }
            let pinned_percent = 3/total;
            let res_percent = 1-pinned_percent;
            this.headerRef.el.innerHTML = '';
            let self = this;
            for (let i = 0; i < raw.length; i++) {
                let style = this.__getHeaderStyleClass(type[raw[i]], raw[i])
                let template = document.createElement('template');
                template.innerHTML = `<th  class="o_column_sortable ${style} " title="${text[i]}">${text[i]}</th>`;
                template.content.firstChild.addEventListener('click', e => self._triggerTempOrder(raw[i], e));
                template.content.firstChild.style.width = `${100*res_percent*this.headerWidth[raw[i]]/total}%`;
                this.headerRef.el.append(template.content.firstChild);
            }
            let template = document.createElement('template');
            template.innerHTML = `<th style='width:${100*pinned_percent}%;text-overflow:unset!important;' ></th>`;
            let parent = template.content.firstChild;
            if (!this.isDemoData){
                let exportButton = document.createElement('button');
                exportButton.setAttribute('class', 'btn-export-layout btn btn-secondary fa fa-download');
                exportButton.addEventListener('click', e => self._triggerExtractXLSX());
                parent.appendChild(exportButton)
            }
            this.headerRef.el.append(parent);
        }

        _triggerExtractXLSX(){
            this.trigger('extract-xlsx');
        }

        __getHeaderStyleClass(column, raw) {
            let styleLst = [];
            if (column[0] == 'number' || ['cell_monetary', 'cell_percent'].includes(column[1])) {
                styleLst.push('o_list_number_th');
            }
            if (raw == this.nowSort.key) {
                styleLst.push(((this.nowSort.type == 'desc') ? 'o-sort-up' : 'o-sort-down'));
            }
            return styleLst.join(' ')
        }

        _triggerTempOrder(name, evt) {
            evt.stopPropagation();
            this.nowSort = {
                key: name,
                type: ((this.nowSort.key == name) ? ((this.nowSort.type == 'desc') ? 'asc' : 'desc') : 'desc')
            }
            let payload = { key: 'order', value: this.nowSort, dontSave: true };
            this.trigger('change-filter-value', payload);
        }

        _triggerCheckbox(id, el, evt) {
            evt.stopPropagation();
            let isPinned = (el.classList.contains('pinned'));
            this.rpc({
                model: 'bi.dashboard.item',
                method: 'toggle_pin_item',
                args: [this.env.itemId, id, isPinned],
            });
            el.classList.toggle('pinned')
        }

        async updateTableData(lines, raw, type, external) {
            this.contentRef.el.innerHTML = '';
            this.headerWidth = {};
            if (lines.length > 0) {
                let self = this;
                let fRender = this.__extractLineRenderFunction(lines[0], raw, type);
                for (let row = 0; row < lines.length; row++) {
                    let line = document.createElement('tr');
                    line.setAttribute('id', lines[row].id);
                    for (let column = 0; column < raw.length; column++) {
                        let key = raw[column]
                        let template = document.createElement('template');
                        let data = await fRender[column](lines[row].data[key], raw[column], type[raw[column]], lines[row])
                        let html = data[0];
                        template.innerHTML = html.trim();
                        if (type[raw[column]][0] === 'number')
                            template.content.firstChild.classList.add('o_field_number')
                        if (external[raw[column]] && self.model)
                            this.addOpenEvent(lines[row].id, template.content.firstChild)
                        line.append(template.content.firstChild);
                        this.calculateExpand(key, data[1])
                    }
                    let template = document.createElement('template');
                    template.innerHTML = `<td class="o_data_cell o_field_cell pin_col" >
                    <i class="fa fa-thumb-tack ${(lines[row].pinned ? "pinned" : "")}"></i></td>`;
                    let td = template.content.firstElementChild;
                    let inp = td.firstElementChild;
                    td.addEventListener('click', (e) => self._triggerCheckbox(lines[row].id, inp, e))
                    line.append(td);
                    line.classList.add('o_data_row');
                    this.contentRef.el.append(line);
                }
            } else {
                this.headerWidth.noContent = true;
            }
        }

        addOpenEvent(id, el) {
            let self = this;
            el.classList.add('o_form_uri');
            el.addEventListener('click', (evt) => {
                if (self.model) {
                    this.trigger('open-form-record', {
                        model_id: self.model,
                        record_id: id
                    });
                }
                evt.stopPropagation();
            })
        }

        calculateExpand(key, value) {
            if (this.headerWidth[key]) {
                if (this.headerWidth[key][0] === value){
                    this.headerWidth[key][2] +=1;
                }
                this.headerWidth[key][0] = (this.headerWidth[key][0] * this.headerWidth[key][1] + value) / (this.headerWidth[key][1] + 1);
                this.headerWidth[key][1] =  this.headerWidth[key][1] + 1;
            } else {
                this.headerWidth[key] = [value, 1, 1]
            }
        }

        __extractLineRenderFunction(fLine, raw, type, hookF = ItemListCell) {
            let fList = [];
            for (let key of raw) {
                fList.push(hookF[type[key][1]]);
            }
            return fList
        }

    }

    GridListElement.template = 'GridListElement';
    GridListElement.components = { ItemTitleFrame };

    return {
        'GridElementContentBase': GridElementContentBase,
        'GridChartElement': GridChartElement,
        'GridMixedElement': GridMixedElement,
        'GridKPIElement': GridKPIElement,
        'GridGaugeElement': GridGaugeElement,
        'GridListElement': GridListElement
    };
});