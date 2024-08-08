from odoo import _, api, fields, models, tools, exceptions


class AsignCert(models.Model):
    _name = 'asign.cert'
    _description = 'a.sign Certificate'

    name = fields.Char('Serial (Hex)', required=True)

    serial_hex = fields.Char('Serial (Normalized)', index=True, store=True,
                             compute="_compute_serial_hex",
                             help="Serial number of the certificate in normalized hex format.")

    cert = fields.Binary('Certificate', help='Certificate for the POS system.')
    cert_name = fields.Char(compute='_compute_cert_name')

    cert_type = fields.Selection([
        ('online', 'Online'),
        ('card', 'Card'),
    ], default='online', required=True)

    user = fields.Char()
    password = fields.Char()

    _sql_constraints = [
        (
            'unique_serial_hex', 'UNIQUE(serial_hex)',
            'Serial number hast to be unique'
        )
    ]

    @api.depends('serial_hex')
    def _compute_cert_name(self):
        for cert in self:
            cert.cert_name = f'{self.serial_hex}.cer' if cert.serial_hex else 'cert.cer'

    @api.depends('name')
    def _compute_serial_hex(self):
        for cert in self:
            cert.serial_hex = f'{int(cert.name, 16):x}' if cert.name else ''

    @api.model
    def _get_cert(self, serial_hex):
        asign_cert = self.search([('serial_hex', '=', serial_hex)], limit=1)
        if not asign_cert:
            raise exceptions.ValidationError(_('No certificate found for serial %s', serial_hex))
        return asign_cert

    @tools.ormcache('serial_hex')
    def _get_login(self, serial_hex):
        asign_cert = self._get_cert(serial_hex)
        return asign_cert.user, asign_cert.password
