from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.claro_oportunidades.models import desplegables as desp_op
from openerp.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date

class BOStatusOp(models.Model):
    _name = 'claro_bo_op.status_op'
    _order = 'campania asc,sequence asc'
    #_rec_name = 'nombre'
    #desp_op.campanias
    campania = fields.Selection(string='Campaña', selection=desp_op.campanias)
    name = fields.Char(string='Etiqueta de Estado')
    sequence = fields.Integer(string='Secuencia',default=10,help="Se ordena de menor a mayor")
    process_type = fields.Selection(string='Tipo', selection=[('INTERMEDIO','INTERMEDIO'),('INTERMEDIO-SUB','INTERMEDIO-SUB'),('INICIO','INICIO'),('FIN','FIN')],default="INTERMEDIO")
    rq_respaldo = fields.Boolean(string='Requiere Respaldo', default=False)
    active = fields.Boolean(string='Activo', default=True)

    @api.constrains('campania', 'process_type')
    def _check_unique_start_end(self):
        for record in self:
            if record.process_type in ['INICIO', 'FIN']:
                domain = [
                    ('campania', '=', record.campania),
                    ('process_type', '=', record.process_type),
                    ('id', '!=', record.id) # Excluir el registro actual
                ]
                exists = self.search_count(domain)
                
                if exists > 0:
                    raise ValidationError(_(
                        "Ya existe un estado de tipo %s para la campaña %s. "
                        "Solo se permite un inicio y un fin por campaña."
                    ) % (record.process_type, record.campania))
    

    """
    df_start unico
    df_end unico  ==> por campaña

    """

    #
class BOStatusOpRec(models.Model):
    _name = 'claro_bo_op.status_op_rec'
    _order = 'start_date asc'
    bo_status_op = fields.Many2one('claro_bo_op.status_op', string='Status Op')
    start_date = fields.Datetime(string='Inicio Proceso', default=fields.datetime.now())
    end_date = fields.Datetime(string='Fin Proceso',)
    oportunidad = fields.Many2one('claro_oportunidades.oportunidad',ondelete='cascade',string='Oportunidad')
    rq_respaldo = fields.Boolean(string='Respaldo',related='bo_status_op.rq_respaldo', readonly=True)
    respaldo_ids = fields.Many2many('ir.attachment', string="Documento")
    

    def action_save_and_close(self):
        return {'type': 'ir.actions.act_window_close'}
    
    @api.onchange('bo_status_op')
    def _onchange_bo_status_op_end(self):
        if self.bo_status_op and self.bo_status_op.process_type == 'FIN':
            if not self.end_date:
                self.end_date = datetime.now()
        else:
            self.end_date = False
    

    @api.onchange('oportunidad')
    def _onchange_bo_status_op_domain(self):
 
        if self.oportunidad:
            # IDs de estados que ya se usaron
            used_status_ids = self.oportunidad.status_op_rec_ids.mapped('bo_status_op').ids
            
            return {
                'domain': {
                    'bo_status_op': [
                        ('campania', '=', self.oportunidad.campania), # Referencia a status_op.campania
                        ('id', 'not in', used_status_ids),
                        ('active', '=', True)
                    ]
                }
            }