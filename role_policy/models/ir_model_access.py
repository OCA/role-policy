# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)

_CRUD = {"c": "create", "r": "read", "u": "update", "d": "unlink"}


class IrModelAccess(models.Model):
    _inherit = "ir.model.access"

    @api.model
    def _get_acl_access_group_ids(self, model, crud):
        """
        Return the group ids which allow ACL access
        of type 'access' to 'model'.

        :param model: the name of the ORM model, e.g. sale.order
        :param crud: any combinatie of the letters crud

        :return: the ids of the groups granting the requested accesses.
        """
        # pylint: disable=E8103
        query = (
            """
        SELECT rg.id
          FROM ir_model_access ima
          INNER JOIN ir_model im ON ima.model_id = im.id
          INNER JOIN res_groups rg ON ima.group_id = rg.id
          WHERE im.model = '%s' AND ima.active = TRUE
        """
            % model
        )
        for access in crud:
            assert access in _CRUD, "Invalid crud parameter"
            query += "AND ima.perm_%s = TRUE " % _CRUD[access]
        self.env.cr.execute(query)
        gids = self.env.cr.fetchall()
        return [x[0] for x in gids]
