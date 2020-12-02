# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Role Policy Demo",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/role-policy",
    "category": "Tools",
    "depends": ["role_policy", "contacts"],
    "data": [
        "data/res_role_data.xml",
        "data/web_modifier_rule_data.xml",
        "data/res_user_data.xml",
    ],
    "installable": True,
}
