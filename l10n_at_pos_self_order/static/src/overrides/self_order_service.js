/** @odoo-module */

import { SelfOrder } from "@pos_self_order/app/self_order_service";
import { patch } from "@web/core/utils/patch";
import { qrCodeSrc } from "@point_of_sale/utils";


patch(SelfOrder.prototype, {

    export_for_printing(order) {
        var res = super.export_for_printing(...arguments);
        if (order.asign_state !== undefined) {
            res.asign_state = order.asign_state;
            res.asign_serial = order.asign_serial;
            res.asign_qrcode = order.asign_qrcode;
            res.asign_type = order.asign_type;
            res.asign_ref = order.asign_ref;
            if (order.asign_state === 's') {
                res.asign_qrcode_img = qrCodeSrc(order.asign_qrcode);
            }
        }
        return res;
    }

});