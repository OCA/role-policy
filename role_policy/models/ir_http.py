# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        res = super().session_info()
        user = request.env.user
        sidebar_option_rules = self.env["view.sidebar.option"]._get_rules()
        export_options = {}
        archive_options = {}
        for rule in sidebar_option_rules:
            if rule.option == "export":
                export_options[rule.model] = rule.disable
            else:
                archive_options[rule.model] = rule.disable
        res.update(
            {
                "roles": [(r.id, r.code) for r in user.role_ids],
                "sidebar_options": {
                    "export_options": export_options,
                    "archive_options": archive_options,
                },
            }
        )
        return res
