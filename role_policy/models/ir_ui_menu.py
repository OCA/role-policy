# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    role_ids = fields.Many2many(
        comodel_name="res.role",
        relation="res_role_menu_rel",
        column1="menu_id",
        column2="role_id",
        string="Roles",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "groups_id" in vals:
                del vals["groups_id"]
            if "role_ids" in vals:
                roles = self.env["res.role"].browse(vals["role_ids"][0][2])
                vals["groups_id"] = [(6, 0, [x.id for x in roles.mapped("group_id")])]
        return super().create(vals_list)

    def write(self, vals):
        if "groups_id" in vals:
            del vals["groups_id"]
        res = super().write(vals)
        if "role_ids" in vals:
            for menu in self:
                menu.groups_id = menu.role_ids.mapped("group_id")
        return res
