from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    asign_enabled = fields.Boolean(related='pos_config_id.asign_enabled', readonly=False)
    asign_method = fields.Selection(related='pos_config_id.asign_method', readonly=False)
    asign_state = fields.Selection(related='pos_config_id.asign_state', readonly=False)

