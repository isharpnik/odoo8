# -*- coding: utf-8 -*-

{
    'name': 'Stock Split Picking Wizard',
    'category': 'Warehouse Management',
    'author': 'Ajay Patel',
    'version': '8.0.1.0.0',
    'website': 'www.technosquare.in',
    'description':
        """

Odoo-8.0 Stock Split Picking Wizard
===============================================
        Stock Split Picking Wizard
""",
    'depends': ['stock'],
    'data': [
        'views/stock_partial_picking.xml',
        'wizard/stock_split_details.xml',
    ],
    'auto_install': False,
    'installable': True,

}
