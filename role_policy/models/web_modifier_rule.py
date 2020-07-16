# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict
import logging
from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import safe_eval, locate_node

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
    view_type = fields.Selection(selection="_selection_view_type")
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
                    name, remaining = part.split("]")
                    name2 = self._resolve_rule_element_button_name(name, line_errors)
                    if name2 != name:
                        to_update = True
                        parts[i] = "]".join([name2, remaining])
                if to_update:
                    element = "button[@name=".join(parts)
            elif element_ui[:7] == "button ":
                parts = element_ui.split("name=")
                if len(parts) > 1:
                    part1 = parts[1].split(" ", 1)
                    name = part1[0]
                    if len(part1) == 2:
                        remaining = part1[1]
                    else:
                        remaining = False
                    name2 = self._resolve_rule_element_button_name(name, line_errors)
                    if name2 != name:
                        element = "name=".join([parts[0], name2])
                        if remaining:
                            element += " " + remaining
        return element

    def _resolve_rule_element_button_name(self, name, line_errors):
        quote_char = name[0]
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
                name = quote_char + str(act_id[1]) + quote_char
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

    @api.constrains("view_id", "view_type")
    def _check_view(self):
        for rule in self:
            if rule.view_id:
                if rule.viev_type != rule.view_id.type:
                    raise UserError(_(
                        "Error in rule with ID %s: "
                        "view_type is not consistent with view."
                    ) % rule.id)
            else:
                if rule.remove:
                    raise UserError(_(
                        "Error in rule with ID %s: "
                        "'Remove' requires to define a view."
                    ) % rule.id)

    @api.constrains("modifier_invisible", "modifier_readonly", "modifier_required")
    def _check_modifier(self):
        """TODO: add checks on modifier syntax"""
        pass

    @api.onchange('view_id')
    def _onchange_view_id(self):
        self.view_type = self.view_id.type
        if not self.view_id:
            self.remove = False

    def _register_hook(self):
        """
        Similar approach as in standard addons, module 'base_automation'.
        """

        def role_policy_fields_view_get():
            """
            Instanciate a fields_view_get method that processes
            view modifier rules.
            We use this technique only for those rules that have no view_id
            specified (e.g. to hide a specific button or field from all views
            on an object).
            Security errors may occur since we post-process the fields_view_get
            output (when hitting an ACL error on a field, you should remove the
            field explicitly from the view by specifying the view_id).
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
                    self._name, False, view_type=False, remove=False,
                    call_method='fields_view_get')
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

        rules = self.with_context({}).search([('view_id', '=', False)])
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

    def _get_rules(self, model, view_id, view_type=False, remove=False,
                   call_method=False):
        signature_fields = self.env["web.modifier.rule"]._rule_signature_fields()
        dom = [
            ("model", "=", model),
            ("role_id", "in", self.env.user.role_ids.ids),
            ("remove", "=", remove),
        ]
        if call_method == 'fields_view_get':
            dom += [
                '|',
                ('view_id', '=', view_id),
                ('view_id', '=', False),
                '|',
                ('view_type', '=', view_type),
                ('view_type', '=', False),
            ]
        else:
            dom += [
                ('view_id', '=', view_id),
                ('view_type', '=', view_type),
            ]
        all_rules = self.env["web.modifier.rule"].search(dom)
        all_rules = all_rules.sorted(
            key=lambda r:
            (r.element, r.view_id or '0', r.view_type or '0', r.priority)
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
