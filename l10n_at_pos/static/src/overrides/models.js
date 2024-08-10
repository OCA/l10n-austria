/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    // @Override for initial setup of asign
    setup() {
        super.setup(...arguments);
        if (this.pos.config.asign_enabled) {
            this.asign_state = this.asign_state || 'u';
            this.save_to_db();
        }
    },

    export_as_JSON() {
        var json = super.export_as_JSON();
        if (this.asign_state !== undefined) {
            json.asign_state = this.asign_state;
        }
        return json;
    },

    export_for_printing() {
        debugger;
        var json = super.export_for_printing();
        if (this.asign_state !== undefined) {
            json.asign_state = this.asign_state;
        }
        return json;
    }
});