# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SecurityPolicyTag(models.Model):
    _name = "security.policy.tag"
    _description = "Security Policy reporting tags"
    _order = "code,name"

    code = fields.Char(required=True)
    name = fields.Char(required=True)
    note = fields.Text(name="Description")
    modifier_ids = fields.Many2many(
        comodel_name="view.modifier.rule",
        relation="policy_tag_modifier_rel",
        column1="tag_id",
        column2="modifier_id",
        string="Tags",
        help="Security Policy reporting tags",
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self._default_company_id(),
    )

    @api.model
    def _default_company_id(self):
        return self.env.user.company_id
