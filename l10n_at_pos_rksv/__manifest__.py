# Copyright 2024 Weboffice IT-Service und Marketing GmbH & Co KG <https://weboffice.at>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
{
    "name": "POS Austria RKSV",
    "summary": "Austrian RKSV (a.sign) integration for Point of Sale",
    "author": (
        "Weboffice IT-Service und Marketing GmbH & Co KG, "
        "Odoo Community Association (OCA)"
    ),
    "website": "https://github.com/OCA/l10n-austria",
    "category": "Localization/Austria",
    "version": "20.0.1.7.0",
    "license": "LGPL-3",
    "depends": [
        "l10n_at",
        "point_of_sale",
    ],
    "external_dependencies": {
        "python": ["cryptography", "requests"],
    },
    "data": [
        "data/asign_cron.xml",
        "views/res_config_settings_views.xml",
        "views/account_tax_views.xml",
        "views/pos_order_views.xml",
        "views/asign_views.xml",
        "views/pos_config_views.xml",
        "views/report_certificate.xml",
        "views/report_pos_config.xml",
        "views/pos_report.xml",
        "receipt/pos_order_receipt.xml",
        "security/ir.access.csv",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "l10n_at_pos_rksv/static/src/**/*",
        ],
    },
    "post_init_hook": "post_init_hook",
    "development_status": "Beta",
    "installable": True,
}
