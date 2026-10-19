# Copyright 2026 Weboffice IT-Service und Marketing GmbH & Co KG <https://weboffice.at>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import models


class PosOrderReceipt(models.AbstractModel):
    _inherit = "pos.order.receipt"

    def order_receipt_generate_data(self, basic_receipt=False):
        """Add the RKSV block data; the JS copy lives in
        ``static/src/app/utils/printer/generate_printer_data.js``."""
        data = super().order_receipt_generate_data(basic_receipt)
        if self.asign_state:
            data["conditions"]["l10n_at_pos_rksv"] = True
            if self.asign_state == "s" and self.asign_qrcode:
                data["image"]["asign_qr_code"] = self._order_receipt_generate_qr_code(
                    self.asign_qrcode
                )
        return data
