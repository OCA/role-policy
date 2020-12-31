/*
# Copyright 2020 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/

odoo.define("role_policy.role_policy", function(require) {
    "use strict";

    var AbstractController = require("web.AbstractController");
    var KanbanController = require("web.KanbanController");
    var ListController = require("web.ListController");
    var core = require("web.core");
    var _t = core._t;
    var session = require("web.session");

    KanbanController.include({
        renderButtons: function() {
            this._super.apply(this, arguments);
            var buttons = {
                create: "button.o-kanban-button-new",
                import: "button.o_button_import",
            };
            if (!session.exclude_from_role_policy) {
                for (var button in buttons) {
                    var Operations = session.model_operations[button];
                    var hideButton = false;
                    if (this.modelName in Operations) {
                        hideButton = Operations[this.modelName];
                    } else if ("default" in Operations) {
                        hideButton = Operations.default;
                    }
                    if (hideButton) {
                        var toHide = this.$buttons
                            ? this.$buttons.find(buttons[button])
                            : false;
                        if (toHide) {
                            toHide.hide();
                        }
                    }
                }
            }
        },
    });

    ListController.include({
        renderSidebar: function($node) {
            var sidebarProm = this._super($node);
            if (session.exclude_from_role_policy) {
                return sidebarProm;
            }
            var exportOperations = session.model_operations.export;
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
                var archiveOperations = session.model_operations.archive;
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
