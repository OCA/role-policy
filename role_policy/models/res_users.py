# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    role_ids = fields.Many2many(
        comodel_name="res.role",
        relation="res_role_users_rel",
        column1="uid",
        column2="role_id",
        string="Roles",
    )

    @api.model_create_multi
    def create(self, vals_list):
        group_user = self.env.ref("base.group_user")
        for vals in vals_list:
            if "role_ids" in vals:
                roles = self.env["res.role"].browse(vals["role_ids"][0][2])
                group_ids = [group_user.id] + [x.id for x in roles.mapped("group_id")]
                vals["groups_id"] = [(6, 0, group_ids)]
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if "role_ids" in vals:
            group_user = self.env.ref("base.group_user")
            for user in self:
                user.groups_id = group_user + user.role_ids.mapped("group_id")
        return res

    @api.model
    def _has_group(self, group_ext_id):
        if self.env.context.get("role_policy_has_groups_ok"):
            return True
        else:
            return super()._has_group(group_ext_id)
