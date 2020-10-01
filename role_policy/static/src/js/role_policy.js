/*
# Copyright 2009-2020 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/

odoo.define("role_policy.role_policy", function(require) {
    "use strict";

    var AbstractController = require("web.AbstractController");
    var ListController = require("web.ListController");
    var core = require("web.core");
    var _t = core._t;
    var session = require("web.session");

    ListController.include({
        renderSidebar: function($node) {
            var sidebarProm = this._super($node);
            if (session.is_admin) {
                return sidebarProm;
            }
            var exportOperations = session.sidebar_operations.export_operations;
            var removeExport = false;
            if (this.modelName in exportOperations) {
                removeExport = exportOperations[this.modelName];
            } else if ("default" in exportOperations) {
                removeExport = exportOperations.default;
            }
            if (removeExport) {
                var exportLabel = _t("Export");
                var other = this.sidebar.items.other;
                var otherNew = [];
                for (var i = 0; i < other.length; i++) {
                    if (other[i].label !== exportLabel) {
                        otherNew.push(other[i]);
                    }
                }
                this.sidebar.items.other = otherNew;
            }

            return sidebarProm;
        },
    });

    AbstractController.include({
        init: function(parent, model, renderer, params) {
            this._super.apply(this, arguments);
            if (!session.is_admin) {
                var archiveOperations = session.sidebar_operations.archive_operations;
                var removeArchive = false;
                if (this.modelName in archiveOperations) {
                    removeArchive = archiveOperations[this.modelName];
                } else if ("default" in archiveOperations) {
                    removeArchive = archiveOperations.default;
                }
                if (params.archiveEnabled && removeArchive) {
                    params.archiveEnabled = false;
                }
            }
        },
    });
});
