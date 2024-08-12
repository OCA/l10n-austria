from odoo import models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    def action_open_wizard(self):
        self.ensure_one()
        if not self.current_session_id:
            self._check_asign_before_creating_new_session()
        return super().action_open_wizard()
