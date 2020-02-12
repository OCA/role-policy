# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResRoleAcl(models.Model):
    _name = "res.role.acl"
    _description = "Role ACL"
    _sql_constraints = [
        ("name_uniq", "unique(name, company_id)", "The Name must be unique")
    ]

    name = fields.Char(readonly=True)
    role_id = fields.Many2one(comodel_name="res.role", required=True)
    model_id = fields.Many2one(comodel_name="ir.model", required=True)
    group_id = fields.Many2one(comodel_name="res.groups", readonly=True)
    access_id = fields.Many2one(comodel_name="ir.model.access", readonly=True)
    perm_read = fields.Boolean(string="Read Access")
    perm_write = fields.Boolean(string="Write Access")
    perm_create = fields.Boolean(string="Create Access")
    perm_unlink = fields.Boolean(string="Delete Access")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company", related="role_id.company_id", store=True
    )

    @api.model
    def create(self, vals):
        self._create_role_acl(vals)
        return super().create(vals)

    def _create_role_acl(self, vals):
        crud = self._compute_crud(vals)
        role = self.env["res.role"].browse(vals["role_id"])
        group = self._compute_group(vals, crud, role)
        role.group_id.implied_ids += group
        name = "_".join([role.code, group.name])
        access = self._compute_access(vals, group)
        vals.update({"name": name, "group_id": group.id, "access_id": access.id})

    def write(self, vals):
        self._update_role_acl(vals)
        return super().write(vals)

    def _update_role_acl(self, vals):
        for acl in self:
            crud = acl._compute_crud(vals)
            acl._compute_group(vals, crud)

    def _compute_crud(self, vals):
        if "perm_create" in vals:
            crud = vals["perm_create"] and "c" or ""
        else:
            crud = self.perm_create and "c" or ""
        if "perm_read" in vals:
            crud += vals["perm_read"] and "r" or ""
        else:
            crud += self.perm_read and "r" or ""
        if "perm_write" in vals:
            crud += vals["perm_write"] and "u" or ""
        else:
            crud += self.perm_write and "u" or ""
        if "perm_unlink" in vals:
            crud += vals["perm_unlink"] and "d" or ""
        else:
            crud += self.perm_write and "d" or ""
        return crud

    def _compute_group(self, vals, crud, role):
        if vals.get("model_id"):
            model = self.env["ir.model"].browse(vals["model_id"])
        else:
            model = self.model_id
        group_name = "_".join(["role_acl", model.model.replace(".", "_"), crud])
        if role.company_id:
            group_name += "_{}".format(role.company_id.id)
        group = self.env["res.groups"].search([("name", "=", group_name)])
        if not group:
            categ = self.env.ref("role_policy.ir_module_category_role")
            group = self.env["res.groups"].create(
                {"role": True, "name": group_name, "category_id": categ.id}
            )
        return group

    def _compute_access(self, vals, group):
        access_name = "acl_{}".format(group.name)
        access = self.env["ir.model.access"].search([("name", "=", access_name)])
        if not access:
            access_vals = {
                k: vals[k]
                for k in vals
                if k in ["perm_read", "perm_write", "perm_create", "perm_unlink"]
            }
            access_vals.update(
                {
                    "name": access_name,
                    "model_id": vals["model_id"],
                    "group_id": group.id,
                }
            )
            access = self.env["ir.model.access"].create(access_vals)
        return access
