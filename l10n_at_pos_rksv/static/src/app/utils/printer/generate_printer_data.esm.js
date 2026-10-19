// Copyright 2026 Weboffice IT-Service und Marketing GmbH & Co KG <https://weboffice.at>
// License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import {GeneratePrinterData} from "@point_of_sale/app/utils/printer/generate_printer_data";
import {patch} from "@web/core/utils/patch";

// JS copy of receipt/pos_order_receipt.py
patch(GeneratePrinterData.prototype, {
    generateReceiptData() {
        const data = super.generateReceiptData(...arguments);
        const order = this.order;
        if (order.asign_state) {
            data.conditions.l10n_at_pos_rksv = true;
            if (order.asign_state === "s" && order.asign_qrcode) {
                data.image.asign_qr_code = this.generateQrCode(order.asign_qrcode);
            }
        }
        return data;
    },
});
