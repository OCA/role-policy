# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class IrUiView(models.Model):
    _inherit = "ir.ui.view"

    def _apply_group(self, model, node, modifiers, fields):
        """
        Skip group processing on field and view level.
        """
        if self.env.context.get('force_apply_group'):
            return super()._apply_group(model, node, modifiers, fields)
        return True
