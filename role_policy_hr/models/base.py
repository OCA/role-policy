# Copyright 2009-2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class BaseModel(models.AbstractModel):
    _inherit = "base"

    def _role_policy_untouchable_groups(self):
        """
        An employee record is stored in the database via the hr_employee table
        but only a subset of these fields are available to the regular users.
        Only users belonging to the "hr.group_hr_user" can retrieve all fields.
        """
        res = super()._role_policy_untouchable_groups()
        res.append("hr.group_hr_user")
        return res
