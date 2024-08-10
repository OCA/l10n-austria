/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    // @Override for initial setup of asign
    setup() {
        super.setup(...arguments);
        if (this.pos.config.asign_enabled) {
            this.asign = this.asign || 'u';
            this.save_to_db();
        }
    }
});