# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from lxml import etree

from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.tools import locate_node, safe_eval

_logger = logging.getLogger(__name__)


class IrUiView(models.Model):
    _inherit = "ir.ui.view"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not self.env.context.get("role_policy_init") and "groups_id" in vals:
                del vals["groups_id"]
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.context.get("role_policy_init") and "groups_id" in vals:
            del vals["groups_id"]
        return super().write(vals)

    def read_combined(self, fields=None):
        res = super().read_combined(fields=fields)
        if not self.model:
            return res
        res["arch"] = self._apply_view_type_attribute_rules(res["arch"])
        archs = [(res["arch"], self.id)]
        archs = self._apply_view_modifier_remove_rules(self.model, archs)
        archs = self._apply_view_modifier_rules(self.model, archs)
        if archs:
            arch = self._remove_security_groups(archs[0][0])
        else:
            arch = self._no_access_view_arch(res)
        res["arch"] = arch
        return res

    def _apply_group(self, model, node, modifiers, fields):
        """
        Skip group processing on field and view level.
        """
        if self.env.context.get("force_apply_group"):
            return super()._apply_group(model, node, modifiers, fields)
        return True

    @api.model
    def get_inheriting_views_arch(self, view_id, model):
        archs = super().get_inheriting_views_arch(view_id, model)
        archs = self._apply_view_modifier_remove_rules(model, archs)
        archs = self._apply_view_modifier_rules(model, archs)
        return archs

    def _apply_view_type_attribute_rules(self, arch):
        vta_rules = self.env["view.type.attribute"]._get_rules(self.id)
        arch_node = etree.fromstring(arch)
        if vta_rules:
            [arch_node.set(r.attrib, r.attrib_val) for r in vta_rules]

        if not self.env.is_admin():
            operations = self.env["view.model.operation"]._operations_dict()
            vmo_rules = self.env["view.model.operation"]._get_rules(model=self.model)
            rules = vmo_rules.filtered(
                lambda r: r.operation not in vta_rules.mapped("attrib")
            )
            for rule in rules:
                for k, v in operations.items():
                    if self.type in v.get("view_types", []) and k == rule.operation:
                        arch_node.set(
                            v.get("view_type_attribute") or k,
                            rule.disable and "false" or "true",
                        )
        arch = etree.tostring(arch_node, encoding="unicode")
        return arch

    def _apply_view_modifier_remove_rules(self, model, archs_in):
        archs = archs_in[:]
        removal_indexes = []
        for i, (arch, view_id) in enumerate(archs_in):
            rules = self.env["view.modifier.rule"]._get_rules(
                model, view_id, remove=True
            )
            for rule in rules:
                if not rule.element:
                    if not rule.view_id:
                        raise UserError(
                            _(
                                "Syntax error in rule %s of role %s. "
                                "A rule without an element is only allowed "
                                "for complete view removals."
                            )
                            % (rule, rule.role_id.code)
                        )
                    removal_indexes.append(i)
                else:
                    arch_node = etree.fromstring(arch)
                    try:
                        rule_node = etree.fromstring("<{}/>".format(rule.element))
                    except Exception:
                        raise UserError(
                            _("Incorrect element definition in rule %s of role %s.")
                            % (rule, rule.role_id.code)
                        )
                    to_remove = locate_node(arch_node, rule_node)
                    if to_remove is not None:
                        to_remove.getparent().remove(to_remove)
                        arch = etree.tostring(arch_node, encoding="unicode")
                    archs[i] = (arch, view_id)
        for i in sorted(removal_indexes, reverse=True):
            del archs[i]
        return archs

    def _apply_view_modifier_rules(self, model, archs_in):
        archs = []
        for (arch, view_id) in archs_in:
            view = self.browse(view_id)
            rules = self.env["view.modifier.rule"]._get_rules(
                model, view_id, view_type=view.type
            )
            for rule in rules:
                arch_node = etree.fromstring(arch)
                el = rule.element
                try:
                    if el[:5] == "xpath":
                        expr = safe_eval(el.split("expr=")[1])
                    else:
                        parts = el.split(" ")
                        tag = parts[0].strip()
                        attrib, val = parts[1].strip().split("=")
                        attrib = attrib.strip()
                        val = val.strip()[1:-1]
                        expr = "//{}[@{}='{}']".format(tag, attrib, val)
                except Exception:
                    raise UserError(
                        _("Incorrect element definition in rule %s of role %s.")
                        % (rule, rule.role_id.code)
                    )
                expr = "({})[1]".format(expr)
                rule_node = arch_node.xpath(expr)
                if not rule_node:
                    continue
                rule_node = rule_node[0]
                attrs = []
                rule_node.attrib.pop("attrs", None)
                for mod in [
                    "modifier_invisible",
                    "modifier_readonly",
                    "modifier_required",
                ]:
                    rule_mod = getattr(rule, mod)
                    modifier = mod[9:]
                    rule_node.attrib.pop(modifier, None)
                    if rule_mod in ["0", "1"]:
                        rule_node.set(modifier, rule_mod)
                    elif rule_mod:
                        attrs.append((modifier, rule_mod))
                if attrs:
                    attrs = ", ".join(["'{}': {}".format(x[0], x[1]) for x in attrs])
                    rule_node.set("attrs", "{" + attrs + "}")
                arch = etree.tostring(arch_node, encoding="unicode")
            archs.append((arch, view_id))
        return archs

    @api.model
    def apply_inheritance_specs(
        self, source, specs_tree, inherit_id, pre_locate=lambda s: True
    ):
        """
        Avoid raise for syntax errors in web modifier rules.
        Those errors are logged into the logfile,
        cf. base/models/ir.ui.view.py, method raise_view_error:
                _logger.info(message)
        """
        try:
            source = super().apply_inheritance_specs(
                source, specs_tree, inherit_id, pre_locate=pre_locate
            )
        except ValueError:
            source = source
        return self._remove_security_groups(source)

    def _remove_security_groups(self, source):
        if "groups=" in source:
            s0, s1 = source.split("groups=", 1)
            s2 = s1.split('"', 2)[2]
            return s0 + self._remove_security_groups(s2)
        else:
            return source

    def _no_access_view_arch(self, view_dict):
        if view_dict["type"] == "form":
            message = _("Your are not allowed to view this information.")
            arch = "<form>%s</form>" % message
        else:
            raise NotImplementedError
        return arch
