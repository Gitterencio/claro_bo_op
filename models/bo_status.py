# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import base64
import io
import logging

class BOStatus(models.Model):
    _name = 'claro_bo_op.status'

    @api.model
    def get_user_stats(self):
        user_stat = self.env['claro_bo_op.user_stats'].sudo().search([('bo_assigned_user', '=', self.env.user.id)],limit=1)
        return user_stat
    
    @api.model
    def get_bo_assigned_group(self):   
        if self.env.user.has_group('claro_oportunidades.group_claro_oportunidades_bo'):
            user_stat = self.get_user_stats()
            if not user_stat:
                self.env['claro_bo_op.user_stats'].sudo().create({'bo_assigned_user': self.env.user.id})
            return True
        else:
            user_stat = self.get_user_stats()
            if user_stat:
                user_stat.sudo().write({"bo_assigned_ready": False})
        
        return False



    @api.model
    def get_bo_assigned_user_status(self):
        user_stat = self.get_user_stats()
        if user_stat:
            return user_stat.bo_assigned_ready
        else:
            return False

    @api.model    
    def set_active_status(self):
        user_stat = self.get_user_stats()
        if user_stat:
            user_stat.sudo().write({"bo_assigned_ready": True})

            notification = {
                'title': 'ESTADO DE RECEPCION ACTIVO',
                'message': f'EN ESPERA DE ASIGNACION DE VENTAS PARA SEGUIMIENTO',
                'sticky': False,
                'warning': True,
            }
  
            if self.env.user.partner_id:
                self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', 
                                         notification)

            return user_stat.bo_assigned_ready
        else:
            return False

    @api.model    
    def set_desactive_status(self):
        user_stat = self.get_user_stats()
        if user_stat:
            user_stat.sudo().write({"bo_assigned_ready": False})
            notification = {
                'title': 'ESTADO DE RECEPCION INACTIVO',
                'message': f'FUERA DE LA LISTA DE RECEPCION DEVENTAS PARA SEGUIMIENTO',
                'sticky': False,
                'warning': False,
            }
  
            if self.env.user.partner_id:
                self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', 
                                         notification)
            return user_stat.bo_assigned_ready
        
        else:
            return False

    @api.model
    def get_link_active_record(self):

        lista = []
        host = "http://localhost:8069"
        base_url = self.env['ir.config_parameter'].sudo().get_param('claro_bo_op.bo_assigned_host') or host
        menu_id = self.env.ref('claro_oportunidades.menu_root').id
        action_id = self.env.ref('claro_oportunidades.oportunidad_action_window_bo').id

        set_filter_active=[('estado_venta','!=',"caida"),('ribbon_dynamic_title','=',"INICIO"),('estado_venta','!=',"anulada"),('ribbon_dynamic_title','!=',"FIN"),('bo_assigned_user', '=', self.env.user.id)]
        records = self.env['claro_oportunidades.oportunidad'].sudo().search(set_filter_active,order='bo_assigned_date desc')
        
        for record in records:
            url_lista = f"{base_url}/web#id={record.id}&menu_id={menu_id}&action={action_id}&model=claro_oportunidades.oportunidad&view_type=form"
            espacios = '\u00A0' * 3
            lista.append({'text': f'■[Campaña:{record.campania}]{espacios}{record.nombre}{espacios}[Estado:{record.bo_assigned_last_rec}]{espacios}[ID:{record.id}]', 'url': url_lista})

        return lista