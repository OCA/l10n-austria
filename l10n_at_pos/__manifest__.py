{
    "name": "POS Austria",
    "version": "17.0.1.0.0",
    "development_status": "Beta",
    "summary": "Austrian POS features for tax authority",
    "category": "Point of sale",
    "author": "Martin Reisenhofer, Odoo Community Association (OCA)",
    "maintainer": "martin-reisenhofer",
    "website": "https://github.com/OCA/l10n_at_pos",
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
    "depends": [
        'l10n_at',
        "point_of_sale",
        'account'
    ],
    "data": [
        "views/res_config_settings_views.xml",
        'views/account_tax_views.xml',
        'views/pos_order_views.xml'
    ],
    'post_init_hook': 'post_init_hook'
}
