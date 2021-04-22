# Copyright 2020-2021 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import config

_logger = logging.getLogger(__name__)


class ViewModelOperation(models.Model):
    _name = "view.model.operation"
    _description = "View Model Operation"
    _order = "role_id, sort, operation"
    _sql_constraints = [
        (
            "operation_uniq",
            "unique(role_id, model, operation, company_id)",
            "The operation must be unique",
        )
    ]

    role_id = fields.Many2one(string="Role", comodel_name="res.role", required=True)
    model = fields.Char(
        required=True, help="Specify 'default' or a 'model name, e.g. sale.order"
    )
    sort = fields.Char(compute="_compute_sort", store=True)
    priority = fields.Integer(
        default=16,
        required=True,
        help="The priority determines which rule will be "
        "selected in case of conflicting rules. "
        "Rule conflicts may exist for users with "
        "multiple roles or inconsistent role definitions.",
    )
    operation = fields.Selection(selection="_selection_operation", required=True)
    disable = fields.Boolean(help="Disable this operation", default=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company", related="role_id.company_id", store=True
    )

    @api.model
    def _selection_operation(self):
        ops_dict = self._operations_dict()
        return [(k, v["label"]) for k, v in ops_dict.items()]

    @api.depends("model")
    def _compute_sort(self):
        for rule in self:
            if rule.model == "default":
                rule.sort = "0"
            else:
                rule.sort = rule.model or ""

    @api.onchange("model")
    def _onchange_model(self):
        for rule in self:
            if rule.model and rule.model != "default":
                if rule.model not in self.env:
                    raise UserError(
                        _("Error in rule with ID %s: " "model '%s' does not exist.")
                        % (rule.id, rule.model)
                    )

    def _operations_dict(self):
        """
        Returns dict defining the supported operations.
        Specify "view_types" and "view_type_attribute" to implement this
        operation via the view.type.attribute rule set.
        The "view_type_attribute" key is optional, if not set the
        attribute name is equal to the operation name).

        The "archive" operation is implemented via js code.
        The "export" operation is implemented via combination of js code
        and view type attribute.
        """
        return {
            "create": {"label": _("Create"), "view_types": ("tree", "form")},
            "edit": {"label": _("Edit"), "view_types": ("tree", "form")},
            "delete": {"label": _("Delete"), "view_types": ("tree", "form")},
            "duplicate": {"label": _("Duplicate"), "view_types": ("tree", "form")},
            "export": {
                "label": _("Export"),
                "view_types": ("tree", "form"),
                "view_type_attribute": "export_xlsx",
            },
            "import": {"label": _("Import"), "view_types": ("tree", "form")},
            "archive": {"label": _("Archive")},
        }

    def _get_rules(self, model=None):
        rules = self.browse()
        if self.env.user.exclude_from_role_policy or config.get("test_enable"):
            return rules
        signature_fields = self._rule_signature_fields()
        user_roles = self.env.user.enabled_role_ids or self.env.user.role_ids
        dom = [("role_id", "in", user_roles.ids)]
        if model:
            dom.append(("model", "in", (model, "default")))
        all_rules = self.search(dom)
        rules_dict = {}
        for rule in all_rules:
            key = "-".join([str(getattr(rule, f)) for f in signature_fields])
            if key not in rules_dict:
                rules_dict[key] = rule
            else:
                rules_dict[key] += rule
        # Keep only rules with highest priority.
        # No rule for one of the user roles is considered highest priority
        roles_nbr = len(user_roles)
        for key in rules_dict:
            key_rules = rules_dict[key]
            if len(key_rules) != roles_nbr:
                continue
            rules += key_rules.sorted(lambda r: r.priority)[0]
        if model:
            default_rules = rules.filtered(lambda r: r.model == "default")
            model_rules = rules - default_rules
            model_rules_operations = [r.operation for r in model_rules]
            rules -= default_rules.filtered(
                lambda r: r.operation in model_rules_operations
            )
        return rules

    def _rule_signature_fields(self):
        return ["model", "operation"]
