from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    bo_assigned_host = fields.Char(string="BO ASSIGNED HOST",default="http://10.0.90.10:8069",config_parameter="claro_bo_op.bo_assigned_host")

