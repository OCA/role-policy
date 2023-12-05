/*
  Copyright 2020-2023 Noviat.
  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/

odoo.define("role_policy_hr.role_policy_hr", function(require) {
    "use strict";

    var FormController = require("web.FormController");

    FormController.include({
        _onSave: function(ev) {
            this._super(ev);
            var model = this.initialState.model;
            var ctx = this.initialState.context;
            if (model === "res.users" && ctx && ctx.from_my_profile === true) {
                location.reload();
            }
        },
    });
});
