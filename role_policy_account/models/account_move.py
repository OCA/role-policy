# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def post(self):
        self.env["model.method.execution.right"].check_right(
            "account.move,post", raise_exception=True
        )
        ctx = dict(self.env.context, role_policy_has_groups_ok=True)
        self = self.with_context(ctx)
        return super().post()
