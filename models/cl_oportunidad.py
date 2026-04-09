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
    bo_assigned_await = fields.Boolean(string='Asignacion Solicitada', default=False)
    bo_assigned_await_date = fields.Datetime(string='Fecha de Solicitud Asignacion')
    bo_assigned_date = fields.Datetime(string='Fecha de Asignacion')
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
            titulo = "SIN ASIGNAR"
            last = "SIN ASIGNAR"
            
            if rec.status_op_rec_ids:
                ultimo_estado = rec.status_op_rec_ids[-1]
                
                # Prevenir errores si bo_status_op está vacío temporalmente
                if ultimo_estado.bo_status_op:
                    titulo = ultimo_estado.bo_status_op.process_type or "SIN ASIGNAR"
                    last = ultimo_estado.bo_status_op.name or "SIN ASIGNAR"
                    
                if (titulo == 'FIN') and not ultimo_estado.end_date:
                    titulo = 'INTERMEDIO'
            
            # ASIGNACIÓN DIRECTA SIN ROMPER LA CACHÉ
            # Odoo autoriza esto nativamente por ser un campo compute (store=True)
            rec.ribbon_dynamic_title = titulo
            rec.bo_assigned_last_rec = last

    def _limpiar_diccionario_newid(self, data):
        """
        Escanea recursivamente los comandos de Odoo y convierte los objetos 
        virtuales (<NewId origin=X>) en enteros (X).
        """
        if isinstance(data, dict):
            return {k: self._limpiar_diccionario_newid(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._limpiar_diccionario_newid(v) for v in data]
        elif isinstance(data, tuple):
            return tuple(self._limpiar_diccionario_newid(v) for v in data)
        elif hasattr(data, 'origin') and getattr(data, 'origin', False):
            return int(data.origin)
        return data

    def write(self, values):
        # 1. Limpiamos los NewId de la interfaz ANTES de pasarlo al padre
        clean_values = self._limpiar_diccionario_newid(values)

        # 2. Si vienen cambios en la secuencia de procesos (status_op_rec_ids)
        if 'status_op_rec_ids' in clean_values:
            
            if not self.permitir_edicion:
                
                # EL CABALLO DE TROYA: 
                # Le inyectamos 'permitir_edicion' al diccionario desde aquí.
                # El modelo padre leerá esto y dejará pasar el guardado.
                clean_values['permitir_edicion'] = True
                
                # Mandamos los datos limpios y con la llave al padre
                res = super(oportunidad, self).write(clean_values)
                
                # Volvemos a bloquear la edición silenciosamente
                self.write({'permitir_edicion': False})
                
                return res
        
        # 3. Comportamiento normal si no hay cambios en la secuencia
        return super(oportunidad, self).write(clean_values)
    
    def delete_assigne_user(self):
        if self.permitir_edicion:
            self.bo_assigned_user = False
            self.status_op_rec_ids.unlink()
         

        else:
            self.set_permitir_edicion()
            self.bo_assigned_user = False
            self.status_op_rec_ids.unlink()
            self.set_cerrar_edicion()

    def get_next_status_bo_assigned(self,prime=False,context={}):
        ids_array= []
        if self.status_op_rec_ids:
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
            if prime:
                ahora = datetime.now()
                self.env['claro_bo_op.status_op_rec'].sudo().create({'oportunidad':self.id,'start_date':ahora,'bo_status_op':status.id})
                
            else:
                idx=-100
                if self.status_op_rec_ids:
                    idx = self.status_op_rec_ids[-1].bo_status_op.sequence
                set_filter.append(('sequence',">=",idx))
                status = self.env['claro_bo_op.status_op'].sudo().search(set_filter,limit=1)
                form_view_id = self.env.ref("claro_bo_op.status_op_rec_form_view").id

                context = {}
                ctx = context.copy()
                
                ctx.update({'default_oportunidad': self.id})
                ctx.update({'default_start_date': datetime.now()})
                ctx.update({'default_bo_status_op': status.id})
                #'context': ctx,
                return {
                    'name': 'Actualizar Estado',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'claro_bo_op.status_op_rec',
                    'views': [(form_view_id, 'form')],
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'nodestroy':False,
                    'target': 'new',
                    'context': ctx,
                }
        else:
            self._compute_ui_control()

    def set_need_assigned(self):
        if self.permitir_edicion:
            self.write({'bo_assigned_await':True})
            self.write({'bo_assigned_await_date':datetime.now()})
         

        else:
            self.set_permitir_edicion()
            self.write({'bo_assigned_await':True})
            self.write({'bo_assigned_await_date':datetime.now()})
            self.set_cerrar_edicion()
        try:
            self.cron_task_assigned_bo()
        except:
            logging.info("##########ERROR EN LA ASINACION SOLICITUD#############")

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
                 self.write({'bo_assigned_date':datetime.now()})
                 self.get_next_status_bo_assigned(prime=True)
            else:
               self.set_permitir_edicion()
               self.write({'bo_assigned_user':user.id})
               self.write({'bo_assigned_date':datetime.now()})
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
       
        #logging.info(data.date())
        #logging.info(limit_data)


        user_tz_name = self.env.user.tz or self.env.context.get('tz') or 'UTC'
        user_tz = pytz.timezone(user_tz_name)
        utc_now = pytz.utc.localize(fields.Datetime.now())
        local_data = utc_now.astimezone(user_tz)
        oportunidades_sin_asignar = self.search([('create_date', '>=', limit_data),('bo_assigned_user', '=', False),('bo_assigned_await', '=', True)])
        logging.info("##########EEEEEEE#############")
        logging.info(len(oportunidades_sin_asignar))
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
            
            

    def send_notify_inbox_assigned_bo_user(self, user_name, mensaje_inbox, partner_id):
        odoobot_id = self.env.ref('base.partner_root').id 

        channel = self.env['mail.channel'].sudo().search([
            ('channel_type', '=', 'chat'),
            ('channel_partner_ids', 'in', [partner_id]),
            ('channel_partner_ids', 'in', [odoobot_id])
        ], limit=1)

        if not channel:
            # SOLUCIÓN DEFINITIVA: Usar tuplas con el comando 4 (Agregar registro)
            channel = self.env['mail.channel'].sudo().with_context(mail_create_nosubscribe=True).create({
                'channel_partner_ids': [(4, partner_id), (4, odoobot_id)], 
                'public': 'private',
                'channel_type': 'chat',
                'name': f'OdooBot & {user_name} NOTI-BO',
            })

        # Postear el mensaje como si fuera OdooBot
        channel.sudo().message_post(
            body=mensaje_inbox,
            author_id=odoobot_id, 
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
        value = user_stat.bo_assigned_campains
        campains = value.split(",") if isinstance(value, str) and value else False
        logging.info(f'CAMPANNAS {campains}')
        if user_stat and (not campains or self.campania in campains):
            if self.permitir_edicion:
                 self.write({'bo_assigned_user':user_stat.bo_assigned_user.id})
                 self.write({'bo_assigned_date':datetime.now()})
                 self.get_next_status_bo_assigned(prime=True)
            else:
               self.set_permitir_edicion()
               self.write({'bo_assigned_user':user_stat.bo_assigned_user.id})
               self.write({'bo_assigned_date':datetime.now()})
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
