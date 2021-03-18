# Copyright 2020-2021 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import api, fields, models
from odoo.tools import config

from odoo.addons.base.models.res_users import Users as ResUsersBase

from .helpers import diff_to_odoo_x2many_commands, play_odoo_x2x_commands_on_ids


class ResUsers(models.Model):
    _inherit = "res.users"

    role_ids = fields.Many2many(
        comodel_name="res.role",
        relation="res_role_users_rel",
        column1="uid",
        column2="role_id",
        string="Roles",
    )
    enabled_role_ids = fields.Many2many(
        comodel_name="res.role",
        relation="res_role_users_enabled_rel",
        column1="uid",
        column2="role_id",
        domain="[('id', 'in', role_ids)]",
        string="Enabled Roles",
        help="If you have multiple roles you may experience loss of functionality.\n"
        "E.g. Role 2 may hide a button which you need to do your job in Role 1.\n"
        "You can enable here a subset of your roles.\n"
        "Leave this field blank to enable all your roles.",
    )
    exclude_from_role_policy = fields.Boolean(
        compute="_compute_exclude_from_role_policy", store=True
    )

    def __init__(self, pool, cr):
        """ Override of __init__ to add access rights.
        Access rights are disabled by default, but allowed on some specific
        fields defined in self.SELF_{READ/WRITE}ABLE_FIELDS.
        """
        super().__init__(pool, cr)
        # duplicate list to avoid modifying the original reference
        type(self).SELF_WRITEABLE_FIELDS = list(self.SELF_WRITEABLE_FIELDS)
        type(self).SELF_WRITEABLE_FIELDS.extend(["enabled_role_ids"])

    def _compute_exclude_from_role_policy(self):
        for user in self:
            if user in (
                self.env.ref("base.user_admin"),
                self.env.ref("base.user_root"),
            ):
                user.exclude_from_role_policy = True
            else:
                user.exclude_from_role_policy = False

    @api.onchange("role_ids")
    def _onchange_role_ids(self):
        enabled_roles = self.enabled_role_ids.filtered(lambda r: r in self.role_ids)
        if enabled_roles != self.enabled_role_ids:
            self.enabled_role_ids = enabled_roles

    @api.model_create_multi
    def create(self, vals_list):
        """
        Remove no role groups.
        """
        if config.get("test_enable"):
            return super().create(vals_list)

        keep_ids = self._get_role_policy_group_keep_ids()
        for i, vals in enumerate(vals_list):
            vals = self._remove_reified_groups(vals)
            gids = []
            role_gids = []
            if "groups_id" in vals:
                for entry in vals["groups_id"]:
                    if entry[0] == 4 and entry[1] in keep_ids:
                        gids.append(entry[1])
                    if entry[0] == 6:
                        gids.extend([x for x in entry[2] if x in keep_ids])
                if gids:
                    vals["groups_id"] = [(6, 0, gids)]
            if "role_ids" in vals:
                for entry in vals["role_ids"]:
                    if entry[0] == 6:
                        roles = self.env["res.role"].browse(entry[2])
                        role_gids += [x.id for x in roles.mapped("group_id")]
                    else:
                        raise NotImplementedError
                vals["groups_id"] = [(6, 0, role_gids + gids)]
            vals_list[i] = vals
        users = super().create(vals_list)
        users._role_policy_remove_no_role_groups()
        return users

    def write(self, vals):
        if self.env.context.get("role_policy_bypass_write"):
            return super(ResUsersBase, self).write(vals)

        if config.get("test_enable"):
            return super().write(vals)

        if "enabled_role_ids" in vals:
            self.clear_caches()
        vals = self._remove_reified_groups(vals)
        if not any([x in vals for x in ("groups_id", "role_ids", "enabled_role_ids")]):
            return super().write(vals)

        for user in (self.env.ref("base.user_admin"), self.env.ref("base.user_root")):
            if user in self:
                super(ResUsers, user).write(vals)
                self -= user
        if not self:
            return True

        for user in self:
            user._role_policy_write(vals)
        self._role_policy_remove_no_role_groups()

        return True

    @api.model
    def _has_group(self, group_ext_id):
        if not self.env.context.get("role_policy_has_groups_ok") or config.get(
            "test_enable"
        ):
            return super()._has_group(group_ext_id)
        else:
            return True

    @api.model
    def fields_view_get(
        self, view_id=None, view_type=False, toolbar=False, submenu=False
    ):
        res = super().fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        if view_type == "form" and view_id == self.env.ref("base.view_users_form").id:
            role_categ = self.env.ref("role_policy.ir_module_category_role")
            view = etree.XML(res["arch"])
            expr = "//page[@name='access_rights']//separator[@string='{}']".format(
                role_categ.name
            )
            role_node = view.xpath(expr)
            if role_node:
                group_el = role_node[0].getparent()
                remove = False
                for el in group_el:
                    if el.tag == "separator":
                        if (
                            "string" in el.attrib
                            and el.attrib["string"] == role_categ.name
                        ):
                            remove = True
                        else:
                            break
                    if remove:
                        group_el.remove(el)
                res["arch"] = etree.tostring(view, encoding="unicode")
        return res

    def _get_role_policy_group_keep_ids(self):
        group_user = self.env.ref("base.group_user")
        keep_ids = [
            self.env.ref(x).id for x in self._role_policy_untouchable_groups()
        ] + [group_user.id]
        return keep_ids

    def _role_policy_remove_no_role_groups(self):
        keep_ids = self._get_role_policy_group_keep_ids()
        ctx = dict(self.env.context, role_policy_bypass_write=True)
        for user in self.with_context(ctx):
            if user.exclude_from_role_policy:
                continue
            groups = user.groups_id
            to_remove = groups.filtered(lambda r: r.id not in keep_ids and not r.role)
            if to_remove:
                super(ResUsersBase, user).write(
                    {"groups_id": [(3, x) for x in to_remove.ids]}
                )

    def _role_policy_write(self, vals):
        """
        remove no role groups
        remove role ACL groups when removing/disabling roles
        """
        self.ensure_one()
        keep_gids = self._get_role_policy_group_keep_ids()

        # remove no role groups
        target_gids = set(self.groups_id.ids)
        if "groups_id" in vals:
            target_gids = play_odoo_x2x_commands_on_ids(target_gids, vals["groups_id"])
            del vals["groups_id"]
        target_gids = {x for x in target_gids if x in keep_gids}

        # remove role ACL groups when removing/disabling roles
        target_rids = set()
        if vals.get("enabled_role_ids"):
            target_rids = play_odoo_x2x_commands_on_ids(
                target_rids, vals["enabled_role_ids"]
            )
        if not target_rids:
            if vals.get("role_ids"):
                target_rids = play_odoo_x2x_commands_on_ids(
                    target_rids, vals["role_ids"]
                )
            else:
                target_rids = set(self.role_ids.ids)
        if target_rids:
            enabled_roles = self.env["res.role"].browse(target_rids)
            enabled_role_groups = enabled_roles.mapped("group_id")
            enabled_role_groups |= enabled_role_groups.mapped("implied_ids")
            target_gids |= set(enabled_role_groups.ids)

        groups_updates = diff_to_odoo_x2many_commands(self.groups_id.ids, target_gids)

        super().write(vals)

        if groups_updates:
            super(ResUsersBase, self.sudo()).write({"groups_id": groups_updates})
        if "role_ids" in vals:
            ctx = dict(self.env.context, role_policy_bypass_write=True)
            self.with_context(ctx)._onchange_role_ids()
