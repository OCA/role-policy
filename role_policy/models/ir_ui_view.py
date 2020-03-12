# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class IrUiView(models.Model):
    _inherit = "ir.ui.view"

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
