# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from lxml import etree

from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.tools import locate_node

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
        res["arch"] = self._remove_security_groups(res["arch"])
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
        if model:
            self._apply_web_modifier_rules(view_id, model, archs)
            archs = self._apply_web_modifier_remove_rules(model, archs)
        return archs

    def _apply_web_modifier_rules(self, view_id, model, archs):
        rules = self.env["web.modifier.rule"]._get_rules(model, view_id, remove=False)
        template_modifier = '<attribute name="{}">{}</attribute>'
        template_attrs = '<attribute name="attrs">{{"{}": {}}}</attribute>'
        for rule in rules:
            rule_arch = '<{} position="attributes">'.format(rule.element)
            mod_arch = False
            for mod in ["modifier_invisible", "modifier_readonly", "modifier_required"]:
                rule_mod = getattr(rule, mod)
                modifier = mod[9:]
                if rule_mod in ["0", "1"]:
                    mod_arch = template_modifier.format(modifier, int(rule_mod))
                    rule_arch += mod_arch
                elif rule_mod:
                    mod_arch = template_attrs.format(modifier, rule_mod)
                    rule_arch += mod_arch
            if mod_arch:
                rule_arch += "</{}>".format(rule.element.split()[0])
                archs.append((rule_arch, False))

    def _apply_web_modifier_remove_rules(self, model, archs_in):
        archs = archs_in[:]
        removal_indexes = []
        for i, (arch, view_id) in enumerate(archs_in):
            rules = self.env["web.modifier.rule"]._get_rules(
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
        if not inherit_id:
            try:
                source = super().apply_inheritance_specs(
                    source, specs_tree, inherit_id, pre_locate=pre_locate
                )
            except ValueError:
                source = source
        else:
            source = super().apply_inheritance_specs(
                source, specs_tree, inherit_id, pre_locate=pre_locate
            )
        return self._remove_security_groups(source)

    def _remove_security_groups(self, source):
        if "groups=" in source:
            s0, s1 = source.split("groups=", 1)
            s2 = s1.split('"', 2)[2]
            return s0 + self._remove_security_groups(s2)
        else:
            return source
