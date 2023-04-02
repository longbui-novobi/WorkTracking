odoo.define('odoo_dashboard_builder.DashboardItem', function (require) {
    "use strict";

    var GridElementContent = require('odoo_dashboard_builder.DashboardItemTemplate');

    const framework = require('web.framework');
    const session = require('web.session');
    const {Component} = owl;
    const {useRef, useSubEnv} = owl.hooks;

    const layoutTemplate = {
        'chart': 'GridChartElement',
        'kpi': 'GridKPIElement',
        'mixed': 'GridMixedElement',
        'gauge_mixed': 'GridGaugeElement',
        'list': 'GridListElement'
    };

    const filterEventHandler = {
        'period': '_onPeriodChange',
        'team': '_onSalesTeamChange',
        'periodical': '_onPeriodicalChange',
        'location': '_onLocationChange',
        'revenue': '_onRevenueFilterChange',
        'team_break': '_onSalesTeamBreakChange',
    };


    class GridElementComponent extends Component {
        contentComponent = useRef("content");

        constructor(parent, params, generalFilters = {}, status = false) {
            super(parent, params);
            this.initParameter(params, generalFilters);
            useSubEnv({
                // 'lastUpdated': this.lastRefresh,
                'filterConfig': this.filterConfig,
                'displayID': this.displayID,
                'itemId': this.itemId,
                'status': status,
                'title': params.info,
            });
        }

        initParameter(params, generalFilters) {
            this.displayID = _.uniqueId('it-');
            this.itemId = params.id;
            this.configId = params.config_id;
            this.itemTemplate = params.template;
            this.iconUrl = params.kpi_icon;
            // this.intervalTime = params.intervalTime;
            this.layoutConfig = params.layoutConfig;
            this.filterConfig = params.filter;
            this.titleInfo = params.info;
            // this.lastUpdated = params.lastUpdated;
            this.options = {month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'};
            // this.lastRefresh = this._getDateFormat(params.lastUpdated);
            this.filterValues = {};
            this.isChangeFilter = false;
            this.resetPaging = false;
            var self = this;
            Object.keys(this.filterConfig).forEach(filter => {
                self.filterValues[filter] = self.filterConfig[filter].select;
            });
            Object.keys(generalFilters).forEach(filter => {
                let selectedValue = generalFilters[filter];
                self.filterValues[filter] = selectedValue;
                if (self.filterConfig[filter]) {
                    self.filterConfig[filter]['select'] = selectedValue;
                }
            });
        }

        mounted() {
            super.mounted(...arguments);
            this.trigger("item-ready", this.el);
            let template = layoutTemplate[this.itemTemplate];
            if (template !== undefined && GridElementContent[template] !== undefined) {
                this.content = new GridElementContent[template](this, this.titleInfo);
                this.content.mount(this.contentComponent.el);
            }
        }

        updateItemState(config) {
            if (this.titleState && config.isTitleChange) {
                let info = config.info;
                this.titleState.updateTitleF(info.name, info.description);
            }
            if (config.isKpiImageChange) {
                this.content.updateKpiImage(config.kpi_icon);
            }
        }

        onTriggerTitleState(evt) {
            this.titleState = evt.detail
        }

        onOpenFormRecord(evt) {
            let self = this;
            this.rpc({
                model: 'bi.dashboard.item',
                method: 'get_action_list_2_form',
                args: [evt.detail],
            }).then(function (action) {
                if (action) {
                    self.trigger('open-detailed-view', {action: action})
                }
            })
        }

        _getDateFormat(date = null) {
            return new moment(date).format("MMM DD, h:mm a");
        }

        onRefreshItem() {
            this.updateItemContent();
        }

        onAdvanceItem(evt) {
            this.trigger("item-advance", {
                    displayID: this.displayID,
                    itemID: this.itemId,
                    configID: this.configId,
                    action: evt.detail,
                    item_name: this.titleInfo.title,
                }
            );
        }

        onKPIValueClick() {
            this.onItemTitleClick();
        }

        onItemTitleClick(){
            let self = this;
            this.rpc({
                model: 'bi.dashboard.item',
                method: 'get_detailed_view',
                args: [this.itemId, this.configId, this.filterValues],
            }).then(function (action) {
                if (action) {
                    self.trigger('open-detailed-view', {action: action})
                }
            })
        }

        onChangeFilter(data) {
            let filter_type = data.detail;
            if (filter_type.dontSave) {
                this.__changeFilterValueWithoutSave(filter_type)
            } else {
                if (this.filterValues.order) {
                    delete this.filterValues.order;
                    this.content.resetOrder();
                }
                if (this.resetPagingEvent)
                    this.resetPagingEvent();
                let handler = filterEventHandler[filter_type.key];
                if (handler !== undefined && this[handler] !== undefined) {
                    this[handler](filter_type);
                } else {
                    this.__changeFilterValue(filter_type);
                }
            }
            if (!filter_type.dontLoad) {
                this.updateItemContent();
            }
        }

        onCatchPagingReset(evt) {
            this.resetPagingEvent = evt.detail;
        }

        __changeFilterValueWithoutSave(data) {
            this.filterValues[data.key] = data.value;
        }

        __changeFilterValue(data) {
            this.filterValues[data.key] = data.value;
            this.saveFitlerConfig();
        }

        _onPeriodChange(data) {
            this.__changeFilterValue(data);
        }

        _onSalesTeamChange(data) {
            this.__changeFilterValue(data);
            this.content.updateSalesTeam(data);
        }

        _onPeriodicalChange(data) {
            this.__changeFilterValue(data);
        }

        _onLocationChange(data) {
            this.__changeFilterValue(data);
        }

        _onRevenueFilterChange(data) {
            this.__changeFilterValue(data);
            this.__checkRevenueFilter();
        }

        _onSalesTeamBreakChange(data) {
            this.__changeFilterValue(data);
            this.__checkSalesTeamBreakFilter(data);
        }

        __checkFilter() {
            this.__checkRevenueFilter();
            this.__checkSalesTeamBreakFilter();
        }

        __checkRevenueFilter() {
            let value = this.filterValues && this.filterValues.revenue;
            if (value) {
                let periodical_filter = this.el.getElementsByClassName(`periodical-content`)[0];
                let location_filter = this.el.getElementsByClassName(`location-content`)[0];
                let team_filter = this.el.getElementsByClassName(`team-content`)[0];
                if (value == 'product' || value == 'product_category') {
                    $(periodical_filter).addClass('filter_hide');
                    $(location_filter).addClass('filter_hide');
                    $(team_filter).removeClass('filter_hide');

                } else if (value == 'location') {
                    $(periodical_filter).addClass('filter_hide');
                    $(location_filter).removeClass('filter_hide');
                    $(team_filter).removeClass('filter_hide');
                } else if (value == 'team') {
                    $(periodical_filter).removeClass('filter_hide');
                    $(location_filter).addClass('filter_hide');
                    $(team_filter).addClass('filter_hide');
                }
            }
        }

        __checkSalesTeamBreakFilter() {
            let value = this.filterValues && this.filterValues.team_break;
            if (value) {
                let periodical_filter = this.el.getElementsByClassName(`periodical-content`)[0];
                let team_filter = this.el.getElementsByClassName(`team-content`)[0];
                if (value == 'team') {
                    $(team_filter).removeClass('filter_hide');

                } else if (value == 'total') {
                    $(team_filter).addClass('filter_hide');
                }
            }
        }

        onExtractXLSX() {
            framework.blockUI();
            session.get_file({
                url: '/dashboard_builder/list_view/extract',
                data: {
                    data: JSON.stringify({
                        "item_id": this.itemId,
                        "filter_configs": this.filterValues,
                        "config_id": this.configId
                    })
                },
                complete: framework.unblockUI,
            });
        }

        onItemMounted() {
            this.updateItemContent();
        }

        openChartEventFromKey(evt){
            let self = this;
            this.rpc({
                model: 'bi.dashboard.item',
                method: 'get_detail_view_from_key',
                args: [this.itemId, this.configId, this.filterValues, evt.detail],
            }).then(function (action) {
                if (action) {
                    self.trigger('open-detailed-view', {action: action})
                }
            })
        }
        updateItemContent() {
            var self = this;
            this.requestContent().then(function (data) {
                self.content.updateContent(data);
                self.el.style.display = 'inline-block';
            });
        }

        requestContent() {
            return this.rpc({
                model: 'bi.dashboard.item',
                method: 'get_data',
                args: [this.itemId, this.filterValues, this.configId],
            });
        }

        getFilterConfig() {
            let t = {};
            for (let key in this.filterConfig) {
                t[key] = this.filterValues[key];
            }
            return JSON.stringify(t);
        }

        saveFitlerConfig() {
            let option = this.getFilterConfig();
            this.rpc(
                {
                    model: 'bi.dashboard.item.config',
                    method: 'update_filter',
                    args: [this.configId, option],
                });
        }

        getConfig() {
            let item = $(this.el);
            return {
                id: this.itemId,
                cid: this.configId,
                layoutConfig: {
                    x: parseInt(item.attr('gs-x')),
                    y: parseInt(item.attr('gs-y')),
                    width: parseInt(item.attr('gs-w')),
                    height: parseInt(item.attr('gs-h'))
                },
                active: true,
            };
        }

    }

    GridElementComponent.template = 'GridStackElement';

    return GridElementComponent;
});