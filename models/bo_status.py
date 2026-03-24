# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import base64
import io


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
        elif self.env.user.bo_assigned_ready:
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
            self.env.user.sudo().write({"bo_assigned_ready": False})
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
