# Copyright 2020 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class RolePolicyExportXls(models.AbstractModel):
    _name = "report.role_policy.export_xls"
    _inherit = "report.report_xlsx.abstract"
    _description = "Role Policy XLSX Export"

    def _get_ws_params(self, wb, data, role):
        ws_params = []
        for entry in [
            "acl",
            "menu",
            "act_window",
            "act_server",
            "act_report",
            "modifier_rule",
            "view_type_attribute",
            "model_operation",
            "model_method",
        ]:
            method = getattr(self, "_get_ws_params_{}".format(entry))
            method_params = method(data, role)
            method_params["wanted_list"].append("unlink")
            method_params["col_specs"].update(
                {
                    "unlink": {
                        "header": {"value": "Delete Entry"},
                        "data": {"value": ""},
                        "width": 12,
                    }
                }
            )
            ws_params.append(method_params)
        return ws_params

    def _get_ws_params_acl(self, data, role):

        acl_template = {
            "name": {
                "header": {"value": "Name"},
                "data": {"value": self._render("role_acl.name")},
                "width": 50,
            },
            "model": {
                "header": {"value": "Model"},
                "data": {"value": self._render("role_acl.model_id.model")},
                "width": 20,
            },
            "perm_read": {
                "header": {"value": "Read"},
                "data": {"value": self._render("role_acl.perm_read and 1 or 0")},
                "width": 6,
            },
            "perm_write": {
                "header": {"value": "Write"},
                "data": {"value": self._render("role_acl.perm_write and 1 or 0")},
                "width": 6,
            },
            "perm_create": {
                "header": {"value": "Create"},
                "data": {"value": self._render("role_acl.perm_create and 1 or 0")},
                "width": 6,
            },
            "perm_unlink": {
                "header": {"value": "Delete"},
                "data": {"value": self._render("role_acl.perm_unlink and 1 or 0")},
                "width": 6,
            },
            "active": {
                "header": {"value": "Active"},
                "data": {"value": self._render("role_acl.active and 1 or 0")},
                "width": 6,
            },
        }
        params = {
            "ws_name": "Role ACLs",
            "generate_ws_method": "_export_acl",
            "title": "Role ACLs",
            "wanted_list": [k for k in acl_template],
            "col_specs": acl_template,
        }
        return params

    def _export_acl(self, workbook, ws, ws_params, data, role):

        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers["standard"])
        ws.set_footer(self.xls_footers["standard"])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=self.format_theader_yellow_left,
        )
        ws.freeze_panes(row_pos, 0)

        for role_acl in role.acl_ids:
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space={"role_acl": role_acl},
                default_format=self.format_tcell_left,
            )

    def _get_ws_params_menu(self, data, role):

        menu_template = {
            "name": {
                "header": {"value": "Menu"},
                "data": {"value": self._render("menu.complete_name")},
                "width": 50,
            },
            "menu_id": {
                "header": {"value": "External Identifier"},
                "data": {"value": self._render("xml_id")},
                "width": 50,
            },
        }

        params = {
            "ws_name": "Menu Items",
            "generate_ws_method": "_export_menu",
            "title": "Role ACLs",
            "wanted_list": [k for k in menu_template],
            "col_specs": menu_template,
        }

        return params

    def _export_menu(self, workbook, ws, ws_params, data, role):

        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers["standard"])
        ws.set_footer(self.xls_footers["standard"])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=self.format_theader_yellow_left,
        )
        ws.freeze_panes(row_pos, 0)

        for rec in role.menu_ids:
            [xml_id] = rec.get_external_id().values()
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space={"menu": rec, "xml_id": xml_id},
                default_format=self.format_tcell_left,
            )

    def _get_ws_params_act_window(self, data, role):

        act_window_template = {
            "name": {
                "header": {"value": "Window Action"},
                "data": {"value": self._render("act_window.name")},
                "width": 50,
            },
            "act_window_id": {
                "header": {"value": "External Identifier"},
                "data": {"value": self._render("xml_id")},
                "width": 50,
            },
        }

        params = {
            "ws_name": "Window Actions",
            "generate_ws_method": "_export_act_window",
            "title": "Window Actions",
            "wanted_list": [k for k in act_window_template],
            "col_specs": act_window_template,
        }

        return params

    def _export_act_window(self, workbook, ws, ws_params, data, role):

        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers["standard"])
        ws.set_footer(self.xls_footers["standard"])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=self.format_theader_yellow_left,
        )
        ws.freeze_panes(row_pos, 0)

        for rec in role.act_window_ids:
            [xml_id] = rec.get_external_id().values()
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space={"act_window": rec, "xml_id": xml_id},
                default_format=self.format_tcell_left,
            )

    def _get_ws_params_act_server(self, data, role):

        act_server_template = {
            "name": {
                "header": {"value": "Server Action"},
                "data": {"value": self._render("act_server.name")},
                "width": 50,
            },
            "act_server_id": {
                "header": {"value": "External Identifier"},
                "data": {"value": self._render("xml_id")},
                "width": 50,
            },
        }

        params = {
            "ws_name": "Server Actions",
            "generate_ws_method": "_export_act_server",
            "title": "Server Actions",
            "wanted_list": [k for k in act_server_template],
            "col_specs": act_server_template,
        }

        return params

    def _export_act_server(self, workbook, ws, ws_params, data, role):

        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers["standard"])
        ws.set_footer(self.xls_footers["standard"])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=self.format_theader_yellow_left,
        )
        ws.freeze_panes(row_pos, 0)

        for rec in role.act_server_ids:
            [xml_id] = rec.get_external_id().values()
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space={"act_server": rec, "xml_id": xml_id},
                default_format=self.format_tcell_left,
            )

    def _get_ws_params_act_report(self, data, role):

        act_report_template = {
            "name": {
                "header": {"value": "Report Action"},
                "data": {"value": self._render("act_report.name")},
                "width": 50,
            },
            "act_server_id": {
                "header": {"value": "External Identifier"},
                "data": {"value": self._render("xml_id")},
                "width": 50,
            },
        }

        params = {
            "ws_name": "Report Actions",
            "generate_ws_method": "_export_act_report",
            "title": "Report Actions",
            "wanted_list": [k for k in act_report_template],
            "col_specs": act_report_template,
        }

        return params

    def _export_act_report(self, workbook, ws, ws_params, data, role):

        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers["standard"])
        ws.set_footer(self.xls_footers["standard"])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=self.format_theader_yellow_left,
        )
        ws.freeze_panes(row_pos, 0)

        for rec in role.act_report_ids:
            [xml_id] = rec.get_external_id().values()
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space={"act_report": rec, "xml_id": xml_id},
                default_format=self.format_tcell_left,
            )

    def _get_ws_params_modifier_rule(self, data, role):

        modifier_template = {
            "model": {
                "header": {"value": "Model"},
                "data": {"value": self._render("rule.model or ''")},
                "width": 20,
            },
            "priority": {
                "header": {"value": "Prio"},
                "data": {"value": self._render("rule.priority")},
                "width": 4,
            },
            "view": {
                "header": {"value": "View"},
                "data": {"value": self._render("rule.view_id.name or ''")},
                "width": 20,
            },
            "view_xml_id": {
                "header": {"value": "View External Identifier"},
                "data": {"value": self._render("rule.view_xml_id or ''")},
                "width": 50,
            },
            "view_type": {
                "header": {"value": "View Type"},
                "data": {"value": self._render("rule.view_id.type or ''")},
                "width": 10,
            },
            "element": {
                "header": {"value": "Element"},
                "data": {"value": self._render("rule.element_ui or ''")},
                "width": 50,
            },
            "remove": {
                "header": {"value": "Remove"},
                "data": {"value": self._render("rule.remove and 1 or 0")},
                "width": 6,
            },
            "invisible": {
                "header": {"value": "Invisible"},
                "data": {"value": self._render("rule.modifier_invisible or ''")},
                "width": 25,
            },
            "readonly": {
                "header": {"value": "Readonly"},
                "data": {"value": self._render("rule.modifier_readonly or ''")},
                "width": 25,
            },
            "required": {
                "header": {"value": "Required"},
                "data": {"value": self._render("rule.modifier_required or ''")},
                "width": 25,
            },
            "active": {
                "header": {"value": "Active"},
                "data": {"value": self._render("rule.active and 1 or 0")},
                "width": 6,
            },
            "sequence": {
                "header": {"value": "Sequence"},
                "data": {"value": self._render("rule.sequence")},
                "width": 8,
            },
        }

        params = {
            "ws_name": "View Modifier Rules",
            "generate_ws_method": "_export_modifier_rule",
            "title": "View Modifier Rules",
            "wanted_list": [k for k in modifier_template],
            "col_specs": modifier_template,
        }

        return params

    def _export_modifier_rule(self, workbook, ws, ws_params, data, role):

        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers["standard"])
        ws.set_footer(self.xls_footers["standard"])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=self.format_theader_yellow_left,
        )
        ws.freeze_panes(row_pos, 0)

        for rule in role.modifier_rule_ids:
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space={"rule": rule},
                default_format=self.format_tcell_left,
            )

    def _get_ws_params_view_type_attribute(self, data, role):

        view_type_attribute_template = {
            "priority": {
                "header": {"value": "Prio"},
                "data": {"value": self._render("rule.priority")},
                "width": 4,
            },
            "view": {
                "header": {"value": "View"},
                "data": {"value": self._render("rule.view_id.name or ''")},
                "width": 20,
            },
            "view_xml_id": {
                "header": {"value": "View External Identifier"},
                "data": {"value": self._render("rule.view_xml_id or ''")},
                "width": 50,
            },
            "view_type": {
                "header": {"value": "View Type"},
                "data": {"value": self._render("rule.view_id.type or ''")},
                "width": 10,
            },
            "attrib": {
                "header": {"value": "Attribute"},
                "data": {"value": self._render("rule.attrib or ''")},
                "width": 20,
            },
            "attrib_val": {
                "header": {"value": "Attribute Value"},
                "data": {"value": self._render("rule.attrib_val or ''")},
                "width": 50,
            },
            "active": {
                "header": {"value": "Active"},
                "data": {"value": self._render("rule.active and 1 or 0")},
                "width": 6,
            },
            "sequence": {
                "header": {"value": "Sequence"},
                "data": {"value": self._render("rule.sequence")},
                "width": 8,
            },
        }

        params = {
            "ws_name": "View Type Attributes",
            "generate_ws_method": "_export_view_type_attribute",
            "title": "View Type Attributes",
            "wanted_list": [k for k in view_type_attribute_template],
            "col_specs": view_type_attribute_template,
        }

        return params

    def _export_view_type_attribute(self, workbook, ws, ws_params, data, role):

        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers["standard"])
        ws.set_footer(self.xls_footers["standard"])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=self.format_theader_yellow_left,
        )
        ws.freeze_panes(row_pos, 0)

        for rule in role.view_type_attribute_ids:
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space={"rule": rule},
                default_format=self.format_tcell_left,
            )

    def _get_ws_params_model_operation(self, data, role):

        model_operation_template = {
            "model": {
                "header": {"value": "Model"},
                "data": {"value": self._render("rule.model or ''")},
                "width": 20,
            },
            "priority": {
                "header": {"value": "Prio"},
                "data": {"value": self._render("rule.priority")},
                "width": 4,
            },
            "operation": {
                "header": {"value": "Operation"},
                "data": {"value": self._render("rule.operation or ''")},
                "width": 20,
            },
            "disable": {
                "header": {"value": "Disable"},
                "data": {"value": self._render("rule.disable and 1 or 0")},
                "width": 6,
            },
            "active": {
                "header": {"value": "Active"},
                "data": {"value": self._render("rule.active and 1 or 0")},
                "width": 6,
            },
        }

        params = {
            "ws_name": "View Model Operations",
            "generate_ws_method": "_export_model_operation",
            "title": "View Model Operations",
            "wanted_list": [k for k in model_operation_template],
            "col_specs": model_operation_template,
        }

        return params

    def _export_model_operation(self, workbook, ws, ws_params, data, role):

        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers["standard"])
        ws.set_footer(self.xls_footers["standard"])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=self.format_theader_yellow_left,
        )
        ws.freeze_panes(row_pos, 0)

        for rule in role.model_operation_ids:
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space={"rule": rule},
                default_format=self.format_tcell_left,
            )

    def _get_ws_params_model_method(self, data, role):

        method_template = {
            "name": {
                "header": {"value": "Model,Method"},
                "data": {"value": self._render("entry.name")},
                "width": 60,
            },
            "active": {
                "header": {"value": "Active"},
                "data": {"value": self._render("entry.active and 1 or 0")},
                "width": 6,
            },
        }

        params = {
            "ws_name": "Model Methods",
            "generate_ws_method": "_export_model_method",
            "title": "Model Methods",
            "wanted_list": [k for k in method_template],
            "col_specs": method_template,
        }

        return params

    def _export_model_method(self, workbook, ws, ws_params, data, role):

        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers["standard"])
        ws.set_footer(self.xls_footers["standard"])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=self.format_theader_yellow_left,
        )
        ws.freeze_panes(row_pos, 0)

        for entry in role.model_method_ids:
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space={"entry": entry},
                default_format=self.format_tcell_left,
            )
