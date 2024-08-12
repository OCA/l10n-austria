{
    "name": "POS Austria Self-Order",
    "version": "17.0.1.0.0",
    "development_status": "Beta",
    "summary": "Austrian POS features for tax authority for Self-Order",
    "category": "Point of sale",
    "author": "Martin Reisenhofer, Odoo Community Association (OCA)",
    "maintainer": "martin-reisenhofer",
    "website": "https://github.com/OCA/l10n_at_pos",
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
    "depends": [
        'l10n_at_pos',
        'pos_self_order'
    ],
    "assets": {
        "pos_self_order.assets": [
            "l10n_at_pos/static/src/css/pos_receipt.css",
            "l10n_at_pos/static/src/overrides/order_receipt.xml",
            "l10n_at_pos_self_order/static/src/**/*"
        ]
    },
    "data": [
    ]
}
