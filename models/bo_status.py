# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import base64
import io


class BOStatus(models.Model):
    _name = 'claro_bo_op.status'

    @api.model
    def get_bo_assigned_group(self):        
        if self.env.user.has_group('claro_oportunidades.group_claro_oportunidades_bo'):
            return True
        elif self.env.user.bo_assigned_ready:
            self.env.user.sudo().write({"bo_assigned_ready": False})
        
        return False



    @api.model
    def get_bo_assigned_user_status(self):

        return self.env.user.bo_assigned_ready

    @api.model    
    def set_active_status(self):
        self.env.user.sudo().write({"bo_assigned_ready": True})

        notification = {
                'title': 'ESTADO DE RECEPCION ACTIVO',
                'message': f'EN ESPERA DE ASIGNACION DE VENTAS PARA SEGUIMIENTO',
                'sticky': False,
                'warning': True,
        }
  
        if self.env.user.partner_id:
            self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', 
                                         notification)

        return self.env.user.bo_assigned_ready

    @api.model    
    def set_desactive_status(self):
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
        return self.env.user.bo_assigned_ready
