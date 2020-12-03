# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models

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
        pass

    def _get_rules(self, view_id):
        signature_fields = self._rule_signature_fields()
        dom = [("view_id", "=", view_id), ("role_id", "in", self.env.user.role_ids.ids)]
        all_rules = self.search(dom)
        all_rules = all_rules.sorted(key=lambda r: (r.attrib or "", r.priority))
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
        return ["view_id", "attrib"]
