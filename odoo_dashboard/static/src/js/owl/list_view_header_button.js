odoo.define('invoice.action_button', function (require) {
    "use strict";

    var core = require('web.core');
    var ListController = require('web.ListController');
    var _t = core._t;


    ListController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                this.$buttons.find('.oe_create_button_bi_board').click(this.proxy('action_create_new_dashboard'));
            }
        },

        action_create_new_dashboard: function () {
            let self = this;
            self.do_action({
                name: _t('New Dashboard'),
                type: 'ir.actions.act_window',
                res_model: 'bi.dashboard.board',
                views: [[false, 'form']],
                view_mode: 'form',
                target: 'current',
                context: {'create_from_personal_dashboard': true},
            });
        }
    })
});

