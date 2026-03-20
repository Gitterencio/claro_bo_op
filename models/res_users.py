from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError
import logging

class Users(models.Model):
    _inherit = "res.users"
    
    bo_assigned_count = fields.Integer(string='CL BO CONTEO',help="Conteo de listas asignadas",default=0)
    bo_assigned_ready = fields.Boolean(string='CL BO LISTO',help="Esta disponible para asignacion de ventas",default=False)
    bo_assigned_last = fields.Datetime(string='CL BO ULTIMA ASIGNACION',help="Fecha de la ultima asignacion",default=fields.datetime.today())

    def set_count_asigned(self):
        set_filter=[('bo_assigned_user', '=', self.id)]
        self.bo_assigned_count = self.env['claro_oportunidades.oportunidad'].sudo().search_count(set_filter)

    def set_update_asigned(self,data):
        self.bo_assigned_last = data
