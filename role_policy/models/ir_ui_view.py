# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models

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
        res = super().get_inheriting_views_arch(view_id, model)
        res.extend(self._get_web_modifier_rule_views_arch(view_id, model))
        return res

    def _get_web_modifier_rule_views_arch(self, view_id, model):
        rule_views = []
        if not model:
            return rule_views
        rules = self.env["web.modifier.rule"]._get_rules(model, view_id)
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
                rule_views.append((rule_arch, False))
        return rule_views

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
