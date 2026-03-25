odoo.define('claro_bo_op.status', function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.Widget');
    var SystrayMenu = require('web.SystrayMenu');
    var rpc = require('web.rpc');

    var _t = core._t;
    var QWeb = core.qweb;

    var Status_form_btn = Widget.extend({
        template: 'claro_bo_op.status_form_btn',
        events: {
            "click": "on_click",
            "click #bo_status_green_on": "f_desactive_status",
            "click #bo_status_red_off": "f_active_status",
        },

        /**
         * @override
         */
        start: function () {
            var self = this;

            // Inicializamos ocultando elementos usando el selector local this.$
            this.$('#alert').hide();
            this.$('#bo_status_green_on').hide();
            this.$('#bo_status_red_off').hide();

            // Es fundamental retornar el super y la promesa del RPC
            // para que Odoo espere a que el DOM esté listo antes de posicionar el widget.
            return this._super.apply(this, arguments).then(function () {
                return self.f_get_bo_assigned_group();
            });
        },

        // Helper para centralizar la actualización de la UI
        _update_ui_status: function (isActive) {

            if (isActive) {
                this.$('#bo_status_green_on').show();
                this.$('#bo_status_red_off').hide();
            } else {
                this.$('#bo_status_green_on').hide();
                this.$('#bo_status_red_off').show();
            }
        },

        on_click: function (event) {
            // Evita que el dropdown se cierre si el click no es en un icono específico
            if (!$(event.target).is('i')) {
                event.stopPropagation();
            }
        },

        f_desactive_status: function () {
            var self = this;
            rpc.query({
                model: 'claro_bo_op.status',
                method: 'set_desactive_status',
                args: []
            }).then(function (result) {
                self._update_ui_status(result);
            });
        },

        f_active_status: function () {
            var self = this;
            rpc.query({
                model: 'claro_bo_op.status',
                method: 'set_active_status',
                args: []
            }).then(function (result) {
                self._update_ui_status(result);
            });
        },

        f_get_bo_status: function () {
            var self = this;
            return rpc.query({
                model: 'claro_bo_op.status',
                method: 'get_bo_assigned_user_status',
                args: []
            }).then(function (result) {
                self._update_ui_status(result);
            });
        },

        f_get_bo_assigned_group: function () {
            var self = this;
            return rpc.query({
                model: 'claro_bo_op.status',
                method: 'get_bo_assigned_group',
                args: []
            }).then(function (result) {

                if (!result) {
                    self.$('#bo_status_green_on').hide();
                    self.$('#bo_status_red_off').hide();
                } else {
                    return self.f_get_bo_status();
                }
            });
        },


    });


    var Status_record_list = Widget.extend({
        template: 'claro_bo_op.status_record_list',
        events: {
            "click": "on_click",
        },

        init: function (parent) {
            this._super(parent);

            this.links_list = [];

        },
        willStart: function () {
            var self = this;
      
            return this._super().then(function () {
                return self.f_get_link_active_record().then(function (res) {

                    self.links_list = res;
                });
            });
        },

        /**
         * @override
         */
        start: function () {
            var self = this;

            this.$('#show-list').hide();

            return this._super.apply(this, arguments).then(function () {
                return self.f_get_bo_assigned_group();
            });
        },

        on_click: function (event) {

            if (!$(event.target).is('i')) {
                event.stopPropagation();
            }
        },

        f_get_link_active_record: function () {
            var self = this;
            return rpc.query({
                model: 'claro_bo_op.status',
                method: 'get_link_active_record',
                args: []
            }).then(function (result) {

                return result
            });
        },
        f_get_bo_assigned_group: function () {
            var self = this;
            return rpc.query({
                model: 'claro_bo_op.status',
                method: 'get_bo_assigned_group',
                args: []
            }).then(function (result) {

                if (!result) {
                    self.$('#show-list').hide();
                } else {
                    self.$('#show-list').show();

                }
            });
        },


    });

    SystrayMenu.Items.push(Status_form_btn);
    SystrayMenu.Items.push(Status_record_list);


    return {
        Status_form_btn: Status_form_btn,
        Status_record_list: Status_record_list
    };
});