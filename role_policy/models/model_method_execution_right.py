# Copyright 2020-2021 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import config

_logger = logging.getLogger(__name__)


class ModelMethodExecutionRight(models.Model):
    _name = "model.method.execution.right"
    _description = "Method Execution Right"
    _order = "name, role_id"
    _sql_constraints = [
        (
            "model_method_uniq",
            "unique(role_id, model_id, method, company_id)",
            "The method must be unique per model",
        )
    ]

    name = fields.Selection(selection="_selection_name", requireed=True)
    role_id = fields.Many2one(string="Role", comodel_name="res.role", required=True)
    model_id = fields.Many2one(
        comodel_name="ir.model",
        compute="_compute_model_method",
        store=True,
        string="Model",
    )
    method = fields.Char(
        compute="_compute_model_method",
        store=True,
        string="Method",
        help="Grant execution right for this method.",
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company", related="role_id.company_id", store=True
    )

    def _selection_name(self):
        return []

    @api.depends("name")
    def _compute_model_method(self):
        for rec in self:
            if rec.name:
                model, method = rec.name.split(",")
                rec.model_id = self.env["ir.model"].search([("model", "=", model)]).id
                rec.method = method
            else:
                rec.model_id = False
                rec.method = False

    @api.model
    def check_right(self, name, raise_exception=True):
        if self.env.user.exclude_from_role_policy or config.get("test_enable"):
            return True
        user_roles = self.env.user.enabled_role_ids or self.env.user.role_ids
        model_methods = user_roles.mapped("model_method_ids").filtered(
            lambda r: r.name == "account.move,post"
            and r.company_id == self.env.user.company_id
            and r.active
        )
        if not model_methods and raise_exception:
            raise UserError(
                _("Your security role does not allow you to execute method %s") % name
            )
        else:
            return model_methods and True or False
