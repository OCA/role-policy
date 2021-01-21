# Copyright 2020-2021 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.http import request
from odoo.tools import config


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        res = super().session_info()
        user = request.env.user
        user_roles = self.env.user.enabled_role_ids or self.env.user.role_ids
        operations = ["archive", "create", "export", "import"]
        rules = (
            self.env["view.model.operation"]
            ._get_rules()
            .filtered(lambda r: r.operation in operations)
        )
        model_operations = {k: {} for k in operations}
        for rule in rules:
            model_operations[rule.operation][rule.model] = rule.disable
        res.update(
            {
                "roles": [(r.id, r.code) for r in user_roles],
                "model_operations": model_operations,
                "exclude_from_role_policy": user.exclude_from_role_policy
                or config.get("test_enable"),
            }
        )
        return res
