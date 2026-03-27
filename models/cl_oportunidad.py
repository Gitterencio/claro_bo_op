from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from openerp.exceptions import UserError, ValidationError
from lxml import etree
import logging
import pytz
import json

class oportunidad(models.Model):
    _inherit = 'claro_oportunidades.oportunidad'

    bo_assigned_user = fields.Many2one('res.users', string='BackOffice Asignado')
    status_op_rec_ids = fields.One2many('claro_bo_op.status_op_rec','oportunidad',string= 'Secuencia Procesos')

    ribbon_dynamic_title = fields.Char(
        compute='_compute_ui_control', 
        store=True
    )

    bo_assigned_last_rec = fields.Char(
        string='Ultimo Estado',
        compute='_compute_ui_control', 
        store=True
    )


    @api.depends('status_op_rec_ids')
    def _compute_ui_control(self):  
        for rec in self:
            titulo="SIN ASIGNAR"
            last="SIN ASIGNAR"
            if rec.status_op_rec_ids:
                titulo = rec.status_op_rec_ids[-1].bo_status_op.process_type
                last = rec.status_op_rec_ids[-1].bo_status_op.name
                if (titulo == 'FIN') and not rec.status_op_rec_ids[-1].end_date:
                    titulo = 'INTERMEDIO'
            
            if rec.permitir_edicion:
                rec.ribbon_dynamic_title = titulo
                rec.bo_assigned_last_rec = last
            else:
               rec.set_permitir_edicion()
               rec.ribbon_dynamic_title = titulo
               rec.bo_assigned_last_rec = last
               rec.set_cerrar_edicion()

    def write(self, values):
        if 'status_op_rec_ids' in values:
            logging.info("############ESTAMOS LOCOS ####################")
            if not self.permitir_edicion:
               self.set_permitir_edicion()
               gao = super(oportunidad, self).write(values)
               self.set_cerrar_edicion()
               return gao
        
        return super(oportunidad, self).write(values)
    
    def get_next_status_bo_assigned(self,prime=False):
        ids_array = self.status_op_rec_ids.mapped('bo_status_op.id')
        set_filter =[('campania', '=', self.campania),('id', 'not in',ids_array )]
        
        if prime:
            set_filter.append(('process_type',"=",'INICIO'))
        status = self.env['claro_bo_op.status_op'].sudo().search(set_filter,limit=1)
        logging.info(set_filter)
        if not prime:
            for rec in self.status_op_rec_ids:
                if not rec.end_date:
                    if rec.rq_respaldo and not rec.respaldo_ids:
                        raise ValidationError(_(f'Se requiere documento de respaldo en {rec.bo_status_op.name} para continuar.'))
                    rec.end_date = datetime.now()
        if status:
            self.env['claro_bo_op.status_op_rec'].sudo().create({'oportunidad':self.id,'start_date':datetime.now(),'bo_status_op':status.id})
        else:
            self._compute_ui_control()


    def set_assigned_bo_by_self(self):
        data = datetime.now()
        user_tz_name = self.env.user.tz or self.env.context.get('tz') or 'UTC'
        user_tz = pytz.timezone(user_tz_name)
        utc_now = pytz.utc.localize(fields.Datetime.now())
        local_data = utc_now.astimezone(user_tz)
        record = self
        user = self.env['res.users'].sudo().browse(self.env.user.id)
        user_stat = self.env['claro_bo_op.user_stats'].sudo().search([('bo_assigned_user', '=', self.env.user.id)],limit=1)
        
        if user and user.partner_id:
            if self.permitir_edicion:
                 self.write({'bo_assigned_user':user.id})
                 self.get_next_status_bo_assigned(prime=True)
            else:
               self.set_permitir_edicion()
               self.write({'bo_assigned_user':user.id})
               self.get_next_status_bo_assigned(prime=True)
               self.set_cerrar_edicion()

            if user_stat:
                user_stat.set_update_asigned(data)            
                user_stat.set_count_asigned()
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
               

        
    @api.model
    def cron_task_assigned_bo(self,anios=0,meses=0,dias=0,fecha=False):
        data = datetime.now()
        limit_data = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if fecha:
            datepart = fecha.split("-")
            limit_data = datetime(year=int(datepart[0]),month=int(datepart[1]),day=int(datepart[2]))
        limit_data = limit_data - relativedelta(months=+meses,days=+dias,years=+anios)
        #logging.info("#######################")
        #logging.info(data.date())
        #logging.info(limit_data)


        user_tz_name = self.env.user.tz or self.env.context.get('tz') or 'UTC'
        user_tz = pytz.timezone(user_tz_name)
        utc_now = pytz.utc.localize(fields.Datetime.now())
        local_data = utc_now.astimezone(user_tz)
        oportunidades_sin_asignar = self.search([('bo_assigned_user', '=', False)])
        for record in oportunidades_sin_asignar:
            user = record.assigned_bo_user(data)
            if user and user.partner_id:
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
        set_order = "bo_assigned_active_count ASC"  #data ASC, data DESC            
        set_filter = [
        ('bo_assigned_ready', '=', True),
        ('has_capacity', '=', True)]
        user_stat = self.env['claro_bo_op.user_stats'].sudo().search(set_filter, order=set_order, limit=1)
        if user_stat:
            if self.permitir_edicion:
                 self.write({'bo_assigned_user':user_stat.bo_assigned_user.id})
                 self.get_next_status_bo_assigned(prime=True)
            else:
               self.set_permitir_edicion()
               self.write({'bo_assigned_user':user_stat.bo_assigned_user.id})
               self.get_next_status_bo_assigned(prime=True)
               self.set_cerrar_edicion()

            user_stat.set_update_asigned(data)            
            user_stat.set_count_asigned()
#
            return user_stat.bo_assigned_user
        
        return False
    
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
      
        result = super(oportunidad, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(result['arch'])
        user = self.env['res.users'].sudo().browse(self.env.uid)

        if self._uid == SUPERUSER_ID or user.has_group('claro_oportunidades.group_claro_oportunidades_administrador'):
            if doc.xpath("//field[@name='bo_assigned_user']"):
                cals = doc.xpath("//field[@name='bo_assigned_user']")[0]
          
                modifiers = json.loads(cals.get("modifiers", '{}'))
                modifiers.update({'readonly': False})
                cals.set("modifiers", json.dumps(modifiers))
                cals.set("options",  json.dumps({'clickable': True,'no_create':True,'no_open':True}))

       
        
        result['arch'] = etree.tostring(doc)
        return result 
