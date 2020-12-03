# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResGroups(models.Model):
    _inherit = "res.groups"

    role = fields.Boolean()

    """
    TODO:
    add def create/write to disable adding menu, action, view access
    via the groups m2m relations.
    """
