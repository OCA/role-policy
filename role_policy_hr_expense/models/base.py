# Copyright 2009-2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class BaseModel(models.AbstractModel):
    _inherit = "base"

    def _role_policy_untouchable_groups(self):
        res = super()._role_policy_untouchable_groups()
        res.append("hr_expense.group_hr_expense_team_approver")
        return res
