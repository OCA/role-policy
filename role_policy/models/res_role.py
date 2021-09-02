# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ResRole(models.Model):
    _name = "res.role"
    _description = "Role"
    _inherit = ["mail.thread"]
    _sql_constraints = [
        ("code_company_uniq", "unique (code, company_id)", "The code must be unique !")
    ]

    name = fields.Char(required=True)
    code = fields.Char(required=True, size=5)
    group_id = fields.Many2one(
        comodel_name="res.groups", readonly=True, ondelete="restrict"
    )
    acl_ids = fields.One2many(
        comodel_name="res.role.acl", inverse_name="role_id", string="ACL Items"
    )
    modifier_rule_ids = fields.One2many(
        comodel_name="view.modifier.rule",
        inverse_name="role_id",
        string="View Modifier Rules",
    )
    model_operation_ids = fields.One2many(
        comodel_name="view.model.operation",
        inverse_name="role_id",
        string="View Model Operation",
    )
    view_type_attribute_ids = fields.One2many(
        comodel_name="view.type.attribute",
        inverse_name="role_id",
        string="View Type Attributes",
    )
    menu_ids = fields.Many2many(
        comodel_name="ir.ui.menu",
        relation="res_role_menu_rel",
        column1="role_id",
        column2="menu_id",
        string="Menu Items",
    )
    act_window_ids = fields.Many2many(
        comodel_name="ir.actions.act_window",
        relation="res_role_act_window_rel",
        column1="role_id",
        column2="act_window_id",
        string="Window Actions",
    )
    act_client_ids = fields.Many2many(
        comodel_name="ir.actions.client",
        relation="res_role_client_rel",
        column1="role_id",
        column2="act_client_id",
        string="Client Actions",
    )
    act_server_ids = fields.Many2many(
        comodel_name="ir.actions.server",
        relation="res_role_act_server_rel",
        column1="role_id",
        column2="act_server_id",
        string="Server Actions",
    )
    act_report_ids = fields.Many2many(
        comodel_name="ir.actions.report",
        relation="res_role_act_report_rel",
        column1="role_id",
        column2="act_report_id",
        string="Report Actions",
    )
    user_ids = fields.Many2many(
        comodel_name="res.users",
        relation="res_role_users_rel",
        column1="role_id",
        column2="uid",
        string="Users",
    )
    model_method_ids = fields.One2many(
        comodel_name="model.method.execution.right",
        inverse_name="role_id",
        string="Method Execution Rights",
    )
    sequence = fields.Integer()
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self._default_company_id(),
    )

    @api.model
    def _default_company_id(self):
        return self.env.user.company_id

    def init(self):
        """
        Role groups that have been added to e.g. ir.ui.menu will
        be removed during 'upgrade all' processing. This happens
        only for those records that have the groups_id set in the
        base module (e.g. Settings menu).
        We cannot prevent this since the addons path modules are not yet
        imported when the xml files of the base module are loaded.
        As a consequence we use the init method to restore the role groups.
        """
        super().init()
        if self.env.context.get("module") == "role_policy":
            self._init_restore_role_groups()

    def _init_restore_role_groups(self):
        roles = self.with_context(
            dict(self.env.context, role_policy_init=True, active_test=False)
        ).search([])
        for role in roles:
            for f in ["menu_ids", "act_window_ids", "act_server_ids", "act_report_ids"]:
                torestore = [
                    x for x in getattr(role, f) if role.group_id not in x.groups_id
                ]
                for rec in torestore:
                    rec.update({"groups_id": [(4, role.group_id.id)]})

    @api.model
    def create(self, vals):
        self = self.with_context(dict(self.env.context, role_policy_init=True))
        role_group = self._create_role_group(vals)
        vals["group_id"] = role_group.id
        role = super().create(vals)
        for f in ["menu_ids", "act_window_ids", "act_server_ids", "act_report_ids"]:
            if f in vals and vals[f][0][2]:
                getattr(role, f).write({"groups_id": [(4, role_group.id)]})
        return role

    def _create_role_group(self, vals):
        categ = self.env.ref("role_policy.ir_module_category_role")
        group_vals = {
            "role": True,
            "name": vals["code"],
            "category_id": categ.id,
            "users": vals.get("user_ids"),
        }
        return self.env["res.groups"].create(group_vals)

    def write(self, vals):
        self = self.with_context(dict(self.env.context, role_policy_init=True))
        for role in self:
            if vals.get("code"):
                if role.code != vals["code"] and role.acl_ids:
                    raise UserError(_("You are not allowed to update the code."))
            if "user_ids" in vals:
                self._update_role_groups(role, vals)
            updates = []
            role_gid = role.group_id.id
            for f in ["menu_ids", "act_window_ids", "act_server_ids", "act_report_ids"]:
                if f in vals:
                    model = self._fields[f].comodel_name
                    for entry in vals[f]:
                        if entry[0] == 6:
                            # Addition or removal in M2M result in update of all
                            # items. We only need the differences.
                            model_ids = getattr(role, f).ids
                            old_model_ids = set(model_ids)
                            new_model_ids = set(entry[2])
                            removal_ids = old_model_ids - new_model_ids
                            addition_ids = new_model_ids - old_model_ids
                            if removal_ids:
                                updates.append((model, removal_ids, [(3, role_gid)]))
                            if addition_ids:
                                updates.append((model, addition_ids, [(4, role_gid)]))
                        elif entry[0] in (3, 4):
                            updates.append((model, [entry[1]], [(entry[0], role_gid)]))
                        else:
                            raise NotImplementedError
        res = super().write(vals)
        for model, model_ids, command in updates:
            rs = self.env[model].browse(model_ids)
            rs.write({"groups_id": command})
        return res

    def _update_role_groups(self, role, vals):
        role.group_id.write({"users": vals["user_ids"]})
        # remove user from role_acl groups
        for entry in vals["user_ids"]:
            if entry[0] == 6:
                removals = role.user_ids.filtered(lambda r: r.id not in entry[2])
                for user in removals:
                    extra_roles = user.role_ids - role
                    extra_roles_acl_groups = extra_roles.mapped("group_id.implied_ids")
                    for role_acl_group in role.group_id.implied_ids:
                        if role_acl_group in extra_roles_acl_groups:
                            continue
                        role_acl_group.users -= user
            else:
                # TODO
                raise NotImplementedError

    def unlink(self):
        role_groups = self.mapped("group_id")
        res = super().unlink()
        role_groups.unlink()
        return res

    def export_xls(self):
        report_file = "role_policy_{}_{}".format(
            self.code, fields.Date.to_string(fields.Date.today())
        )
        report_name = "role_policy.export_xls"
        report = {
            "name": _("Role Policy Export"),
            "type": "ir.actions.report",
            "report_type": "xlsx",
            "report_name": report_name,
            "report_file": report_name,
            "context": dict(self.env.context, report_file=report_file),
            "data": {"dynamic_report": True},
        }
        return report

    def import_policy(self):
        self.ensure_one()
        view = self.env.ref("role_policy.role_policy_import_view_form")
        return {
            "name": _("Role Policy Import"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "role.policy.import",
            "view_id": view.id,
            "context": dict(self.env.context, active_id=self.id),
            "target": "new",
            "type": "ir.actions.act_window",
        }
