from odoo import models, fields, api, _
import base64
import io


class BOUserStats(models.Model):
    _name = 'claro_bo_op.user_stats'

    bo_assigned_user = fields.Many2one('res.users', string='BackOffice Asignado',)
    bo_assigned_count = fields.Integer(string='CL BO CONTEO',help="Conteo de listas asignadas",default=0)
    bo_assigned_active_count = fields.Integer(string='CL BO CONTEO ACTIVAS',help="Conteo de listas asignadas",default=0)
    bo_assigned_ready = fields.Boolean(string='CL BO LISTO',help="Esta disponible para asignacion de ventas",default=False)
    bo_assigned_last = fields.Datetime(string='CL BO ULTIMA ASIGNACION',help="Fecha de la ultima asignacion",default=fields.datetime.today())

    def set_count_asigned(self):
        set_filter=[('bo_assigned_user', '=', self.bo_assigned_user.id)]
        set_filter_active=[('bo_assigned_user', '=', self.bo_assigned_user.id)]
        self.bo_assigned_count = self.env['claro_oportunidades.oportunidad'].sudo().search_count(set_filter)
        self.bo_assigned_active_count = self.env['claro_oportunidades.oportunidad'].sudo().search_count(set_filter_active)

    def set_update_asigned(self,data):
        self.bo_assigned_last = data

    def set_refresh_count(self):
        records = self.env['claro_bo_op.user_stats'].sudo().search([])
        for r in records:
            r.set_count_asigned()

    _sql_constraints = [

        ('bo_assigned_user_uniq', 'unique(bo_assigned_user)', "USER STATS EXISTS!"),

    ]