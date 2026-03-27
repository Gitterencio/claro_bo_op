from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.claro_oportunidades.models import desplegables as desp_op
from openerp.exceptions import UserError, ValidationError

class BOStatusOp(models.Model):
    _name = 'claro_bo_op.status_op'
    _order = 'campania asc,sequence asc'
    #_rec_name = 'nombre'
    #desp_op.campanias
    campania = fields.Selection(string='Campaña', selection=desp_op.campanias)
    name = fields.Char(string='Etiqueta de Estado')
    sequence = fields.Integer(string='Secuencia',default=10,help="Se ordena de menor a mayor")
    process_type = fields.Selection(string='Tipo', selection=[('INTERMEDIO','INTERMEDIO'),('INICIO','INICIO'),('FIN','FIN')],default="INTERMEDIO")
    rq_respaldo = fields.Boolean(string='Requiere Respaldo', default=False)

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
    bo_status_op = fields.Many2one('claro_bo_op.status_op', string='Status Op',)
    #ABC SIGUIENTE
    start_date = fields.Datetime(string='Inicio Proceso', default=fields.datetime.now())
    end_date = fields.Datetime(string='Fin Proceso',)

    oportunidad = fields.Many2one('claro_oportunidades.oportunidad',ondelete='cascade',string='Oportunidad')
    rq_respaldo = fields.Boolean(string='Respaldo',related='bo_status_op.rq_respaldo', readonly=True)
    respaldo_ids = fields.Many2many('ir.attachment', string="Documento")
    