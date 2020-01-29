# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    role_ids = fields.Many2many(
        comodel_name="res.role",
        relation="res_role_users_rel",
        column1="uid",
        column2="role_id",
        string="Roles",
    )
