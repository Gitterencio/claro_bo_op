# -*- coding: utf-8 -*-
{
    'name': "Claro BO Asignaciones",
    'summary': """Asignaciones de ventas BO""",
    'description': """Asignaciones de ventas BO""",
    'version': '0.1',
    'category': 'Uncategorized',
    'website': "",
    'depends': ['base', 'web','claro_oportunidades'],
    'data': [
        'data/bo_assigned_op_cron_task.xml',
        'data/bo_assigned_op_user_stats_cron_task.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/_01_tree.xml',
        'views/_02_form.xml',
        'views/_08_action.xml',
        'views/_09_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'claro_bo_op/static/src/js/claro_bo_op_nav.js',
            'claro_bo_op/static/src/scss/claro_bo_op_nav.scss'
        ],
        'web.assets_qweb': [
            'claro_bo_op/static/src/xml/claro_bo_op_nav.xml'
        ],
    },
    # 'images': ['static/description/banner.png'],
  
    'application': True,
  
}
