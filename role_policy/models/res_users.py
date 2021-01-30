# Copyright 2020-2021 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import api, fields, models
from odoo.tools import config


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
        ctx = dict(self.env.context, role_policy_bypass_write=True)
        for user in users.with_context(ctx):
            if user.exclude_from_role_policy:
                continue
            groups = user.groups_id
            to_remove = groups.filtered(lambda r: r.id not in keep_ids and not r.role)
            if to_remove:
                user.groups_id -= to_remove
        return users

    def write(self, vals):
        """
        Remove no role groups.
        """
        if self.env.context.get("role_policy_bypass_write") or config.get(
            "test_enable"
        ):
            return super().write(vals)

        if "enabled_role_ids" in vals:
            self.clear_caches()
        if "enabled_role_ids" not in self.SELF_WRITEABLE_FIELDS:
            self.SELF_WRITEABLE_FIELDS.append("enabled_role_ids")
        vals = self._remove_reified_groups(vals)
        if not ("groups_id" in vals or "role_ids" in vals):
            return super().write(vals)

        for user in (self.env.ref("base.user_admin"), self.env.ref("base.user_root")):
            if user in self:
                super(ResUsers, user).write(vals)
                self -= user
        if not self:
            return True

        keep_ids = self._get_role_policy_group_keep_ids()
        removal_gids = []
        addition_gids = []
        if "groups_id" in vals:
            for entry in vals["groups_id"]:
                if entry[0] == 3:
                    removal_gids.append(entry[1])
                elif entry[0] == 4:
                    if entry[1] in keep_ids:
                        addition_gids.append(entry[1])
                elif entry[0] == 5:
                    removal_gids.extend(user.groups_id.ids)
                elif entry[0] == 6:
                    addition_gids.extend([x for x in entry[2] if x in keep_ids])
                else:  # 0, 1, 2
                    raise NotImplementedError
            del vals["groups_id"]

        for user in self:
            self._role_policy_write(user, vals, removal_gids, addition_gids)
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
                group_el.getparent().remove(group_el)
                res["arch"] = etree.tostring(view, encoding="unicode")
        return res

    def _get_role_policy_group_keep_ids(self):
        group_user = self.env.ref("base.group_user")
        keep_ids = [
            self.env.ref(x).id for x in self._role_policy_untouchable_groups()
        ] + [group_user.id]
        return keep_ids

    def _role_policy_write(self, user, vals, removal_gids, addition_gids):
        min_gids = removal_gids[:]
        plus_gids = addition_gids[:]
        for entry in vals.get("role_ids", []):
            if entry[0] == 3:
                role = user.role_ids.filtered(lambda r: r.id == entry[1])
                min_gids.append(role.group_id.id)
            elif entry[0] == 4:
                role = self.env["res.role"].browse(entry[1])
                plus_gids.append(role.group_id.id)
            elif entry[0] == 5:
                min_gids.extend(user.role_ids.mapped("group_id").ids)
            elif entry[0] == 6:
                roles = self.env["res.role"].browse(entry[2])
                plus_gids.extend(roles.mapped("group_id").ids)
            else:  # 0, 1, 2
                raise NotImplementedError
        min_gids = set(min_gids)
        plus_gids = set(plus_gids)
        old_gids = user.groups_id.ids
        removal_ids = [x for x in min_gids if x in old_gids]
        addition_ids = [x for x in plus_gids if x not in old_gids]
        updates = []
        for x in removal_ids:
            updates.append((3, x))
        for x in addition_ids:
            updates.append((4, x))
        user_vals = vals.copy()
        if updates:
            user_vals["groups_id"] = updates
        super(ResUsers, user).write(user_vals)
        if "role_ids" in vals:
            ctx = dict(self.env.context, role_policy_bypass_write=True)
            user.with_context(ctx)._onchange_role_ids()
