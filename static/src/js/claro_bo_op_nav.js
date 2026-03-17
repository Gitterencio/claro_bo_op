odoo.define('claro_bo_op.status', function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.Widget');
    var SystrayMenu = require('web.SystrayMenu');
    var rpc = require('web.rpc')

    var _t = core._t;
    var QWeb = core.qweb

    var Status_form_btn = Widget.extend({
        template: 'claro_bo_op.status_form_btn',
        events: {
            "click": "on_click",
            "click #bo_status_green_on": "f_desactive_status",
            "click #bo_status_red_off": "f_active_status",
        },

        start: function () {
            this.$('#alert').hide();
            this.$('#bo_status_green_on').hide();
            this.$('#bo_status_red_off').hide();
            this.f_get_bo_assigned_group();

        },

        on_click: function (event) {
            if ($(event.target).is('i') === false) {
                event.stopPropagation();
            }
        },
        f_desactive_status: function () {
                 rpc.query({
                model: 'claro_bo_op.status',
                method: 'set_desactive_status',
                args: []
            }).then(function (result) {
               if (result) {
                    $('#bo_status_green_on').show();
                    $('#bo_status_red_off').hide();
                } else {
                    $('#bo_status_green_on').hide();
                    $('#bo_status_red_off').show();
                }
               
            });
        },
        f_active_status: function () {
             rpc.query({
                model: 'claro_bo_op.status',
                method: 'set_active_status',
                args: []
            }).then(function (result) {
               if (result) {
                    $('#bo_status_green_on').show();
                    $('#bo_status_red_off').hide();
                } else {
                    $('#bo_status_green_on').hide();
                    $('#bo_status_red_off').show();
                }
               
            });
        },
        f_get_bo_status: function () {
            rpc.query({
                model: 'claro_bo_op.status',
                method: 'get_bo_assigned_user_status',
                args: []
            }).then(function (result) {
                if (result) {
                    $('#bo_status_green_on').show();
                    $('#bo_status_red_off').hide();
                } else {
                    $('#bo_status_green_on').hide();
                    $('#bo_status_red_off').show();
                }
            });

        },

        f_get_bo_assigned_group:function () {
            var self = this;
            rpc.query({
                model: 'claro_bo_op.status',
                method: 'get_bo_assigned_group',
                args: []
            }).then(function (result) {

                if (!result) {
                    
                    $('#bo_status_green_on').hide();
                    $('#bo_status_red_off').hide();
                }else{
                    self.f_get_bo_status();
                } 
            });

        },
        f_short: function () {
            var data = $('#ip_link').val();
            if (data != "") {
                rpc.query({
                    model: 'qr.generator',
                    method: 'get_qr_code',
                    args: [data]
                }).then(function (result) {
                    document.getElementById("ItemPreview").src = "data:image/png;base64," + result;
                    document.getElementById("b_download").href = "data:image/png;base64," + result;
                    $('#ItemPreview').show();
                    $('#BtnDownload').show();
                });
            }
            else {
                $('#ItemPreview').hide();
                $('#BtnDownload').hide();
            }
        },

        f_clear: function () {
            $("#ip_link").val("");
            $('#ItemPreview').hide();
            $('#BtnDownload').hide();
        },

    });

    SystrayMenu.Items.push(Status_form_btn);

    return {
        Status_form_btn: Status_form_btn,
    };
});
