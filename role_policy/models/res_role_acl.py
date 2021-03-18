# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

CRUD2FLD = {"c": "perm_create", "r": "perm_read", "u": "perm_write", "d": "perm_unlink"}


class ResRoleAcl(models.Model):
    _name = "res.role.acl"
    _description = "Role ACL"
    _order = "name"
    _sql_constraints = [
        (
            "model_role_uniq",
            "unique(model_id, role_id, company_id)",
            "The Model must be unique per role",
        ),
        ("name_uniq", "unique(name, company_id)", "The Name must be unique"),
        (
            "crud_nut_null",
            "CHECK(perm_read OR perm_write OR perm_create OR perm_unlink)",
            "At least one access must be set !",
        ),
    ]

    name = fields.Char(readonly=True)
    role_id = fields.Many2one(comodel_name="res.role", required=True)
    model_id = fields.Many2one(comodel_name="ir.model", required=True)
    group_id = fields.Many2one(comodel_name="res.groups", readonly=True)
    access_id = fields.Many2one(
        comodel_name="ir.model.access", ondelete="restrict", readonly=True
    )
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
        if vals.get("active", True):
            self._create_role_acl(vals)
        return super().create(vals)

    def unlink(self):
        self._unlink_role_acl()
        return super().unlink()

    def write(self, vals):
        self._update_role_acl(vals)
        return super().write(vals)

    def _create_role_acl(self, vals):
        role = self.env["res.role"].browse(vals["role_id"])
        model = self.env["ir.model"].browse(vals["model_id"])
        crud = self._compute_crud(vals)
        acl_group = self._compute_group(model, crud, role)
        role.group_id.implied_ids += acl_group
        name = "_".join([role.code, acl_group.name])
        access = self._compute_access(model, crud, acl_group)
        vals.update({"name": name, "group_id": acl_group.id, "access_id": access.id})

    def _unlink_role_acl(self):
        for acl in self:
            acl.role_id.group_id.implied_ids -= acl.group_id
            for user in acl.group_id.users:
                extra_roles = user.role_ids - acl.role_id
                if acl.group_id in extra_roles.mapped("group_id.implied_ids"):
                    continue
                acl.group_id.users -= user

    def _update_role_acl(self, vals):
        for acl in self:
            old_acl_group = acl.group_id
            crud = acl._compute_crud(vals)
            model = (
                vals.get("model_id")
                and self.env["ir.model"].browse(vals["model_id"])
                or acl.model_id
            )
            acl_group = acl._compute_group(model, crud, acl.role_id)
            if acl_group != old_acl_group:
                acl.role_id.group_id.implied_ids = [
                    (3, old_acl_group.id),
                    (4, acl_group.id),
                ]
                acl.role_id.user_ids.update({"groups_id": [(3, old_acl_group.id)]})
                access = self._compute_access(model, crud, acl_group)
                vals.update(
                    {
                        "name": "_".join([acl.role_id.code, acl_group.name]),
                        "group_id": acl_group.id,
                        "access_id": access.id,
                    }
                )
            if "active" in vals and vals["active"] != acl.active:
                if not vals["active"]:
                    acl.role_id.group_id.implied_ids = [(3, acl_group.id)]
                    acl.role_id.user_ids.update({"groups_id": [(3, acl_group.id)]})
                else:
                    acl.role_id.group_id.implied_ids = [(4, acl_group.id)]
                    acl.role_id.user_ids.update({"groups_id": [(4, acl_group.id)]})

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
            crud += self.perm_unlink and "d" or ""
        return crud

    def _compute_group(self, model, crud, role):
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

    def _compute_access(self, model, crud, acl_group):
        access = self.env["ir.model.access"].search([("name", "=", acl_group.name)])
        if not access:
            access_vals = {CRUD2FLD[k]: True for k in crud}
            access_vals.update(
                {"name": acl_group.name, "model_id": model.id, "group_id": acl_group.id}
            )
            access = self.env["ir.model.access"].create(access_vals)
        return access
