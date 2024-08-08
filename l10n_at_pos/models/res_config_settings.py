import re
from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    asign_enabled = fields.Boolean(related='pos_config_id.asign_enabled', readonly=False)
    asign_method = fields.Selection(related='pos_config_id.asign_method', readonly=False)
    asign_state = fields.Selection(related='pos_config_id.asign_state', readonly=True)
    asign_serial_hex = fields.Char('a.sign Serial', help="Serial number of the certificate in hex format.",
                                   compute='_compute_asign', inverse='_inverse_asign_serial_hex')

    asign_fid = fields.Char(related='pos_config_id.asign_fid', readonly=False)
    asign_pid = fields.Char(compute='_compute_asign', inverse='_inverse_asign_pid')
    asign_key = fields.Char(related='pos_config_id.asign_key', readonly=False)
    asign_crc = fields.Char(related='pos_config_id.asign_crc', readonly=True)


    @api.depends('pos_config_id')
    def _compute_asign(self):
        for record in self:
            config = record.pos_config_id
            record.asign_serial_hex = config.asign_serial_hex
            record.asign_pid = config.asign_pid

    def _inverse_asign_serial_hex(self):
        ''' normalize hex string to lowercase '''
        for record in self:
            if record.asign_serial_hex:
                record.pos_config_id.asign_serial_hex = f'{int(record.asign_serial_hex, 16):x}'
            else:
                record.asign_serial_hex = ''

    def _inverse_asign_pid(self):
        ''' update sequence to fiscal POS ID'''
        for record in self:
            config = record.pos_config_id
            if config:
                fiscal_pos_id = record.asign_pid
                # remove all non-alphanumeric characters
                if fiscal_pos_id:
                    fiscal_pos_id = re.sub('[^0-9A-Za-z]', '', fiscal_pos_id)
                config.asign_pid = fiscal_pos_id
                # not override if asign_pid is empty
                if fiscal_pos_id:
                    config.sequence_id.name = record.asign_pid
                    config.sequence_id.prefix = f'{record.asign_pid}/'
                    config.sequence_id.postfix = None

    def action_asign_assign(self):
        self.pos_config_id.action_asign_assign()

    def action_asign_reset(self):
        self.pos_config_id.action_asign_reset()

