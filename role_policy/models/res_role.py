# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResRole(models.Model):
    _name = "res.role"
    _description = "Role"
    _inherit = ["mail.thread"]
    _sql_constraints = [
        ("code_company_uniq", "unique (code, company_id)", "The code must be unique !")
    ]

    name = fields.Char(required=True)
    code = fields.Char(required=True, size=5)
    modifier_rule_ids = fields.One2many(
        comodel_name="web.modifier.rule",
        inverse_name="role_id",
        string="Web Modifier Rules",
    )
    menu_ids = fields.Many2many(
        comodel_name="ir.ui.menu",
        relation="res_role_menu_rel",
        column1="role_id",
        column2="menu_id",
        string="Menu Items",
    )
    user_ids = fields.Many2many(
        comodel_name="res.users",
        relation="res_role_users_rel",
        column1="role_id",
        column2="uid",
        string="Users",
    )
    sequence = fields.Integer()
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self._default_company_id(),
    )

    @api.model
    def _default_company_id(self):
        return self.env.user.company_id
