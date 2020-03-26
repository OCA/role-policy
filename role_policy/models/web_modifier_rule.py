# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class WebModifierRule(models.Model):
    _name = "web.modifier.rule"
    _description = "View Modifiers Rule"
    _order = "model,sequence,view_type,element"
    _sql_constraints = [
        (
            "element_uniq",
            "unique(element, model_id, view_id, view_type, company_id)",
            "The Element must be unique",
        )
    ]

    role_id = fields.Many2one(string="Role", comodel_name="res.role", required=True)
    model_id = fields.Many2one(comodel_name="ir.model", required=True, string="Model")
    model = fields.Char(related="model_id.model", store=True, string="model_name")
    sequence = fields.Integer(default=16, required=True)
    priority = fields.Integer(
        default=16,
        required=True,
        help="The priority determines which rule will be "
        "selected in case of conflicting rules. "
        "Rule conflicts may exist for users with "
        "multiple roles or inconsistent role definitions.",
    )
    view_id = fields.Many2one(
        comodel_name="ir.ui.view", domain="[('model', '=', model)]"
    )
    view_type = fields.Selection(selection="_selection_view_type")
    element = fields.Char(
        help="Specify the view element. E.g."
        '\nbutton name="button_cancel"'
        '\nxpath expr="//page[@id=\'invoice_tab\\]"'
    )
    remove = fields.Boolean(
        help="Remove this view or view element from the user interface. "
        "You should use this option in stead of 'Invisible' "
        "in order to hide view elements for which the user's role "
        "does not have read Access rights."
    )
    # modifer field names should not be equal to modifier names
    # since this creates problems in the Odoo js client
    # hence we put modifier_ in front of it
    modifier_invisible = fields.Char(
        string="Invisible", help="Specify 1 (True), 0 (False) or a domain expression."
    )
    modifier_readonly = fields.Char(
        string="Readonly", help="Specify 1 (True), 0 (False) or a domain expression."
    )
    modifier_required = fields.Char(
        string="Required", help="Specify 1 (True), 0 (False) or a domain expression."
    )
    tag_ids = fields.Many2many(
        comodel_name="security.policy.tag",
        relation="policy_tag_modifier_rel",
        column1="modifier_id",
        column2="tag_id",
        string="Tags",
        help="Security Policy reporting tags",
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company", related="role_id.company_id", store=True
    )

    def _selection_view_type(self):
        return [
            ("tree", "Tree"),
            ("form", "Form"),
            ("graph", "Graph"),
            ("pivot", "Pivot"),
            ("calendar", "Calendar"),
            ("diagram", "Diagram"),
            ("gantt", "Gantt"),
            ("kanban", "Kanban"),
            ("search", "Search"),
            ("qweb", "QWeb"),
        ]

    @api.constrains("element")
    def _check_element(self):
        """TODO: add checks on element syntax"""
        pass

    @api.constrains("modifier_invisible", "modifier_readonly", "modifier_required")
    def _check_modifier(self):
        """TODO: add checks on modifier syntax"""
        pass

    def _get_rules(self, model, view_id, remove=False):
        signature_fields = self.env["web.modifier.rule"]._rule_signature_fields()
        order = ",".join(signature_fields) + ",priority"
        view = self.env["ir.ui.view"].browse(view_id)
        dom = [
            ("model", "=", model),
            ("role_id", "in", self.env.user.role_ids.ids),
            ("remove", "=", True),
            "|",
            ("view_id", "=", view_id),
            ("view_id", "=", False),
            "|",
            ("view_type", "=", view.type),
            ("view_type", "=", False),
        ]
        all_rules = self.env["web.modifier.rule"].search(dom, order=order)
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
            rules = self.env["web.modifier.rule"]
        return rules

    def _rule_signature_fields(self):
        return ["element", "view_id", "view_type"]
