# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    role_ids = fields.Many2many(
        comodel_name="res.role",
        relation="res_role_menu_rel",
        column1="menu_id",
        column2="role_id",
        string="Roles",
    )

    @api.model
    def _visible_menu_ids(self, debug=False):
        visible_ids = super()._visible_menu_ids(debug=debug)
        menus = self.browse(visible_ids)
        roles = self.env.user.role_ids
        menus = menus.filtered(
            lambda menu: not menu.role_ids or menu.role_ids & roles)
        return set(menus.ids)
