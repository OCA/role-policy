# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        res = super().session_info()
        user = request.env.user
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
                "roles": [(r.id, r.code) for r in user.role_ids],
                "model_operations": model_operations,
            }
        )
        return res
