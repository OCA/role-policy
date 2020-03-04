# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from collections import defaultdict

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class IrActionsActions(models.Model):
    _inherit = "ir.actions.actions"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not self.env.context.get("role_policy_init") and "groups_id" in vals:
                del vals["groups_id"]
            if "role_ids" in vals:
                roles = self.env["res.role"].browse(vals["role_ids"][0][2])
                vals["groups_id"] = [(6, 0, [x.id for x in roles.mapped("group_id")])]
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.context.get("role_policy_init") and "groups_id" in vals:
            del vals["groups_id"]
        res = super().write(vals)
        if "role_ids" in vals:
            for action in self:
                action.groups_id = action.role_ids.mapped("group_id")
        return res

    @api.model
    def get_bindings(self, model_name):
        res = super().get_bindings(model_name)
        admin = self.env.ref("base.user_admin")
        root = self.env.ref("base.user_root")
        if self.env.user not in (admin, root):
            user_roles = self.env.user.role_ids
            user_groups = user_roles.mapped("group_id")
            res_roles = defaultdict(list)
            for k in res:
                res_roles[k] = []
                for v in res[k]:
                    if v.get("groups_id"):
                        for group_id in v["groups_id"]:
                            if group_id in user_groups.ids:
                                res_roles[k].append(v)
                                continue
            return res_roles
        return res


class IrActionsActWindow(models.Model):
    _inherit = "ir.actions.act_window"

    role_ids = fields.Many2many(
        comodel_name="res.role",
        relation="res_role_act_window_rel",
        column1="act_window_id",
        column2="role_id",
        string="Roles",
    )


class IrActionsServer(models.Model):
    _inherit = "ir.actions.server"

    role_ids = fields.Many2many(
        comodel_name="res.role",
        relation="res_role_server_rel",
        column1="act_server_id",
        column2="role_id",
        string="Roles",
    )


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    role_ids = fields.Many2many(
        comodel_name="res.role",
        relation="res_role_report_rel",
        column1="act_report_id",
        column2="role_id",
        string="Roles",
    )
