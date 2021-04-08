# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from collections import defaultdict

from odoo import api, fields, models

from .helpers import filter_odoo_x2many_commands

_logger = logging.getLogger(__name__)


class IrActionsActions(models.Model):
    _inherit = "ir.actions.actions"

    def __getattribute__(self, item):
        """
        ignore role groups for the 'exclude_from_role_policy' users
        """
        res = super().__getattribute__(item)
        if item == "groups_id" and self.env.user.exclude_from_role_policy:
            res = res.filtered(lambda r: not r.role)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        keep_ids = self._get_role_policy_group_keep_ids()
        for vals in vals_list:
            if not self.env.context.get("role_policy_init") and "groups_id" in vals:
                commands = filter_odoo_x2many_commands(
                    vals.get("groups_id", []), keep_ids
                )
                if commands:
                    vals["groups_id"] = commands
                else:
                    del vals["groups_id"]
            if "role_ids" in vals:
                roles = self.env["res.role"].browse(vals["role_ids"][0][2])
                vals["groups_id"].extend([(4, x.id) for x in roles.mapped("group_id")])
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.context.get("role_policy_init") and "groups_id" in vals:
            keep_ids = self._get_role_policy_group_keep_ids()
            commands = filter_odoo_x2many_commands(vals.get("groups_id", []), keep_ids)
            if commands:
                vals["groups_id"] = commands
            else:
                del vals["groups_id"]
        res = super().write(vals)
        if "role_ids" in vals:
            for action in self:
                action.groups_id += [
                    (4, x.id) for x in action.role_ids.mapped("group_id")
                ]
        return res

    @api.model
    def get_bindings(self, model_name):
        res = super().get_bindings(model_name)
        if not self.env.user.exclude_from_role_policy:
            user_roles = self.env.user.enabled_role_ids or self.env.user.role_ids
            user_groups = user_roles.mapped("group_id")
            for group in self._role_policy_untouchable_groups():
                user_groups += self.env.ref(group)
            res_roles = defaultdict(list)
            for k in res:
                res_roles[k] = []
                for v in res[k]:
                    if v.get("groups_id"):
                        for group_id in v["groups_id"]:
                            if group_id in user_groups.ids and v not in res_roles[k]:
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
