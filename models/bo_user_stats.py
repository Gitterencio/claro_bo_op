from odoo import api, fields, models, SUPERUSER_ID, _
import base64
import io
from lxml import etree
import json
from werkzeug.security import generate_password_hash, check_password_hash

class BOUserStats(models.Model):
    _name = 'claro_bo_op.user_stats'

    bo_assigned_user = fields.Many2one('res.users', string='BackOffice Asignado',)
    bo_assigned_count = fields.Integer(string='CL BO CONTEO',help="Conteo de listas asignadas",default=0)
    bo_assigned_active_count = fields.Integer(string='CL BO CONTEO ACT-RECIENTES',help="Conteo de listas asignadas",default=0)
    bo_assigned_active_limit = fields.Integer(string='CL BO LIMITE ACT-RECIENTES',help="Conteo de listas asignadas",default=20)
    bo_assigned_ready = fields.Boolean(string='CL BO LISTO',help="Esta disponible para asignacion de ventas",default=False)
    bo_assigned_last = fields.Datetime(string='CL BO ULTIMA ASIGNACION',help="Fecha de la ultima asignacion",default=fields.datetime.today())
    bo_assigned_campains = fields.Char(string='CAMP PERMITIDAS',help="Conteo de listas asignadas")


    bo_assigned_permise_code = fields.Char(string='Clave Permiso',help="Clave de permiso")
    bo_assigned_login = fields.Char(
        related='bo_assigned_user.login',
        string='Login',
        store=True
    )

    has_capacity = fields.Boolean(compute='_compute_capacity', store=True)

    @api.depends('bo_assigned_active_limit', 'bo_assigned_active_count')
    def _compute_capacity(self):
        for rec in self:
            rec.has_capacity = rec.bo_assigned_active_limit == 0 or rec.bo_assigned_active_limit > rec.bo_assigned_active_count
            
    def set_count_asigned(self):
        set_filter=[('bo_assigned_user', '=', self.bo_assigned_user.id)]
        set_filter_active=[('ribbon_dynamic_title','!=',"NO-GESTIONAR"),('estado_venta','!=',"caida"),('estado_venta','!=',"anulada"),('ribbon_dynamic_title','=',"INICIO"),('bo_assigned_user', '=', self.bo_assigned_user.id)]
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
    def create(self, vals):
        # Encriptar al crear el registro
        if vals.get('bo_assigned_permise_code'):
            vals['bo_assigned_permise_code'] = generate_password_hash(vals['bo_assigned_permise_code'])
        return super(BOUserStats, self).create(vals)

    def write(self, vals):
        # Encriptar al modificar el registro
        if vals.get('bo_assigned_permise_code'):
            vals['bo_assigned_permise_code'] = generate_password_hash(vals['bo_assigned_permise_code'])
        return super(BOUserStats, self).write(vals)

    def validar_clave(self, clave_ingresada):
        """
        Método de utilidad para verificar si una clave ingresada 
        coincide con la clave encriptada en la base de datos.
        """
        self.ensure_one()
        if not self.bo_assigned_permise_code:
            return False,clave_ingresada
        # Compara el hash guardado con el texto ingresado
        return check_password_hash(self.bo_assigned_permise_code, clave_ingresada),self.bo_assigned_permise_code

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

            if doc.xpath("//field[@name='bo_assigned_campains']"):
                cals = doc.xpath("//field[@name='bo_assigned_campains']")[0]
          
                modifiers = json.loads(cals.get("modifiers", '{}'))
                modifiers.update({'readonly': False})
                cals.set("modifiers", json.dumps(modifiers))

            if doc.xpath("//field[@name='bo_assigned_ready']"):
                cals = doc.xpath("//field[@name='bo_assigned_ready']")[0]
          
                modifiers = json.loads(cals.get("modifiers", '{}'))
                modifiers.update({'readonly': False})
                cals.set("modifiers", json.dumps(modifiers))

        if self._uid == SUPERUSER_ID or user.has_group('claro_bo_op.group_claro_bo_op_stats_administrador'):
            if doc.xpath("//field[@name='bo_assigned_permise_code']"):
                cals = doc.xpath("//field[@name='bo_assigned_permise_code']")[0]
          
                modifiers = json.loads(cals.get("modifiers", '{}'))
                modifiers.update({'readonly': False})
                cals.set("modifiers", json.dumps(modifiers))

                
        result['arch'] = etree.tostring(doc)
        return result 
