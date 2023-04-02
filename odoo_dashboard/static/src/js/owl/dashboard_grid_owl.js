odoo.define('odoo_dashboard.DashboardGrid', function (require) {
    "use strict";
    var GridElementComponent = require('odoo_dashboard.DashboardItem');
    const {Component} = owl;
    const {useRef} = owl.hooks;

    class GridView extends Component {

        gridContent = useRef('grid-content');

        constructor(parent, params) {
            super(null, params);
            this.parentWidget = parent;
            this.cellHeight = params.cellHeight || 40;
            this.cellHeightUnit = params.cellHeightUnit || 'px';
            this.itemConfigs = params.itemConfigs;
            this.generalFilters = params.generalFilters || {};
            this.column = params.column || 12;
            this.floating_layout = params.floating_layout || false;
            this.items = {};
            this.readyItems = 0;
            this.totalItems = this.itemConfigs.length;
        }

        async renderGridElements(itemConfig) {
            const gridElementComponent = new GridElementComponent(this, itemConfig, this.generalFilters);
            gridElementComponent.mount(this.gridContent.el);
            this.items[itemConfig.config_id.toString()] = gridElementComponent;
        }

        async renderGridElement(itemConfig) {
            const gridElementComponent = new GridElementComponent(this, itemConfig, this.generalFilters, true);
            await gridElementComponent.mount(this.gridContent.el);
            this.gridContent.el.appendChild(gridElementComponent.el);
            this.grid.makeWidget(`#${gridElementComponent.displayID}`);
            this.items[itemConfig.config_id.toString()] = gridElementComponent;
        }


        mounted() {
            var self = this;
            this.gridContent.el.style.width = '1366px';
            super.mounted(...arguments);
            _.each(this.itemConfigs, function (itemConfig) {
                self.renderGridElements(itemConfig);
            });
        }

        __triggerReadyItem(el) {
            let element = el.detail;
            this.readyItems += 1;
            this.gridContent.el.appendChild(element);
            this.__onItemResizeStop(element);
            if (this.readyItems === this.totalItems) {
                this.grid = GridStack.init({
                    cellHeight: this.cellHeight,
                    cellHeightUnit: this.cellHeightUnit,
                    column: this.column,
                    float: this.floating_layout,
                });
                this.gridContent.el.style.width = 'none';
                this._responsiveDashboard();
                this.parentWidget.__readyLayout({'data': this});
            }
        }


        disable() {
            if (this.grid) {
                this.grid.disable();
            }
        }

        batchUpdate() {
            if (this.grid) {
                this.grid.batchUpdate();
            }
        }

        updateCellHeight(cellHeight) {
            if (this.grid) {
                this.grid.cellHeight(cellHeight);
            }
        }

        commit() {
            if (this.grid) {
                this.grid.commit();
            }
        }

        enable() {
            if (this.grid) {
                this.grid.enable();
            }
        }

        setAnimation(isAnimated) {
            if (this.grid) {
                this.grid.setAnimation(isAnimated);
            }
        }

        removeItem(itemId) {
            if (itemId && this.grid) {
                this.grid.removeWidget(`#${itemId}`);
            }
        }

        _responsiveDashboard() {
            let self = this;
            let height = window.innerHeight;
            let width = window.innerWidth;

            let nowFontSize = Math.round(0.00835*width + 0.00014*height + 0.4345);
            $(this.gridContent.el)[0].style.fontSize = nowFontSize + "px";
            // Resize event
            this.grid.on('resizestop', (e, ui) => {
                self.__onItemResizeStop(ui);
            });
            $(this.gridContent.el)[0].style.width = 'unset';
        }

        __onItemResizeStop(el) {
            if (el.getAttribute('gs-w') === '1') {
                return;
            }
            let W = el.getAttribute('gs-w') - el.getAttribute('b-w');
            let H = el.getAttribute('gs-h') - el.getAttribute('b-h');
            if (H < 0) H /= 2;
            if (W < 0) W /= 2;
            let Font = 30 * W + 6 * H + 100;
            // el.style.fontSize = Font + "%";
            $(el).find('.t3-top').css('fontSize', Font + "%");

        }

        discardFontChange() {
            let self = this;
            Object.keys(this.items).forEach(itemId => {
                let item = self.items[itemId];
                self.__onItemResizeStop(item.el);
            });
        }

        onChangeGeneralFilter(data) {
            Object.keys(this.items).forEach(itemId => {
                this.items[itemId].onChangeFilter({
                    detail: {
                        key: data.key || '',
                        value: data.value || '',
                    }
                })
            });
        }

        onItemAdvance(ev) {
            if (this.parentWidget) {
                this.parentWidget.trigger_up("item_advance_trigger", ev.detail);
            }
        }

        onOpenDetailedView(ev) {
            if (this.parentWidget) {
                this.parentWidget.trigger_up("open_detailed_view", ev.detail);
            }
        }
    }

    GridView.template = 'GridStackComponent';
    return GridView;
});