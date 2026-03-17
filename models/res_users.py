from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError


class Users(models.Model):
    _inherit = "res.users"
    
    bo_assigned_count = fields.Integer(string='CL BO CONTEO',help="Conteo de listas asignadas",default=0)
    bo_assigned_ready = fields.Boolean(string='CL BO LISTO',help="Esta disponible para asignacion de ventas",default=False)
