# Copyright 2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ModelMethodExecutionRight(models.Model):
    _inherit = "model.method.execution.right"

    def _selection_name(self):
        model_methods = super()._selection_name()
        account_model_methods = [("account.move,post")]
        model_methods += [(x, x) for x in account_model_methods]
        model_methods.sort()
        return model_methods
