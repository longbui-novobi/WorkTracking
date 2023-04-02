odoo.define('odoo_dashboard_builder.CustomBoardPopup', function (require) {
    'use strict';

    var StandaloneFieldManagerMixin = require('web.StandaloneFieldManagerMixin');
    const {FieldMany2One} = require("web.relational_fields");
    var Widget = require('web.Widget');

    var customFM20 = FieldMany2One.extend({
        init: function (parent, name, record, options, advance = {}) {
            this._super.apply(this, arguments)
            this.advance = advance;
        },
        _createContext(name) {
            let res = this._super.apply(this, arguments);
            if (this.advance.context) {
                res = _.extend(res, this.advance.context)
            }
            return res
        },
        _getSearchCreatePopupOptions: function (view, ids, context, dynamicFilters) {
            let res = this._super.apply(this, arguments);
            if (this.advance.title && view !== 'search') {
                res.title = "Create: " + this.advance.title;
            }
            return res
        },
        _onInputFocusout: function () {
            let tString = this.string;
            if (this.advance.title){
                this.string = this.advance.title;
            }
            this._super.apply(this, arguments);
            this.string = tString;
        },
    })

    var TargetBoardPopup = Widget.extend(StandaloneFieldManagerMixin, {
        init: function (parent, modelID, field, extraParams) {
            this._super.apply(this, arguments);
            StandaloneFieldManagerMixin.init.call(this);
            this.widget = undefined;
            this.value = modelID;
            this.field = field;
            this.extraParams = extraParams;

        },
        willStart: async function () {
            await this._super.apply(this, arguments);
            await this._createM2OWidget(this.field, this.value, this.extraParams);
        },
        start: function () {
            const $content = $(`<div></div>`);
            this.$content = $content
            this.$el.append($content);
            this.widget.appendTo($content);
            return this._super.apply(this, arguments);
        },
        _confirmChange: async function () {
            const result = await StandaloneFieldManagerMixin._confirmChange.apply(this, arguments);
            this.trigger_up("board_selected", {value: this.widget.value.res_id});
            this.widget.$input.blur()
            return result;
        },
        _dialogRequireField: function () {
            this.widget.$input.addClass('o_field_invalid')
        },

        _createM2OWidget: async function (fieldName, modelID, extraParams) {
            const recordID = await this.model.makeRecord(modelID, [
                {
                    name: fieldName,
                    relation: modelID,
                    type: "many2one",
                    domain: [['board_config_ids.user_id', '=', extraParams.uid],
                        ['board_config_ids', '!=', extraParams.board_id]],
                },
            ]);
            this.widget = new customFM20(this, fieldName,
                this.model.get(recordID), {
                    mode: "edit",
                    attrs: {
                        options: {
                            no_quick_create: true,
                            no_open: true
                        }
                    },
                },
                extraParams.advance
            );
            this._registerWidget(recordID, fieldName, this.widget);
        },
    });

    var Popup = Widget.extend({

        template: 'odoo_dashboard_builder.dashboardBuilderPopup',
        events: {
            'click .close': '_onClosePopup',
            'click .btn-apply': '_onApplyAction',
            'click .btn-cancel': '_onClosePopup'
        },
        custom_events: {
            board_selected: '_onBoardChange'
        },
        init: function (parent, params) {
            this._super.apply(this, arguments);
            this._initParameter(params)
        },


        _initParameter(params) {
            this.action_name = params.action_type.charAt(0).toUpperCase() + params.action_type.slice(1);
            this.item_name = params.item_name;
            this.now_board = params.now_board;
            this.extra_params = params.extra_params;
            this.config_id = params.config_id;
            this.display_id = params.display_id;
        },

        willStart: function () {
            return this._super.apply(this, arguments);
        },
        renderElement: function () {
            this._super.apply(this, arguments);
            this._renderM20()
        },
        _renderM20: function () {
            this.extra_params.advance = {
                context: {'create_from_personal_dashboard': true},
                title: "Dashboard Board"
            }
            this.M2OFilters = new TargetBoardPopup(this, 'bi.dashboard.board', 'name', this.extra_params);
            this.M2OFilters.appendTo(this.$el.find('#target-board'));
        }
        ,
        _onBoardChange: function (evt) {
            this.board_id = evt.data.value;
        }
        ,
        _onClosePopup: function () {
            this.$el.remove();
            this.destroy();
        }
        ,
        _onApplyAction: function () {
            if (this.board_id === undefined) {
                this.M2OFilters._dialogRequireField()
            } else {
                this.trigger_up('commit_advance_action', {
                    'action_type': this.action_name,
                    'new_board_id': this.board_id,
                    'config_id': this.config_id,
                    'display_id': this.display_id
                })
                this._onClosePopup();
            }
        }
        ,
    })

    return Popup
})