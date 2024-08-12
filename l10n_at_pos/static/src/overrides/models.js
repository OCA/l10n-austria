/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { qrCodeSrc } from "@point_of_sale/utils";


patch(Order.prototype, {
    // @Override for initial setup of asign
    setup() {
        super.setup(...arguments);
        if (this.pos.config.asign_enabled && this.pos.config.asign_state != 'draft') {
            this.asign_state = this.asign_state || 'u';
            this.asign_serial = this.asign_serial || '';
            this.asign_qrcode = this.asign_qrcode || '';
            this.asign_type = this.asign_type || '';
            this.asign_ref = this.asign_ref || '';
            this.save_to_db();
        }
    },

    export_as_JSON() {
        var json = super.export_as_JSON();
        if (this.asign_state !== undefined) {
            json.asign_state = this.asign_state;
            json.asign_serial = this.asign_serial;
            json.asign_qrcode = this.asign_qrcode;
            json.asign_type = this.asign_type;
            json.asign_ref = this.asign_ref;
        }
        return json;
    },

    export_for_printing() {
        var json = super.export_for_printing();
        if (this.asign_state !== undefined) {
            json.asign_state = this.asign_state;
            json.asign_serial = this.asign_serial;
            json.asign_qrcode = this.asign_qrcode;
            json.asign_type = this.asign_type;
            json.asign_ref = this.asign_ref;
            if (this.asign_state === 's') {
                json.asign_qrcode_img = qrCodeSrc(this.asign_qrcode);
            }
        }
        return json;
    }
});


patch(PosStore.prototype, {

    async _save_to_server(orders, options) {
        const serverIds = await super._save_to_server(orders, options);
        if ( !options.draft ) {
            for (const serverId of serverIds) {
                const order = this.env.services.pos.orders.find(
                    (order) => order.name === serverId.pos_reference
                );
                if (order && serverId.asign_state === 's') {
                    order.asign_state = serverId.asign_state;
                    order.asign_serial = serverId.asign_serial;
                    order.asign_type = serverId.asign_type;
                    order.asign_qrcode = serverId.asign_qrcode;
                    order.asign_ref = serverId.asign_ref;
                };
            }
        }
        return serverIds
    }
});