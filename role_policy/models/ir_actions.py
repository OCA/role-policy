# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from collections import defaultdict

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class IrActionsActions(models.Model):
    _inherit = "ir.actions.actions"

    @api.model
    def get_bindings(self, model_name):
        res = super().get_bindings(model_name)
        user_roles = self.env.user.role_ids
        res_roles = defaultdict(list)
        for k in res:
            res_roles[k] = []
            for v in res[k]:
                if not v.get("role_ids"):
                    res_roles[k].append(v)
                    continue
                for rid in user_roles.ids:
                    if rid in v["role_ids"]:
                        res_roles[k].append(v)
                        continue
        return res_roles


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
