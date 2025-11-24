/** @odoo-module */

import { ProductTemplate } from "@point_of_sale/app/models/product_template";
import { patch } from "@web/core/utils/patch";
import { markup } from "@odoo/owl";

/**
 * Extiende ProductTemplate para usar description_ecommerce como fallback
 * si no hay public_description disponible.
 */
patch(ProductTemplate.prototype, {
  get productDescriptionMarkup() {
    // Si hay public_description, usarla
    if (this.public_description) {
      return markup(this.public_description);
    }
    // Si no hay public_description pero sí description_ecommerce, usarla como fallback
    if (this.description_ecommerce) {
      return markup(this.description_ecommerce);
    }
    // Si no hay ninguna, retornar vacío
    return "";
  },
});

