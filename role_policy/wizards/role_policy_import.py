# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
import os
import time

import xlrd

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class RolePolicyImport(models.TransientModel):
    _name = "role.policy.import"
    _description = "Import Role Policy"

    policy_data = fields.Binary(string="File", required=True)
    policy_fname = fields.Char(string="Filename")
    file_type = fields.Selection(
        selection="_selection_file_type", default=lambda self: self._default_file_type()
    )
    codepage = fields.Char(
        string="Code Page",
        default=lambda self: self._default_codepage(),
        help="Code Page of the system that has generated the file.",
    )
    sheet = fields.Selection(
        selection="_selection_sheet",
        help="Specify the Excel sheet."
        "\nIf not specified all sheets will be imported.",
    )
    warning = fields.Text(readonly=True)
    note = fields.Text("Log")

    @api.model
    def _selection_file_type(self):
        return [("xls", "xls"), ("xlsx", "xlsx")]

    @api.model
    def _default_file_type(self):
        return "xlsx"

    @api.model
    def _selection_sheet(self):
        return [
            ("acl", "Role ACLs"),
            ("menu", "Menu Items"),
            ("act_window", "Window Actions"),
            ("act_client", "Client Actions"),
            ("act_server", "Server Actions"),
            ("act_report", "Report Actions"),
            ("modifier_rule", "View Modifier Rules"),
            ("view_type_attribute", "View Type Attributes"),
            ("model_operation", "View Model Operations"),
            ("model_method", "Model Methods"),
            # ('record_rule', 'Record Rules'),
        ]

    @api.model
    def _default_codepage(self):
        return "utf-16le"

    @api.onchange("policy_fname")
    def _onchange_policy_fname(self):
        if not self.policy_fname:
            return
        name, ext = os.path.splitext(self.policy_fname)
        ext = ext[1:]
        if ext not in ["xls", "xlsx"]:
            self.warning = _(
                "<b>Incorrect file format !</b>"
                "<br>Only files of type csv and xls(x) are supported."
            )
            return
        else:
            self.file_type = ext
            self.warning = False

    @api.onchange("sheet")
    def _onchange_sheet(self):
        self.warning = False

    def role_policy_import(self):
        time_start = time.time()
        role = self.env["res.role"].browse(self.env.context["active_id"])
        data = base64.decodestring(self.policy_data)
        if self.file_type in ["xls", "xlsx"]:
            err_log = self._read_xls(data, role)
        else:
            raise NotImplementedError
        if self.warning:
            view = self.env.ref("role_policy.role_policy_import_view_form")
            return {
                "name": _("Import File"),
                "res_id": self.id,
                "view_type": "form",
                "view_mode": "form",
                "res_model": "role.policy.import",
                "view_id": view.id,
                "target": "new",
                "type": "ir.actions.act_window",
                "context": self.env.context,
            }

        if err_log:
            self.note = err_log
            result_view = self.env.ref(
                "role_policy.role_policy_import_view_form_result"
            )
            return {
                "name": _("Role Policy Import result"),
                "res_id": self.id,
                "view_type": "form",
                "view_mode": "form",
                "res_model": "role.policy.import",
                "view_id": result_view.id,
                "target": "new",
                "type": "ir.actions.act_window",
            }
        else:
            import_time = time.time() - time_start
            _logger.warn("Role %s import time = %.3f seconds", role.name, import_time)
            return {"type": "ir.actions.act_window_close"}

    def _read_xls(self, data, role):
        all_sheets = [x[0] for x in self._selection_sheet()]
        if self.sheet:
            sheets = [self.sheet]
            start = all_sheets.index(self.sheet)
        else:
            sheets = all_sheets
            start = 0
        err_log = ""
        wb = xlrd.open_workbook(file_contents=data)
        for i, sheet_name in enumerate(sheets, start=start):
            sheet = wb.sheet_by_index(i)
            sheet_err_log = getattr(self, "_read_{}".format(sheet_name))(sheet, role)
            if sheet_err_log:
                if err_log:
                    err_log += "\n\n"
                err_log += _("Errors detected while importing sheet '%s'.") % sheet.name
                err_log += "\n\n" + sheet_err_log
        return err_log

    def _read_acl(self, sheet, role):
        header = ["Name", "Model", "Read", "Write", "Create", "Delete", "Active"]
        headerline = sheet.row_values(0)
        err_log, unlink_pos, unlink_column = self._check_sheet_header(
            sheet, header, headerline
        )
        if err_log:
            return err_log

        unique_entries = []
        to_unlink = self.env["res.role.acl"]
        to_create = []

        for ri in range(1, sheet.nrows):
            ln = sheet.row_values(ri)
            if self._empty_line(ln):
                continue
            line_errors = []
            model_name = ln[1].strip()
            model_id = self.env["ir.model"]._get_id(model_name)
            if not model_id:
                line_errors.append(_("Model '%s' does not exist.") % model_name)
                err_log = (err_log and err_log + "\n\n") + self._format_line_errors(
                    ln, line_errors
                )
                continue
            if model_id in unique_entries:
                line_errors.append(_("Duplicate entry.") % ln)
            else:
                unique_entries.append(model_id)
            line_action = False
            vals = {"role_id": role.id, "model_id": model_id}
            role_acl = role.acl_ids.filtered(lambda r: r.model_id.model == model_name)
            if unlink_column and self._check_unlink(
                role_acl, ln[unlink_pos], line_errors
            ):
                to_unlink += role_acl
                line_action = "delete"
            elif not role_acl:
                line_action = "create"

            for ci, fld in enumerate(
                [
                    ("perm_read", "Read"),
                    ("perm_write", "Write"),
                    ("perm_create", "Create"),
                    ("perm_unlink", "Delete"),
                    ("active", "Active"),
                ],
                start=2,
            ):
                fld = fld[0]
                column_name = fld[1]
                val = self._read_cell_bool(sheet.cell(ri, ci), column_name, line_errors)
                vals[fld] = val
                if (
                    line_action not in ["create", "delete"]
                    and getattr(role_acl, fld) != val
                ):
                    line_action = "write"
            if line_action == "write":
                to_unlink += role_acl
            if line_action in ["create", "write"] and vals not in to_create:
                to_create.append(vals)

            if line_errors:
                err_log = (err_log and err_log + "\n\n") + self._format_line_errors(
                    ln, line_errors
                )

        if not err_log:
            to_unlink.unlink()
            self.env["res.role.acl"].create(to_create)
        return err_log

    def _read_menu(self, sheet, role):
        header = ["Menu", "External Identifier"]
        return self._read_m2m_sheet(sheet, role, header)

    def _read_act_window(self, sheet, role):
        header = ["Window Action", "External Identifier"]
        return self._read_m2m_sheet(sheet, role, header)

    def _read_act_client(self, sheet, role):
        header = ["Client Action", "External Identifier"]
        return self._read_m2m_sheet(sheet, role, header)

    def _read_act_server(self, sheet, role):
        header = ["Server Action", "External Identifier"]
        return self._read_m2m_sheet(sheet, role, header)

    def _read_act_report(self, sheet, role):
        header = ["Report Action", "External Identifier"]
        return self._read_m2m_sheet(sheet, role, header)

    def _read_m2m_sheet(self, sheet, role, header):
        headerline = sheet.row_values(0)
        err_log, unlink_pos, unlink_column = self._check_sheet_header(
            sheet, header, headerline
        )
        if err_log:
            return err_log
        fld = sheet.name.split(" ")[0].lower()
        if fld == "menu":
            fld = fld + "_ids"
        else:
            fld = "act_" + fld + "_ids"
        rules = getattr(role, fld)

        unique_entries = []
        to_remove_ids = []
        to_add_ids = []

        for ri in range(1, sheet.nrows):
            ln = sheet.row_values(ri)
            if self._empty_line(ln):
                continue
            line_errors = []
            fld_id = self._read_xml_id(ln[1], line_errors)
            rule = rules.filtered(lambda r: r.id == fld_id)
            if unlink_column and self._check_unlink(rule, ln[unlink_pos], line_errors):
                to_remove_ids.append(fld_id)
            if fld_id not in rules.ids:
                to_add_ids.append(fld_id)
            if fld_id in unique_entries:
                line_errors.append(_("Duplicate entry.") % ln)
            else:
                unique_entries.append(fld_id)
            if line_errors:
                if err_log:
                    err_log += "\n\n"
                err_log += self._format_line_errors(ln, line_errors)

        if not err_log:
            updates = [(3, x) for x in to_remove_ids] + [(4, x) for x in to_add_ids]
            if updates:
                setattr(role, fld, updates)

        return err_log

    def _read_modifier_rule(self, sheet, role):
        fields_dict = {
            "Model": {"field": "model_id", "match": True, "method": "_read_cell_model"},
            "Prio": {"field": "priority", "method": "_read_cell_int", "required": True},
            "View": {"field": False},
            "View External Identifier": {
                "field": "view_id",
                "match": True,
                "method": "_read_cell_view",
            },
            "View Type": {
                "field": "view_type",
                "match": True,
                "method": "_read_cell_char",
            },
            "Element": {
                "field": "element_ui",
                "match": True,
                "method": "_read_cell_char",
            },
            "Remove": {"field": "remove", "method": "_read_cell_bool"},
            "Invisible": {
                "field": "modifier_invisible",
                "method": "_read_cell_modifier",
            },
            "Readonly": {"field": "modifier_readonly", "method": "_read_cell_modifier"},
            "Required": {"field": "modifier_required", "method": "_read_cell_modifier"},
            "Active": {"field": "active", "method": "_read_cell_bool"},
            "Sequence": {
                "field": "sequence",
                "method": "_read_cell_int",
                "required": True,
            },
        }
        return self._read_rule_sheet(sheet, role, "modifier_rule_ids", fields_dict)

    def _check_modifier_rule_vals(self, vals, line_errors):
        if not vals.get("model_id") and vals.get("view_type") != "qweb":
            line_errors.append(_("Model definition error."))

    def _read_view_type_attribute(self, sheet, role):
        fields_dict = {
            "Prio": {"field": "priority", "method": "_read_cell_int", "required": True},
            "View": {"field": False},
            "View External Identifier": {
                "field": "view_id",
                "match": True,
                "method": "_read_cell_view",
                "required": True,
            },
            "View Type": {"field": False},
            "Attribute": {
                "field": "attrib",
                "match": True,
                "method": "_read_cell_char",
                "required": True,
            },
            "Attribute Value": {
                "field": "attrib_val",
                "method": "_read_cell_char",
                "required": True,
            },
            "Active": {"field": "active", "method": "_read_cell_bool"},
            "Sequence": {
                "field": "sequence",
                "method": "_read_cell_int",
                "required": True,
            },
        }
        return self._read_rule_sheet(
            sheet, role, "view_type_attribute_ids", fields_dict
        )

    def _check_view_type_attribute_vals(self, vals, line_errors):
        """ placeholder for exra checks """
        pass

    def _read_model_operation(self, sheet, role):
        fields_dict = {
            "Model": {
                "field": "model",
                "match": True,
                "method": "_read_cell_char",
                "required": True,
            },
            "Prio": {"field": "priority", "method": "_read_cell_int", "required": True},
            "Operation": {
                "field": "operation",
                "match": True,
                "method": "_read_cell_char",
                "required": True,
            },
            "Disable": {"field": "disable", "method": "_read_cell_bool"},
            "Active": {"field": "active", "method": "_read_cell_bool"},
        }
        return self._read_rule_sheet(sheet, role, "model_operation_ids", fields_dict)

    def _check_model_operation_vals(self, vals, line_errors):
        """ placeholder for exra checks """
        pass

    def _read_model_method(self, sheet, role):
        fields_dict = {
            "Model,Method": {
                "field": "name",
                "match": True,
                "method": "_read_cell_char",
                "required": True,
            },
            "Active": {"field": "active", "method": "_read_cell_bool"},
        }
        return self._read_rule_sheet(sheet, role, "model_method_ids", fields_dict)

    def _check_model_method_vals(self, vals, line_errors):
        """ placeholder for exra checks """
        pass

    def _read_rule_sheet(self, sheet, role, role_field, fields_dict):

        header = [f for f in fields_dict]
        match_fields = [
            fields_dict[f]["field"] for f in fields_dict if fields_dict[f].get("match")
        ]
        headerline = sheet.row_values(0)
        err_log, unlink_pos, unlink_column = self._check_sheet_header(
            sheet, header, headerline
        )
        rule_model = getattr(role, role_field)._name
        if err_log:
            return err_log

        unique_entries = []
        to_unlink = self.env[rule_model]
        to_create = []
        to_update = []

        for ri in range(1, sheet.nrows):
            ln = sheet.row_values(ri)
            if self._empty_line(ln):
                continue
            vals = {"role_id": role.id}
            line_errors = []

            for ci, header_fld in enumerate(header):
                fld = fields_dict[header_fld].get("field")
                if not fld:
                    continue
                if fields_dict[header_fld].get("required") and not ln[ci]:
                    line_errors.append(_("Missing value for field '%s'.") % header_fld)
                    continue
                method = fields_dict[header_fld]["method"]
                vals[fld] = getattr(self, method)(
                    sheet.cell(ri, ci), header_fld, line_errors
                )

            check_vals_method = "_check_{}_vals".format(role_field[:-4])
            getattr(self, check_vals_method)(vals, line_errors)
            match_key = "-".join([str(vals[f]) for f in match_fields])
            if match_key in unique_entries:
                line_errors.append(_("Duplicate entry.") % ln)
            else:
                unique_entries.append(match_key)
            if line_errors:
                err_log = (err_log and err_log + "\n\n") + self._format_line_errors(
                    ln, line_errors
                )
                continue

            def rule_filter(rule):
                rule_key_fields = []
                for f in match_fields:
                    val = getattr(rule, f)
                    if hasattr(val, "id"):
                        val = val.id
                    rule_key_fields.append(str(val))
                rule_key = "-".join(rule_key_fields)
                return rule_key == match_key

            rule = getattr(role, role_field).filtered(rule_filter)

            if unlink_column and self._check_unlink(rule, ln[unlink_pos], line_errors):
                to_unlink += rule
            elif rule:
                upd_vals = {k: v for k, v in vals.items() if k not in match_fields}
                to_update.append((rule, upd_vals))
            else:
                to_create.append(vals)

        if not err_log:
            to_unlink.unlink()
            self.env[rule_model].create(to_create)
            for rule, vals in to_update:
                rule.update(vals)

        return err_log

    def _check_sheet_header(self, sheet, header, headerline):
        err_log = ""
        unlink_pos = len(header)
        if headerline[:unlink_pos] != header:
            err_log = _(
                "Error while reading sheet '%s':\n"
                "Incorrect sheet header.\n"
                "The first line of your sheet should contain the "
                "following field names: %s"
            ) % (sheet.name, header)
        unlink_column = (
            len(headerline) > unlink_pos and headerline[unlink_pos] == "Delete Entry"
        )
        return err_log, unlink_pos, unlink_column

    def _empty_line(self, ln):
        return (
            not ln
            or (ln[0] and isinstance(ln[0], str) and ln[0][0] == "#")
            or not any(ln)
        )

    def _check_unlink(self, rule, unlink_flag, line_errors):
        if unlink_flag not in ["X", "x", ""]:
            line_errors.append(
                _(
                    "Incorrect value '%s' for field 'Delete Entry'. "
                    "The value should be 'X' or empty."
                )
                % unlink_flag
            )
            return False

        if unlink_flag and not rule:
            line_errors.append(
                _(
                    "Incorrect value '%s' for field 'Delete Entry'. "
                    "You cannot remove a %s which doesn't exist."
                )
                % (unlink_flag, rule._name)
            )
            return False

        return unlink_flag and True or False

    def _read_cell_model(self, cell, column_name, line_errors):
        val = cell.value
        if not val:
            return False
        if cell.ctype == xlrd.XL_CELL_TEXT:
            model_name = self.env["ir.model"]._get_id(val.strip()) or False
        else:
            line_errors.append(
                _("Incorrect value '%s' for field '%s'. ") % (val, column_name)
            )
            model_name = False
        return model_name

    def _read_cell_view(self, cell, column_name, line_errors):
        val = cell.value
        if not val:
            return False
        if cell.ctype == xlrd.XL_CELL_TEXT:
            view_xml_id = val.strip()
            view_id = (
                view_xml_id and self._read_xml_id(view_xml_id, line_errors) or False
            )
        else:
            line_errors.append(
                _("Incorrect value '%s' for field '%s'. ") % (val, column_name)
            )
            view_id = False
        return view_id

    def _read_cell_modifier(self, cell, column_name, line_errors):
        val = cell.value
        if cell.ctype == xlrd.XL_CELL_TEXT:
            val = cell.value.strip()
        elif cell.ctype == xlrd.XL_CELL_NUMBER:
            is_int = cell.value % 1 == 0.0
            if is_int:
                val = str(int(cell.value))
            else:
                val = str(cell.value).strip()
        else:
            val = str(val)
        return val or False

    def _read_cell_char(self, cell, column_name, line_errors):
        val = cell.value
        if not val:
            return False
        try:
            val = str(val)
        except Exception:
            val = False
            line_errors.append(
                _("Incorrect value '%s' for field '%s'. ") % (val, column_name)
            )
        return val

    def _read_cell_bool(self, cell, column_name, line_errors):
        val = cell.value
        if not val:
            return False
        if cell.ctype == xlrd.XL_CELL_TEXT:
            val = val.strip()
        elif cell.ctype == xlrd.XL_CELL_NUMBER:
            is_int = cell.value % 1 == 0.0
            if is_int:
                val = str(int(cell.value))
            else:
                val = str(cell.value)
        if val not in ["0", "1"]:
            line_errors.append(
                _(
                    "Incorrect value '%s' for field '%s'. "
                    "The value should be '0' or '1' or empty."
                )
                % (val, column_name)
            )
        return val == "1" and True or False

    def _read_cell_int(self, cell, column_name, line_errors):
        val = cell.value
        if not val:
            return False
        err_msg = _(
            "Incorrect value '%s' for field '%s'. The value should be an Integer."
        ) % (val, column_name)
        if cell.ctype == xlrd.XL_CELL_TEXT:
            try:
                val = int(val)
            except Exception:
                val = False
                line_errors.append(err_msg)
        elif cell.ctype == xlrd.XL_CELL_NUMBER:
            is_int = cell.value % 1 == 0.0
            if is_int:
                val = str(int(cell.value))
            else:
                val = False
                line_errors.append(err_msg)
        return val

    def _read_xml_id(self, val, line_errors):
        rec = self.env.ref(val, raise_if_not_found=False)
        if not rec:
            line_errors.append(_("Incorrect value for field 'External Identifier'."))
        return rec and rec.id or False

    def _format_line_errors(self, ln, line_errors):
        err_log = _("Error while processing line %s:\n") % ln
        err_log += "\n".join(line_errors)
        return err_log
