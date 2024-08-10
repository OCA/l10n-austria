import re
from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    asign_enabled = fields.Boolean(compute='_compute_asign', inverse='_inverse_asign')

    asign_method = fields.Selection([('card', 'Card'),
                                     ('online', 'Online')], compute='_compute_asign', inverse='_inverse_asign')

    asign_state = fields.Selection([('draft', 'Draft'),
                                    ('assigned', 'Assigned'),
                                    ('active', 'Active')], compute='_compute_asign')

    asign_serial_hex = fields.Char('a.sign Serial', help="Serial number of the certificate in hex format.",
                                   compute='_compute_asign', inverse='_inverse_asign')

    asign_fid = fields.Char(compute='_compute_asign', inverse='_inverse_asign')
    asign_pid = fields.Char(compute='_compute_asign', inverse='_inverse_asign')
    asign_key = fields.Char(compute='_compute_asign', inverse='_inverse_asign')
    asign_crc = fields.Char(compute='_compute_asign', readonly=True)

    @api.onchange('asign_enabled')
    def _onchange_asign_enabled(self):
        self.env['pos.config']._set_asign_defaults(self)

    @api.depends('pos_config_id')
    def _compute_asign(self):
        for record in self:
            config = record.pos_config_id
            record.asign_enabled = config.asign_enabled
            record.asign_method = config.asign_method
            record.asign_state = config.asign_state
            record.asign_serial_hex = config.asign_serial_hex
            record.asign_fid = config.asign_fid
            record.asign_pid = config.asign_pid
            record.asign_key = config.asign_key
            record.asign_crc = config.asign_crc

    def _inverse_asign(self):
        ''' normalize hex string to lowercase '''
        for record in self:
            config = record.pos_config_id
            if config:
                update = {
                    'asign_enabled': record.asign_enabled
                }

                # only allow update if state is draft
                if not record.asign_state or record.asign_state == 'draft':

                    # update basic fields
                    update.update({
                        'asign_enabled': record.asign_enabled,
                        'asign_method': record.asign_method,
                        'asign_fid': record.asign_fid,
                        'asign_key': record.asign_key
                    })

                    # add serial hex
                    if record.asign_serial_hex:
                        update['asign_serial_hex'] = f'{int(record.asign_serial_hex, 16):x}'

                    # remove all non-alphanumeric characters
                    fiscal_pid = record.asign_pid
                    if fiscal_pid:
                        fiscal_pid = re.sub('[^0-9A-Za-z]', '', fiscal_pid)

                    # not override if asign_pid is empty
                    if fiscal_pid:
                        update['asign_pid'] = fiscal_pid
                        config.sequence_id.name = fiscal_pid
                        config.sequence_id.prefix = f'{fiscal_pid}/'
                        config.sequence_id.suffix = None

                # write update
                if update:
                    config.write(update)


    def action_asign_assign(self):
        self.pos_config_id.action_asign_assign()

    def action_asign_reset(self):
        self.pos_config_id.action_asign_reset()

