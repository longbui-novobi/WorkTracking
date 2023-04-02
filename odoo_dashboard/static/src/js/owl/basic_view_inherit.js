// odoo.define('odoo_dashboard_builder.BasicView', function (require) {
//     "use strict";
//
//     var BasicView = require('web.BasicView');
//
//     BasicView.include({
//         init: function (viewInfo, params) {
//             this._super.apply(this, arguments);
//             // Remove ARCHIVE option in the Action menu
//             if (this.controllerParams.modelName === "bi.dashboard.board.config" ||
//                 this.controllerParams.modelName === "bi.dashboard.board") {
//                 this.controllerParams.archiveEnabled = false;
//             }
//         },
//     });
// });