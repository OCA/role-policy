# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Role Policy",
    "version": "13.0.0.0.1",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "http://www.noviat.com",
    "category": "Tools",
    "depends": ["mail"],
    "external_dependencies": {"python": ["lxml"]},
    "data": [
        "security/ir.model.access.csv",
        "security/role_policy_security.xml",
        "views/res_role_views.xml",
        "views/res_users_views.xml",
        "views/security_policy_tag_views.xml",
        "views/web_modfier_rule_views.xml",
        "views/menu.xml",
    ],
    "installable": True,
}
