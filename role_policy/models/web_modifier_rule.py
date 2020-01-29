# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from collections import defaultdict

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import locate_node

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
    view_id = fields.Many2one(comodel_name="ir.ui.view")
    view_type = fields.Selection(selection="_selection_view_type")
    element = fields.Char(
        help="Specify the view element. E.g."
        '\nbutton name="button_cancel"'
        '\nxpath expr="//page[@id=\'invoice_tab\\]"'
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

    @api.constrains("modifier_invisible")
    def _check_modifier_invisible(self):
        if self.modifier_invisible:
            self._check_modifier(self.modifier_invisible)

    @api.constrains("modifier_readonly")
    def _check_modifier_readonly(self):
        if self.modifier_readonly:
            self._check_modifier(self.modifier_readonly)

    @api.constrains("modifier_required")
    def _check_modifier_required(self):
        if self.modifier_required:
            self._check_modifier(self.modifier_required)

    def _check_modifier(self, modifier):
        """TODO: add checks on modifier syntax"""
        pass

    def _register_hook(self):
        """
        Similar approach as in standard addons, module 'base_automation'.
        """

        def role_policy_fields_view_get():
            """
            Instanciate a fields_view_get method that processes
            view modifier rules.
            """

            @api.model
            def fields_view_get(
                self, view_id=None, view_type="form", toolbar=False, submenu=False
            ):
                res = fields_view_get.origin(
                    self,
                    view_id=view_id,
                    view_type=view_type,
                    toolbar=toolbar,
                    submenu=submenu,
                )
                arch_node = etree.fromstring(res["arch"])
                rules = self.env["web.modifier.rule"]._get_rules(
                    self._name, view_id=view_id, view_type=view_type
                )
                arch_update = False
                for rule in rules:
                    try:
                        rule_node = etree.fromstring("<{}/>".format(rule.element))
                    except Exception:
                        raise UserError(
                            _("Incorrect element defintion in rule %s " "of role %s.")
                            % (rule, rule.role_id.code)
                        )
                    view_node = locate_node(arch_node, rule_node)
                    if view_node is not None:
                        _logger.debug(
                            "fields_view_get, view_id=%s, view_type=%s,"
                            "rule_id=%s, element=%s, modifiers before rule = %s",
                            view_id,
                            view_type,
                            rule.id,
                            rule.element,
                            view_node.attrib.get("modifiers"),
                        )
                        modifiers = ""
                        for mod in [
                            "modifier_invisible",
                            "modifier_readonly",
                            "modifier_required",
                        ]:
                            rule_mod = getattr(rule, mod)
                            modifier = mod[9:]
                            if rule_mod:
                                modifiers += '"{}": {}'.format(modifier, rule_mod)
                        view_node.attrib["modifiers"] = "{" + modifiers + "}"
                        _logger.debug(
                            "fields_view_get, view_id=%s, view_type=%s,"
                            "rule_id=%s, element=%s, modifiers after rule = %s",
                            view_id,
                            view_type,
                            rule.id,
                            rule.element,
                            view_node.attrib.get("modifiers"),
                        )
                        arch_update = True
                if arch_update:
                    res["arch"] = etree.tostring(arch_node)
                return res

            return fields_view_get

        rules = self.with_context({}).search([])
        patched_models = defaultdict(set)

        def patch(model, name, method):

            if model not in patched_models[name]:
                patched_models[name].add(model)
                model._patch_method(name, method)

        for rule in rules:
            model_name = rule.model_id.model
            model = self.env.get(model_name)
            # Do not crash if the model of the rule was uninstalled
            if model is None:
                _logger.error(
                    _("Model %s of rule %s does not exist.") % (model_name, rule)
                )
                continue
            patch(model, "fields_view_get", role_policy_fields_view_get())

    def _get_rules(self, model, view_id=None, view_type=None):
        signature_fields = self.env["web.modifier.rule"]._rule_signature_fields()
        order = ",".join(signature_fields) + ",priority"
        all_rules = self.env["web.modifier.rule"].search(
            [("model", "=", model), ("role_id", "in", self.env.user.role_ids.ids)],
            order=order,
        )
        if view_id:
            all_rules = (
                all_rules.filtered(lambda r: r.view_id.id == view_id) or all_rules
            )
        if view_type:
            all_rules = (
                all_rules.filtered(lambda r: r.view_type == view_type) or all_rules
            )
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
