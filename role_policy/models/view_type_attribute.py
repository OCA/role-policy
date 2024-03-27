# Copyright 2020-2021 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models
from odoo.tools import config

_logger = logging.getLogger(__name__)


class ViewTypeAttribute(models.Model):
    _name = "view.type.attribute"
    _description = "View Type Attribute"
    _order = "role_id, sequence"
    _sql_constraints = [
        (
            "view_attrib_uniq",
            "unique(role_id, view_id, attrib, company_id)",
            "The View Type Attribute must be unique",
        )
    ]

    role_id = fields.Many2one(string="Role", comodel_name="res.role", required=True)
    sequence = fields.Integer(default=16, required=True)
    priority = fields.Integer(
        default=16,
        required=True,
        help="The priority determines which attribute rule will be "
        "selected in case of conflicting attribute rules. "
        "Rule conflicts may exist for users with "
        "multiple roles or inconsistent role definitions.",
    )
    view_id = fields.Many2one(comodel_name="ir.ui.view", required=True)
    view_xml_id = fields.Char(
        string="View External Identifier", related="view_id.xml_id", store=True
    )
    view_type = fields.Selection(related="view_id.type")
    attrib = fields.Char(string="Attribute", required=True)
    attrib_val = fields.Char(string="Attribute Value", required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company", related="role_id.company_id", store=True
    )

    @api.constrains("view_id", "attrib", "attrib_val")
    def _check_view_attribute(self):
        """TODO: add checks on syntax"""

    def _get_rules(self, view_id):
        rules = self.browse()
        if config.get("test_enable"):
            return rules
        signature_fields = self._rule_signature_fields()
        user_roles = self.env.user.enabled_role_ids or self.env.user.role_ids
        dom = [("view_id", "=", view_id), ("role_id", "in", user_roles.ids)]
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
        return rules

    def _rule_signature_fields(self):
        return ["view_id", "attrib"]
