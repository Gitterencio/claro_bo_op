from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import datetime, timedelta, date
from openerp.exceptions import UserError, ValidationError
from lxml import etree
import logging
import pytz
import json

class oportunidad(models.Model):
    _inherit = 'claro_oportunidades.oportunidad'

    bo_assigned_user = fields.Many2one('res.users', string='BackOffice Asignado')


    
    #Cuando Odoo ejecuta un método a través de un cron job usando el decorador @api.model (por ejemplo, model.cron_task_assigned_bo()), self representa una instancia vacía del modelo en sí (la clase), no un registro específico de la base de datos
    @api.model
    def cron_task_assigned_bo(self):
        data = datetime.now()
        user_tz_name = self.env.user.tz or self.env.context.get('tz') or 'UTC'
        user_tz = pytz.timezone(user_tz_name)
        utc_now = pytz.utc.localize(fields.Datetime.now())
        local_data = utc_now.astimezone(user_tz)
        oportunidades_sin_asignar = self.search([('bo_assigned_user', '=', False)])
        for record in oportunidades_sin_asignar:
            user = record.assigned_bo_user(data)
            if user and user.partner_id:
                #logging.info("#######################")
                mensaje_tag = 'LA VENTA {1} FUE ASIGNADA A {0} \n Hora: {2} || Fecha: {3}'.format(user.name,record.nombre,local_data.strftime("%H:%M"), local_data.date())
                self.send_notify_tag_assigned_bo_user(mensaje_tag,user.partner_id)

       
                host = "http://localhost:8069"
                base_url = self.env['ir.config_parameter'].sudo().get_param('claro_bo_op.bo_assigned_host') or host

                menu_id = self.env.ref('claro_oportunidades.menu_root').id
                action_id = self.env.ref('claro_oportunidades.oportunidad_action_window_bo').id

                url_lista = f"{base_url}/web#id={record.id}&menu_id={menu_id}&action={action_id}&model=claro_oportunidades.oportunidad&view_type=form"
                message_text = f"""
                <p>_______________________________________________________________________</p>
                <p><strong>¡Venta {record.nombre} Asignada!</strong> {local_data.date()} {local_data.strftime("%H:%M")}</p>
                <p><strong>Campaña</strong>: {record.campania} </p>
                <p><strong>Nombre del Cliente</strong>: {record.nombre} </p>
                <p><strong>Creada</strong>: {record.create_date} </p>
                <p><strong>Asesor</strong>: {record.asesor.name} </p>
                <p><strong>ID Registro</strong>: {record.id} </p>
                <div>
                 <a href="{url_lista}" 
                    style="background-color: #875A7B; color: white; padding: 8px 16px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                     Ver mis oportunidades asignadas
                    </a>
               </div>
               <p>_______________________________________________________________________</p>
               """
                self.send_notify_inbox_assigned_bo_user(user.name,message_text,user.partner_id.id)
               


        return

  
    def send_notify_tag_assigned_bo_user(self,mensaje_tag,partner_id):
            notification = {
                'title': 'ASIGNACION DE VENTA BO',
                'message': f'{mensaje_tag}',
                'sticky': True,
                'warning': True,
                }
            self.env['bus.bus']._sendone(partner_id, 'simple_notification', 
                                         notification)
            
            

    def send_notify_inbox_assigned_bo_user(self,user_name,mensaje_inbox,partner_id):
            odoobot_id = self.env.ref('base.partner_root').id 

            channel = self.env['mail.channel'].sudo().search([
                ('channel_type', '=', 'chat'),
                ('channel_partner_ids', 'in', [partner_id]),
                ('channel_partner_ids', 'in', [odoobot_id])
            ], limit=1)

            if not channel:
                channel = self.env['mail.channel'].sudo().with_context(mail_create_nosubscribe=True).create({
                    'channel_partner_ids': [(6, 0, [partner_id, odoobot_id])],
                    'public': 'private',
                    'channel_type': 'chat',
                    'name': f'OdooBot & {user_name} NOTI-BO',
                })

            # 3. Postear el mensaje como si fuera OdooBot
            channel.sudo().message_post(
                body=mensaje_inbox,
                author_id=odoobot_id, # Esto hace que parezca enviado por OdooBot
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
            )

    @api.model
    def assigned_bo_user(self,data):
        set_filter=[('bo_assigned_ready', '=', True)]
        set_order = "bo_assigned_count ASC"  #data ASC, data DESC    
        users = self.env['res.users'].sudo().search(set_filter,order=set_order)
        
        if users:
            user = users[0]
    
            if self.permitir_edicion:
                 self.write({'bo_assigned_user':user.id})
            else:
               self.set_permitir_edicion()
               self.write({'bo_assigned_user':user.id})
               self.set_cerrar_edicion()

            user.set_update_asigned(data)            
            user.set_count_asigned()
#
            return user
        
        return False
    
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
      
        result = super(oportunidad, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(result['arch'])
        user = self.env['res.users'].sudo().browse(self.env.uid)
        logging.info("#######################")
        if self._uid == SUPERUSER_ID or user.has_group('claro_oportunidades.group_claro_oportunidades_administrador'):
            if doc.xpath("//field[@name='bo_assigned_user']"):
                cals = doc.xpath("//field[@name='bo_assigned_user']")[0]
          
                modifiers = json.loads(cals.get("modifiers", '{}'))
                modifiers.update({'readonly': False})
                cals.set("modifiers", json.dumps(modifiers))
                cals.set("options",  json.dumps({'clickable': True,'no_create':True,'no_open':True}))
                
        result['arch'] = etree.tostring(doc)
        return result 
