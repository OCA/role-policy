# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _compute_sales_count(self):
        sale_report_group_ids = self.env["ir.model.access"]._get_acl_access_group_ids(
            "sale.report", "r"
        )
        if not any([x in sale_report_group_ids for x in self.env.user.groups_id.ids]):
            self.sales_count = 0
            return {}
        else:
            return super()._compute_sales_count()
