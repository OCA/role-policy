# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import safe_eval

_logger = logging.getLogger(__name__)


class WebModifierRule(models.Model):
    _name = "web.modifier.rule"
    _description = "View Modifiers Rule"
    _order = "role_id, sequence"
    _sql_constraints = [
        (
            "element_uniq",
            "unique(role_id, element, model_id, view_id, view_type, company_id)",
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
    view_xml_id = fields.Char(
        string="View External Identifier", related="view_id.xml_id", store=True
    )
    view_type = fields.Selection(selection="_selection_view_type", required=True)
    element_ui = fields.Char(
        string="Element",
        help="Specify the view element. E.g."
        '\nbutton name="button_cancel"'
        '\nxpath expr="//page[@id=\'invoice_tab\\]"',
    )
    element = fields.Char(
        string="Element (internal)",
        compute="_compute_element",
        store=True,
        help="Technical field containt the element after XML_ID resolution",
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

    @api.depends("element_ui")
    def _compute_element(self):
        errors = ""
        for rule in self:
            rule_errors = []
            rule.element = rule._resolve_rule_element(rule_errors)
            if rule_errors:
                rule_errors.insert(0, _("Error while processing rule %s") % rule)
                errors += "\n".join(rule_errors) + "\n"
        if errors:
            raise UserError(errors)

    def _resolve_rule_element(self, line_errors):
        """ return modifier rule element which is equal to element_ui
            but with replacement of XML Id by DB Id for actions buttons.
        """
        element = element_ui = self.element_ui
        if element_ui:
            if element_ui[:5] == "xpath":
                to_update = False
                parts = element_ui.split("button[@name=")
                for i, part in enumerate(parts[1:], start=1):
                    name, name_close = part.split("]")
                    name2 = self._resolve_rule_element_button_name(name, line_errors)
                    if name2 != name:
                        to_update = True
                        parts[i] = "]".join([name2, name_close])
                if to_update:
                    element = "button[@name=".join(parts)
            elif element_ui[:7] == "button ":
                parts = element_ui.split("name=")
                if len(parts) > 1:
                    name = parts[1]
                    name2 = self._resolve_rule_element_button_name(name, line_errors)
                    if name2 != name:
                        parts[1] = name2
                        element = "button ".join(parts)
        return element

    def _resolve_rule_element_button_name(self, name, line_errors):
        name = safe_eval(name)
        if name[:2] == "%(" and name[-2:] == ")d":
            xml_id = name[2:-2]
            act_id = self.env["ir.model.data"].xmlid_to_res_model_res_id(
                xml_id, raise_if_not_found=False
            )
            if act_id[0] not in [
                "ir.actions.act_window",
                "ir.actions.server",
                "ir.actions.report.xml",
            ]:
                line_errors.append(
                    _("Incorrect value '%s' for button name in field 'Element'.")
                    % self.element_ui
                )
            else:
                name = "'{}'".format(act_id[1])
        else:
            self._check_element_ui_button_name(name, line_errors)
        return name

    def _check_element_ui_button_name(self, name, line_errors):
        try:
            name = int(safe_eval(name))
        except Exception:
            pass
        if isinstance(name, int):
            err = _("Syntax Error in field Element '%s'") % self.element_ui
            err += "\n"
            err += _("Use the External Identifier for action buttons.")
            err += "\n"
            err += _('e.g. name="%(sale.act_res_partner_2_sale_order)d"')
            line_errors.append(err)

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
            ("remove", "=", remove),
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
