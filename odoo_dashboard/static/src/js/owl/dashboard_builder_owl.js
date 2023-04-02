odoo.define('odoo_dashboard.DashboardBuilder', function (require) {
    "use strict";

    var core = require('web.core');
    var AbstractAction = require('web.AbstractAction');
    var ajax = require('web.ajax');
    var _t = core._t;
    const framework = require('web.framework');

    var GridView = require('odoo_dashboard.DashboardGrid');
    var CustomFilter = require('odoo_dashboard.CustomFilterHook');
    var CustomPopup = require('odoo_dashboard.CustomBoardPopup');

    const parsingMethod = {
        team: '_onChangeTeamFilter',
        period: '_onChangePeriodFilter'
    };

    var dashboard = AbstractAction.extend({
        contentTemplate: 'odoo_dashboard.dashboardBuilder',
        hasControlPanel: false,
        xmlDependencies: [
            '/odoo_dashboard/static/src/xml/dashboard_view.xml',
            '/odoo_dashboard/static/src/xml/item_filter_view.xml',
            '/odoo_dashboard/static/src/xml/item_view.xml',
        ],
        jsLibs: [
            '/odoo_dashboard/static/lib/js/gridstack-h5.js',
            '/web/static/lib/Chart/Chart.js',
            '/odoo_dashboard/static/lib/js/chartjs-plugin-datalabels.min.js',
            '/odoo_dashboard/static/lib/js/Chart.Geo.min.js',
            '/odoo_dashboard/static/lib/js/gauge.js',
            '/odoo_dashboard/static/lib/js/stack.js',
            '/odoo_dashboard/static/lib/js/string-similarity.min.js',
            '/odoo_dashboard/static/lib/js/html2pdf.js',
            '/odoo_dashboard/static/lib/js/html2canvas.min.js',
            '/web/static/lib/daterangepicker/daterangepicker.js'
        ],
        cssLibs: [
            '/odoo_dashboard/static/lib/css/gridstack.min.css',
            '/web/static/lib/daterangepicker/daterangepicker.css'
        ],
        events: {
            'click #btn_edit_layout': '_onClickBtnEditLayout',
            'click #btn_save_layout': '_onClickBtnSaveLayout',
            'click #btn_discard_layout': '_onClickDiscardLayout',
            'click #refresh-btn': '_onClickBtnReloadData',
            'click .popup-controller .btn': '_updateDashboardStatus',
            'click .btn_inline .select-selected': '_showingDropdown',
            'click .btn_inline .select-items div': '_selectedChange',
            'click .o_back_button': 'back_to_previous',
            'click #btn_add_new_item': '_onClickBtnAddItem',
            'click #btn_export_to_pdf': '_onExport',
            'click #export2img': '_onExport2Image',
            'click #export2pdf': '_onExport2PDF',
        },
        custom_events: {
            ready_layout: '__readyLayout',
            item_advance_trigger: '_onItemAdvance',
            commit_advance_action: '_onItemAdvanceOption',
            open_detailed_view: '_openDetailedView'

        },

        init: function (parent, action) {
            this.action_manager = parent;
            this._initParameter(action);
            return this._super.apply(this, arguments);
        },

        _initParameter: function (action) {
            this.action = action;
            this.dashboard_id = action.params.dashboard_id;
            this.context = action.context;
            this.previewMode = this.context && this.context.preview_layout || false;
            this.dashboard_name = action.name;
            if (!this.dashboard_name) {
                this.previewMode = true;
            }
            this.previewName = this.context && this.context.preview_name || '';
            this.domain = [];
            this.period = 'this_year';
            this.boardItems = [];
            this.filterValues = {};
            this.generalFilters = {};
            this.isBoardChange = false;
            this.boardFilters = {};
            this.removeItems = [];
            this.lastUpdated = '';
            this.options = {month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'};
            this.isManager = false;
            window.selectOpen = false;
        },

        willStart: function () {
            var self = this;
            return Promise.all([
                this.load_dashboard_config(),
                this._checkGroup(),
                this._super.apply(this, arguments)
            ]);
        },

        back_to_previous(ev) {
            this.trigger_up('history_back');
        },

        load_dashboard_config: async function () {
            // Have to load filter config before load dashboard items
            await this._loadDashboardFilters();
            await this._loadDashboardItems();
            await this._loadDashboardLayout();
            await this._getDashboardLastUpdated();
        },

        start: function () {
            let _super = this._super;
            var self = this;
            //Render edit button and last updated time
            // this._loadDashboardUserRole();
            // Update filter values
            Object.keys(self.generalFilters).forEach(filter => {
                let val = self.generalFilters[filter].select;
                self.filterValues[filter] = val;

            });
            $.when(ajax.loadLibs(this)).then(async function () {
                self.render_dashboard();
                self.__checkDashboardStatus().then(function (isUpdating) {
                    if (!isUpdating) {
                        if (self.$('#refresh-btn').hasClass('waiting')) {
                            return _super.apply(this, arguments);
                        }
                        self.__toggleDashboardStatus(false);
                        self.__createUpdatingInterval();
                    } else {
                        self._loadDashboardStatus();
                    }
                });
                self.__renderPretreatment()
            });
            // Resize the chart when changing the screen size
            window.addEventListener('resize', function () {
                self._resizeDashboardItems();
            });
            document.addEventListener('click', function () {
                if (window.selectOpen) {
                    window.selectOpen.classList.remove("select-arrow-active");
                    $(window.selectOpen).next('.select-items').addClass('select-hide');
                    $(window.selectOpen).parents('.many2one').removeClass('active');
                }
                self.__triggerAdvanceBtn();
                self._onHideExport();
            });

            return _super.apply(this, arguments);
        },

        __triggerAdvanceBtn() {
            if (window.advanceItemPopup !== undefined) {
                window.advanceItemPopup.style.display = 'none';
                window.advanceItemBase.classList.remove('trigger-advance');
                window.advanceItemPopup = undefined;
            }
        },

        render_dashboard: async function () {
            let self = this;
            const container = self.el.getElementsByClassName("dashboard_container")[0];
            if (container) {
                let params = {
                    itemConfigs: self.boardItems,
                    generalFilters: self.filterValues,
                    floating_layout: self.floating_layout,
                };
                self.gridView = new GridView(self, params);
                await self.gridView.mount(container);
            }
        },
        __readyLayout: function (el) {
            this.gridView = el.data;
            this.gridView.disable();
            this.gridView.setAnimation(true);
            this._changeCSSColorStyle();
            this._resizeDashboardItems();
            this.__triggerEvent()
        },

        __triggerEvent: function (bubbles = true, cancelable = false, events = 'resize') {
            let event = document.createEvent('HTMLEvents');
            event.initEvent(events, bubbles, cancelable);
            document.dispatchEvent(event);
        },

        on_attach_callback: function () {
            var self = this;
            if (this.gridView && this.gridView.grid) {
                // this.gridView.updateCellHeight(0);
                // this.gridView.commit();
                // this.__triggerEvent(true, false, 'resize');
                this.gridView.destroy();
                this._loadDashboardItems().then(function () {
                    self.render_dashboard();
                });
            }
            return this._super.apply(this, arguments);
        },

        _updateDashboardFilterStatus: function () {
            return this._rpc(
                {
                    model: 'bi.dashboard.board.config',
                    method: 'update_dashboard_filter',
                    args: [this.boardConfigID, JSON.stringify(this.filterValues)],
                });
        },
        // _loadDashboardUserRole: function () {
        //     this._rpc({
        //         model: 'bi.dashboard.board',
        //         method: 'get_dashboard_init_and_role_status',
        //     }).then(role => {
        //         if (!role) {
        //             this.$('#btn_edit_layout').hide();
        //         }
        //         this.$('.dashboard_button_box_left').css('visibility', 'visible');
        //     });
        // },
        _loadDashboardStatus: async function () {
            let action = await this._rpc({
                model: 'bi.dashboard.board',
                method: 'get_dashboard_data_initialize',
                args: [this.dashboard_id],
            });
            if (action.constructor === Object) {
                this.do_action(action);
            }
        },

        _resizeDashboardItems: function () {
            if (this.gridView && this.gridView.grid) {
                var newWidth = window.innerWidth;
                let cellHeight = ((newWidth > 768) ? 40 * newWidth / 1366 : 40);
                this.gridView.batchUpdate();
                this.gridView.updateCellHeight(cellHeight);
                this.gridView.commit();
                this.gridView._responsiveDashboard();
            }
        },

        _checkGroup: async function () {
            this.isManager = await this._rpc(
                {
                    model: 'bi.dashboard.board',
                    method: 'check_manager',
                });
        },

        _changeCSSColorStyle: function () {
            let $el = this.$('#btn_edit_layout');
            let bkg = $el.css('background-color');
            let color = $el.css('color');
            this.dashboardDOM = document.getElementsByClassName('dashboard_container')[0];
            this.dashboardDOM.style.setProperty('--prt', color);
            this.dashboardDOM.style.setProperty('--prb', bkg);
        },

        _onClickBtnEditLayout: function () {
            this._toggle_display(true);
            this.gridView.enable();
        },

        _toggle_display: function (is_movable) {
            this._hide_control_options();
            let $show_components = $('.dashboard_show');
            let $hide_components = $('.dashboard_hide');
            $hide_components.addClass('dashboard_show').removeClass('dashboard_hide');
            $show_components.addClass('dashboard_hide').removeClass('dashboard_show');
            if (is_movable) {
                $('.odoo_dashboard_content').addClass("movable_content");
                $('.dashboard_kpi_content').addClass("movable_content");
            } else {
                $('.odoo_dashboard_content').removeClass("movable_content");
                $('.dashboard_kpi_content').removeClass("movable_content");
            }
        },

        _hide_control_options: function () {
            if (this.previewMode) {
                let $show_components = $('.item-handle-btn');
                $show_components.addClass("control_hide");
            }
        },

        destroy: async function () {
            if (this.gridView !== undefined) {
                this.gridView.destroy();
            }
            this._super.apply(this, arguments);
            delete window.selectOpen;
        },

        _getRoleOfUser: function () {
            // TODO: In the future, each user has their own permissions to monitor the dashboard.
            return 0;
        },

        _loadDashboardItems: async function () {
            let self = this;
            if (this.dashboard_id) {
                this.boardItems = await this._rpc(
                    {
                        model: 'bi.dashboard.board',
                        method: 'get_dashboard_item',
                        args: [this.dashboard_id],
                        context: self.context,
                    });
            }
        },

        _loadDashboardFilters: async function () {
            let self = this;
            if (this.dashboard_id) {
                let return_val = await this._rpc(
                    {
                        model: 'bi.dashboard.board',
                        method: 'get_filters_config',
                        args: [this.dashboard_id],
                        context: self.context,
                    });
                this.generalFilters = return_val.filters;
                this.boardConfigID = return_val.board_config_id;
            }
        },

        _loadDashboardLayout: async function () {
            let self = this;
            if (this.dashboard_id) {
                let return_val = await this._rpc(
                    {
                        model: 'bi.dashboard.board',
                        method: 'get_floating_layout',
                        args: [this.dashboard_id],
                        context: self.context,
                    });
                this.floating_layout = return_val['is_floating_layout'];
                this.is_show_last_updated = return_val['is_show_last_updated'];
            }
        },

        _getDashboardLastUpdated: async function () {
            if (this.is_show_last_updated) {
                let lastUpdated = await this._rpc(
                    {
                        model: 'bi.dashboard.board',
                        method: 'get_last_updated_time',
                    });
                this.lastUpdated = this._formatDatetime(lastUpdated);
                $('#last_update_time').text(this.lastUpdated);
            }
        },

        _formatDatetime: function (value) {
            if (value && value != '') {
                let date = new moment(value);
                let lastUpdated = date.add(this.getSession().getTZOffset(date), 'minutes');
                // let lastUpdated = new Date(date.getTime() + (this.getSession().getTZOffset(date) * 60 * 1000));
                return new moment(lastUpdated).format("MMM DD, h:mm A");
            }
            return '';
        },

        _onClickDiscardLayout: function () {
            this._toggle_display(false);
            if (this.removeItems && this.removeItems.length > 0 && this.gridView) {
                this.gridView.destroy();
                this.render_dashboard();
            } else {
                this.gridView.disable();
                this._resetItemPosition();
                this.gridView.discardFontChange();
            }
        },

        _resetItemPosition: function (evt) {
            for (let item of this.boardItems) {
                let dasboard_item = this.gridView.items[item.config_id.toString()];
                if (dasboard_item) {
                    var element = `#${dasboard_item.displayID}`;
                    this.gridView.grid.update(element, {
                            x: item.layoutConfig.x,
                            y: item.layoutConfig.y,
                            w: item.layoutConfig.width,
                            h: item.layoutConfig.height
                        }
                    );
                }
            }
        },

        _onClickBtnSaveLayout: function (evt) {
            this._toggle_display(false);
            this.gridView.disable();
            Promise.all([this._saveDashboardConfiguration()]);
        }
        ,

        _saveDashboardConfiguration: async function () {
            if (this.gridView && this.gridView.items) {
                let itemConfigurations = [];
                let self = this;
                Object.keys(this.gridView.items).forEach(function (id) {
                    let item = self.gridView.items[id];
                    var config = item.getConfig();
                    if (self.removeItems.includes(id)) {
                        config.active = false;
                    }
                    itemConfigurations.push(config);
                });
                this._updateDashboardConfig(itemConfigurations)
                    .then(function () {
                        self._loadDashboardItems();
                    });
            }
        },


        _updateDashboardConfig: async function (itemConfigs) {
            await this._rpc(
                {
                    model: 'bi.dashboard.board',
                    method: 'update_dashboard_layout',
                    args: [this.dashboard_id, this.boardConfigID, itemConfigs],
                });
        },

        __changeSelected(el) {
            el.siblings('.selected').removeClass('selected');
            el.addClass('selected');
        },


        _selectedChange(e) {
            e.stopPropagation();
            let target = $(e.target).closest('div');
            let parent = target.parent();
            let previous = parent.prev('.select-selected');
            previous.removeClass("select-arrow-active");
            $(e.target).parents('.many2one').removeClass('active');
            parent.addClass('select-hide');
            let new_val = target.attr('val');
            let type = previous.attr('type');
            previous.html(target.text().trim());
            if (this.gridView) {
                this[parsingMethod[type]](new_val, type, parent.parent());
            }
            this.__changeSelected(target);
        },

        _showingDropdown(e) {
            if (window.selectOpen && window.selectOpen !== e.target) {
                window.selectOpen.classList.remove("select-arrow-active");
                $(window.selectOpen).next('.select-items').addClass('select-hide');
                $(window.selectOpen).parents('.many2one').removeClass('active');
            }
            e.stopPropagation();
            window.selectOpen = e.target;
            $(e.target).next('.select-items').toggleClass("select-hide");
            e.target.classList.toggle("select-arrow-active");
            $(e.target).parents('.many2one').toggleClass('active');
        },

        __renderPretreatment() {
            if (this.filterValues['period'] === 'custom_period') {
                this._renderCustomPeriod($('#board-period'), 'period');
            }
        },


        _onChangePeriodFilter: function (val, type, base) {
            if (val !== 'custom_period') {
                if (this.$relatedBtn) {
                    this.$relatedBtn.remove();
                    this.$relatedBtn = null;
                }
                this._triggerPeriodFilter(val);
            } else if (!this.$relatedBtn) {
                this._renderCustomPeriod(base, type);
            }
        },

        _triggerPeriodFilter: function (val) {
            var self = this;
            this.filterValues.period = val;
            this._updateDashboardFilterStatus().then(function () {
                self.gridView.onChangeGeneralFilter({key: 'period', value: val});
            });
        },

        _renderCustomPeriod: async function (baseElement, type) {
            let element = CustomFilter.customDateRangeUIHook(baseElement);
            this.$relatedBtn = element.element;
            this.$input = element.input;
            this.__requestDateDateRange(this.filterValues[type]).then(
                result => {
                    element.input.daterangepicker({
                        "showWeekNumbers": true,
                        "linkedCalendars": false,
                        "showCustomRangeLabel": false,
                        "opens": "center",
                        startDate: new Date(result[0]),
                        endDate: new Date(result[1]),
                        locale: {
                            format: 'MMM D, YYYY'
                        }
                    });
                    element.event((x) => this._onChangeCustomPeriod(this, x))
                }
            )
        },

        _onChangeCustomPeriod: function (self, element) {
            let val = element.value.split('-');
            let data = {
                'start': moment(val[0], 'MMM D, YYYY').add('days', 1),
                'end': moment(val[1], 'MMM D, YYYY').add('days', 1)
            };
            self._rpc(
                {
                    model: 'bi.dashboard.board.config',
                    method: 'update_dashboard_custom_filter',
                    args: [self.boardConfigID, data],
                }).then(() => {
                self._triggerPeriodFilter('custom_period');
            })
        },

        __requestDateDateRange: async function (value) {
            let self = this;
            return this._rpc(
                {
                    model: 'bi.dashboard.board.config',
                    method: 'get_date_range_from_period',
                    args: [self.boardConfigID, value],
                });
        },

        _onChangeTeamFilter: function (val, type, base) {
            this.gridView.onChangeGeneralFilter({key: 'team', value: val});
            this.filterValues.team = val;
            this._updateDashboardFilterStatus();
        },

        _onItemRemove: function (itemID, displayID, isTemporary = true) {
            this.gridView.removeItem(displayID);
            if (isTemporary)
                this.removeItems.push(itemID.toString());
        },

        __loadItemsPosition() {
            let lst = [];
            let self = this;
            for (let item_config_id in this.gridView.items) {
                let item = this.gridView.items[item_config_id];
                if (!self.removeItems.includes(item_config_id)) {
                    lst.push(item.getConfig().layoutConfig)
                }
            }
            return {"items": lst, "rows": this.gridView.grid.getRow(), "columns": this.gridView.grid.getColumn()}
        },

        _onItemAdvance: function (evt) {
            let ev = evt.data;
            if (ev.action === 'drop') {
                this._onItemRemove(ev.configID, ev.displayID)
            } else {
                let config =
                    {
                        'action_type': ev.action,
                        'item_name': ev.item_name,
                        'now_board': this.dashboard_name,
                        'config_id': ev.configID,
                        'display_id': ev.displayID,
                    }
                if (ev.action === 'duplicate') {
                    this._onItemAdvanceOption(
                        {data: _.extend(config, {new_board_id: this.dashboard_id})},
                        this.__loadItemsPosition()
                    )
                } else {
                    let custom = new CustomPopup(this, _.extend(config, {
                        'extra_params': {
                            'uid': this.action.context.uid,
                            'board_id': this.boardConfigID
                        }
                    }))
                    let el = $('.o_web_client')
                    custom.appendTo(el)
                }
            }
        },
        _onItemAdvanceOption: function (evt, extend = null) {
            let self = this;
            this._rpc(
                {
                    model: 'bi.dashboard.item',
                    method: 'action_controller',
                    args: [evt.data, extend]
                }).then(res => {
                let isRemove = res[0], config = res[1];
                if (isRemove) {
                    self._onItemRemove(evt.data.config_id, evt.data.display_id, false);
                } else {
                    if (evt.data.action_type === 'duplicate') {
                        self._onDuplicateItem(config)
                    }
                }
            })
        },
        _onDuplicateItem: function (item_config) {
            this.gridView.renderGridElement(item_config);
        },

        _onClickBtnReloadData: async function (ev) {
            var self = this;
            if (this.$('#refresh-btn').hasClass('waiting')) {
                return;
            }
            this.__toggleDashboardStatus(false);
            this._rpc(
                {
                    model: 'bi.dashboard.item',
                    method: 'force_recompute_dashboard_data',
                }).then(function () {
                self.__createUpdatingInterval();
            });
        },

        _onClickBtnAddItem: function () {
            var self = this;
            this.do_action({
                name: _t('New Dashboard Item'),
                type: 'ir.actions.act_window',
                res_model: 'bi.dashboard.item',
                views: [[false, 'form']],
                view_mode: 'form',
                target: 'current',
                context: {
                    'board_config_id': self.boardConfigID,
                    'default_created_on_ui': true,
                    'default_compute_function': 'get_data_for_custom_item',
                    'default_x_position': 0,
                    'default_y_position': 10000,
                },
            });
        },

        __checkDashboardStatus: function () {
            return this._rpc(
                {
                    model: 'bi.dashboard.item',
                    method: 'check_update_status',
                })
        },

        __createUpdatingInterval: function () {
            let self = this;
            let interval = setInterval(function () {
                self.__checkDashboardStatus().then(function (isUpdated) {
                    if (isUpdated) {
                        if (self.gridView) {
                            self.gridView.destroy();
                        }
                        //self._getDashboardLastUpdated();
                        self.render_dashboard();
                        clearInterval(interval);
                        self.__toggleDashboardStatus(true);
                    }
                })
            }, 60000);
            return interval;
        },

        __toggleDashboardStatus: function (condition) {
            if (condition) {
                this.$('#refresh-btn').removeClass('waiting');
                this._getDashboardLastUpdated();
                this.$('#last_update_time').prev().show();
            } else {
                this.$('#refresh-btn').addClass('waiting');
                let el = this.$('#last_update_time');
                el.html('Update in progress ...');
                el.prev().hide();
            }
        },

        _onExport: function (evt) {
            this.$('#export-dropdown').toggleClass('show');
            this.$('#btn_export_to_pdf').toggleClass('show');
            evt.stopPropagation();
        },
        _onHideExport: async function () {
            if (window.openExportOption !== 'loading') {
                this.$('#export-dropdown').removeClass('show');
                this.$('#btn_export_to_pdf').removeClass('show');
                if (window.openExportOption === 'start') {
                    framework.blockUI();
                    window.openExportOption = 'loading';
                    return this._animationScroll()
                }
                return $.when([])
            }
        },
        _animationScroll: function (isBackward = false) {
            let el = document.querySelector('.o_content');
            let duration = 700, position = 0, padding = el.scrollTop;
            if (isBackward) {
                duration = 350, position = padding = window.beforeExportPosition ?? 0;
            } else {
                window.beforeExportPosition = el.scrollTop;
            }
            return $('.o_content').animate({scrollTop: position}, duration * padding / el.scrollTopMax).promise();
        },
        _onInvisibleLayout: function () {
            this.$('#btn_export_to_pdf').toggle();
            this.$('#btn_edit_layout').toggle();
            this.$('#refresh-btn').toggle();
            this.$('#btn_add_new_item').toggle();
        },

        _onExport2PDF: async function (evt) {
            window.openExportOption = 'start';
            await this._onHideExport();
            this._onInvisibleLayout();
            let self = this;
            var opt = {
                margin: [0, 0, 0, 0],
                filename: `${this.dashboard_name}.pdf`,
                image: {type: 'png', quality: 1},
                jsPDF: {unit: 'px', orientation: 'portrait', format: [1920, 2566]}
            };
            const element = document.getElementById("base");
            html2pdf().set(opt).from(element).save().then(async e => self._animationScroll(true)).then(e => {
                self._onInvisibleLayout();
                framework.unblockUI();
                window.openExportOption = 'end';
            })
        },

        _onExport2Image: async function (evt) {
            window.openExportOption = 'start';
            await this._onHideExport();
            this._onInvisibleLayout();
            let self = this;
            this.$el.css('width', '1920px')
            html2canvas(document.querySelector("#base")).then(canvas => {
                var image = canvas.toDataURL("image/png").replace("image/png", "image/octet-stream");  // here is the most important part because if you dont replace you will get a DOM 18 exception.
                let a = document.createElement('a');
                a.setAttribute('href', image);
                a.setAttribute('download', `${self.dashboard_name}.png`);
                a.click();
                a.remove();
            }).then(async e => self._animationScroll(true)).then(e => {
                self._onInvisibleLayout();
                framework.unblockUI();
                window.openExportOption = 'end';
            })
            self.$el.css('width', 'unset');
        },

        _openDetailedView: function (ev) {
            var action = ev.data && ev.data.action;
            if (action) {
                this.do_action(action);
            }
        }
    });

    core.action_registry.add("odoo_dashboard", dashboard);
    return dashboard;
});
