from odoo import api, fields, models, SUPERUSER_ID, _
import base64
import io
from lxml import etree
import json

class BOUserStats(models.Model):
    _name = 'claro_bo_op.user_stats'

    bo_assigned_user = fields.Many2one('res.users', string='BackOffice Asignado',)
    bo_assigned_count = fields.Integer(string='CL BO CONTEO',help="Conteo de listas asignadas",default=0)
    bo_assigned_active_count = fields.Integer(string='CL BO CONTEO ACTIVAS',help="Conteo de listas asignadas",default=0)
    bo_assigned_active_limit = fields.Integer(string='CL BO LIMITE ACTIVAS',help="Conteo de listas asignadas",default=20)
    bo_assigned_ready = fields.Boolean(string='CL BO LISTO',help="Esta disponible para asignacion de ventas",default=False)
    bo_assigned_last = fields.Datetime(string='CL BO ULTIMA ASIGNACION',help="Fecha de la ultima asignacion",default=fields.datetime.today())

    has_capacity = fields.Boolean(compute='_compute_capacity', store=True)

    @api.depends('bo_assigned_active_limit', 'bo_assigned_active_count')
    def _compute_capacity(self):
        for rec in self:
            rec.has_capacity = rec.bo_assigned_active_limit == 0 or rec.bo_assigned_active_limit > rec.bo_assigned_active_count
            
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

    @api.model
    def fields_view_get(self, view_id=None, view_type='tree', toolbar=False, submenu=False):
      
        result = super(BOUserStats, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(result['arch'])
        user = self.env['res.users'].sudo().browse(self.env.uid)

        if self._uid == SUPERUSER_ID or user.has_group('claro_bo_op.group_claro_bo_op_stats_general'):
            if doc.xpath("//field[@name='bo_assigned_active_limit']"):
                cals = doc.xpath("//field[@name='bo_assigned_active_limit']")[0]
          
                modifiers = json.loads(cals.get("modifiers", '{}'))
                modifiers.update({'readonly': False})
                cals.set("modifiers", json.dumps(modifiers))
                #cals.set("options",  json.dumps({'clickable': True,'no_create':True,'no_open':True}))
                
        result['arch'] = etree.tostring(doc)
        return result 
