from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import datetime, timedelta, date
from openerp.exceptions import UserError, ValidationError
from lxml import etree
import json

class oportunidad(models.Model):
    _inherit = 'claro_oportunidades.oportunidad'

    @api.model
    def cron_task_assigned_bo(self):
        data = datetime.now()
        mensaje = 'Hora: {0} || Fecha: {1} TZ-Estandar'.format(data.strftime("%H:%M:%S"), data.date())
        notification = {
                'title': 'ESTADO CAMBIO',
                'message': f'{mensaje}',
                'sticky': False,
                'warning': True,
        }

        target_user_id = 2 
        user = self.env['res.users'].browse(target_user_id)
  
        if user.partner_id:
            self.env['bus.bus']._sendone(user.partner_id, 'simple_notification', 
                                         notification)
        return