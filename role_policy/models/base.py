# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class BaseModel(models.AbstractModel):
    _inherit = "base"

    @api.model
    def user_has_groups(self, groups):
        """
        Disable no-role groups except for user_admin & user_root.
        """
        user = self.env.user
        if user in [
            self.env.ref("base.user_admin"),
            self.env.ref("base.user_root"),
            self.env.ref("base.public_user"),
        ]:
            return super().user_has_groups(groups)

        role_groups = []
        for group_ext_id in groups.split(","):
            xml_id = group_ext_id[0] == "!" and group_ext_id[1:] or group_ext_id
            if xml_id in [
                "base.group_no_one",
                "base.group_erp_manager",
                "base.group_system",
                "base.group_portal",
                "base.group_public",
            ]:
                role_groups.append(group_ext_id)
            else:
                group = self.env.ref(xml_id)
                if group.role:
                    role_groups.append(group_ext_id)
        if not role_groups:
            return True
        else:
            return super().user_has_groups(",".join(role_groups))
