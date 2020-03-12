# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    """
    Remove groups from menuitems, views, actions and users since the standard groups
    are replaced by role groups when installing this module.
    """
    env = api.Environment(
        cr, SUPERUSER_ID, {"active_test": False, "role_policy_init": True}
    )
    menus = env["ir.ui.menu"].search([])
    menus.write({"groups_id": [(5,)]})
    views = env["ir.ui.view"].search([])
    views.write({"groups_id": [(5,)]})
    for act_model in [
        "ir.actions.act_window",
        "ir.actions.server",
        "ir.actions.report",
    ]:
        actions = env[act_model].search([])
        actions.write({"groups_id": [(5,)]})
    users = env["res.users"].search([("share", "=", False)])
    users -= env.ref("base.user_admin")
    users -= env.ref("base.user_root")
    for user in users:
        toremove = user.groups_id.filtered(lambda r: r != r.env.ref("base.group_user"))
        user.groups_id = [(3, x.id) for x in toremove]
