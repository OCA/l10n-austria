from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    asign_enabled = fields.Boolean('a.sign Enabled', help='Enable Austrian RKSV for POS.')

    asign_method = fields.Selection([('card', 'Card'),
                                     ('online', 'Online')], string='a.sign Method')

    asign_state = fields.Selection([('draft', 'Draft'),
                                    ('assign', 'Assigned'),
                                    ('active', 'Active')], string="a.sign State")

    asign_serial_hex = fields.Char('a.sign Serial',
                                   help='Serial number of the certificate in hex format.')

    asign_cid = fields.Char('a.sign Company ID', help='VAT or tax number of the company.')
    asign_pid = fields.Char('a.sign POS ID', help="ID of the POS system, and prefix of the order number.")
    asign_key = fields.Char('a.sign Encryption Key', help="The AES encryption key of the journal.")

    asign_user = fields.Char('a.sign User')
    asign_password = fields.Char('a.sign Password')



