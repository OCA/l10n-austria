import re
import base64
import hashlib
import secrets
from odoo import fields, models, api, exceptions, _

AES_KEY_SIZE = 32
CRC_N = 3

def next_sequence(objs, field):
    """ Try to find the next sequence for the given field in the given objects. """
    if not objs:
        return None
    # search all existing sequences
    sequences = [v for v in objs.mapped(field) if v]
    if not sequences:
        return None
    # find the last sequence
    last_sequence = max(sequences)
    # try to determine the next sequence
    m = re.match("([^0-9]*)([0-9]+)(.*)", last_sequence)
    if m:
        nextno = str(int(m.group(2)) + 1)
        nextno = nextno.zfill(len(m.group(2)))
        return f'{m.group(1)}{nextno}{m.group(3)}'

    return None


class PosConfig(models.Model):
    _inherit = 'pos.config'


    def _default_asign_fid(self):
        return self.env.company.vat

    def _default_asign_pid(self):
        configs = self.env['pos.config'].search([('company_id', '=', self.env.company.id)])
        return next_sequence(configs, 'asign_pid')

    def _default_asign_key(self):
        return base64.b64encode(secrets.token_bytes(AES_KEY_SIZE)).decode()


    asign_enabled = fields.Boolean('a.sign Enabled', help='Enable Austrian RKSV for POS.')

    asign_method = fields.Selection([('card', 'Card'),
                                     ('online', 'Online')], string='a.sign Method',
                                     default='online')

    asign_state = fields.Selection([('draft', 'Draft'),
                                    ('assigned', 'Assigned'),
                                    ('active', 'Active')], string='a.sign State',
                                    default='draft', readonly=True, copy=False)

    asign_serial_hex = fields.Char('a.sign Serial',
                                   help='Serial number of the certificate in hex format.')

    asign_fid = fields.Char('a.sign Fiscal ID', help='VAT or tax number of the company for the POS.',
                            default=_default_asign_fid)

    asign_pid = fields.Char('a.sign POS ID',
                            default=_default_asign_pid,
                            help="Fiscal ID of the POS system inside the company, and prefix of the order number.", copy=False)
    asign_key = fields.Char('a.sign Encryption Key', help="The AES encryption key of the journal.", copy=False,
                            default=_default_asign_key)

    asign_crc = fields.Char('a.sign Checksum',
                            compute="_compute_asign_crc",
                            help='Checksum of the encryption key.', copy=False, store=True)

    asign_cert = fields.Binary('a.sign Certificate', help='Certificate for the POS system.')

    asign_user = fields.Char('a.sign User')
    asign_password = fields.Char('a.sign Password')

    _sql_constraints = [
        (
            'unique_asign_pid', 'UNIQUE(company_id, asign_pid)',
            'Fiscal POS ID hast to be unique for the company')
    ]

    @api.constrains('asign_serial_hex', 'asign_fid', 'asign_pid', 'asign_key', 'asign_user', 'asign_password')
    def _check_asign_config(self):
        for config in self:
            if config.asign_enabled:
                if not config.asign_method:
                    raise exceptions.ValidationError(
                        f'Austrian RKSV activated but method is empty for POS {config.name}')
                if not config.asign_state:
                    raise exceptions.ValidationError(
                        f'Austrian RKSV activated but state is invalid for POS {config.name}')
                if not config.asign_serial_hex:
                    raise exceptions.ValidationError(
                        f'Austrian RKSV activated but serial is empty for POS {config.name}')
                if not config.asign_fid:
                    raise exceptions.ValidationError(
                        f'Austrian RKSV activated but fiscal ID is empty for POS {config.name}')
                if not config.asign_pid:
                    raise exceptions.ValidationError(
                        f'Austrian RKSV activated but POS ID is empty for POS {config.name}')
                if not config.asign_key:
                    raise exceptions.ValidationError(
                        f'Austrian RKSV activated but encryption key is empty for POS {config.name}')
                if not len(base64.b64decode(config.asign_key)) == AES_KEY_SIZE:
                    raise exceptions.ValidationError(
                        f'Austrian RKSV activated but encryption key has invalid length ({len(config.asign_key)} != 32) for POS {config.name}')

    @api.depends('asign_key')
    def _compute_asign_crc(self):
        for config in self:
            if config.asign_key:
                checksum = hashlib.sha256(config.asign_key.encode()).digest()[:CRC_N]
                config.asign_crc = base64.b64encode(checksum).decode().rstrip('=')
            else:
                config.asign_crc = ''

    def action_asign_assign(self):
        configs = self.filtered(lambda c: c.asign_enabled and c.asign_state == 'draft')
        config_with_open_sessions = configs.filtered(lambda c: c.has_active_session)
        if config_with_open_sessions:
            raise exceptions.UserError(_('POS %s has open sessions. Close them first.', config_with_open_sessions[0].name))
        # write new state
        configs.write({
            'asign_state': 'assigned'
        })

    def action_asign_reset(self):
        configs = self.filtered(lambda c: c.asign_enabled and c.asign_state in ('assigned', 'active'))
        config_with_open_sessions = configs.filtered(lambda c: c.has_active_session)
        if config_with_open_sessions:
            raise exceptions.UserError(_('POS %s has open sessions. Close them first.', config_with_open_sessions[0].name))
        # write new state
        configs.write({
            'asign_state': 'draft'
        })

    def _get_self_ordering_data(self):
        """ Add Austrian RKSV configuration to the POS configuration data. """
        data = super()._get_self_ordering_data()
        config = data['config']
        config.update({
            'asign_enabled': self.asign_enabled,
            'asign_state': self.asign_state,
            'asign_method': self.asign_method
        })
        return data

    def _asign_dep_create(self, dep_export):
        dep = {
            "Belege-Gruppe": [
                {
                    "Signaturzertifikat" : "",
                    "Zertifizierungsstellen" : [],
                    "Belege-kompakt" : dep_export
                }
            ]
        }
        return dep

    def _asign_dep_export(self):
        self.ensure_one()

        dep_export = [
            r['asign_dep'] for r in self.env['pos.order'].search_read([
                    ('config_id', '=', self.id),
                    ('asign_state', '=', 's')
                ], ['asign_dep'], order="asign_seq asc")
        ]

        return self._asign_dep_create(dep_export)





