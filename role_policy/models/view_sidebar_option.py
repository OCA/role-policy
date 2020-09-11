# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ViewSidebarOption(models.Model):
    _name = "view.sidebar.option"
    _description = "View Sidebar Option"
    _order = "role_id, sort, option"
    _sql_constraints = [
        (
            "option_uniq",
            "unique(role_id, model, option, company_id)",
            "The Sidebar Option must be unique",
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
    option = fields.Selection(
        selection="_selection_option", string="Option", required=True
    )
    disable = fields.Boolean(help="Remove this option from the Sidebar", default=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company", related="role_id.company_id", store=True
    )

    @api.model
    def _selection_option(self):
        return [("export", _("Export")), ("archive", _("Archive"))]

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

    def _get_rules(self):
        signature_fields = self._rule_signature_fields()
        dom = [("role_id", "in", self.env.user.role_ids.ids)]
        all_rules = self.search(dom)
        all_rules = all_rules.sorted(key=lambda r: (r.model, r.option, r.priority))
        if all_rules:
            for i, rule in enumerate(all_rules):
                if i == 0:
                    rules = rule
                    previous_signature = [getattr(rule, f) for f in signature_fields]
                else:
                    signature = [getattr(rule, f) for f in signature_fields]
                    if signature != previous_signature:
                        rules += rule
                    previous_signature = signature
        else:
            rules = self.browse()
        return rules

    def _rule_signature_fields(self):
        return ["model", "option"]
