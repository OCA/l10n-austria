# Copyright 2026 Weboffice IT-Service und Marketing GmbH & Co KG <https://weboffice.at>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import models


class PosSession(models.Model):
    _inherit = "pos.session"

    def close_session_from_ui(self, payment_method_closing=None):
        # Odoo 20 closes sessions only here, action_pos_session_close is gone
        res = super().close_session_from_ui(payment_method_closing or {})
        # Trigger the sign-missed cron so cancelled or missed receipts are
        # signed right after closing without blocking or delaying the close.
        if (
            res.get("status")
            and self.config_id.asign_enabled
            and self.config_id.asign_state != "draft"
        ):
            self.env.ref("l10n_at_pos_rksv.pos_config_ir_cron")._trigger()
        return res
