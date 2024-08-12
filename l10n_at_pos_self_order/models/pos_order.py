from odoo import models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _export_for_self_order(self):
        res = super()._export_for_self_order()

        if (self.asign_state != 's'
                and self.state == 'paid'
                and self.session_id.config_id.asign_enabled):
            self.asign_state = 'u'
            self._asign_add_signature()

        res.update({
            'asign_type': self.asign_type,
            'asign_state': self.asign_state,
            'asign_qrcode': self.asign_qrcode,
            'asign_serial': self.asign_serial,
            'asign_ref': self.name
        })
        return res