# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        res = super().session_info()
        user = request.env.user
        rules = self.env["view.model.operation"]._get_rules()
        export_operations = {}
        archive_operations = {}
        for rule in rules:
            if rule.operation == "export":
                export_operations[rule.model] = rule.disable
            else:
                archive_operations[rule.model] = rule.disable
        res.update(
            {
                "roles": [(r.id, r.code) for r in user.role_ids],
                "sidebar_operations": {
                    "export_operations": export_operations,
                    "archive_operations": archive_operations,
                },
            }
        )
        return res
