import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";

patch(ProductScreen.prototype, {
  /**
   * Obtiene el precio con impuestos incluidos del producto para mostrarlo en la tarjeta
   */
  getProductPrice(product) {
    if (!product) {
      return "$ 0.00";
    }

    try {
      // Obtener el precio base del producto
      const pricelist = this.pos.config.pricelist_id;
      const basePrice = product.getPrice(pricelist, 1, 0, false, false);

      // Obtener la posición fiscal del partner actual o null
      const order = this.currentOrder || this.pos.selectedOrder;
      const fiscalPosition = order ? order.fiscal_position_id : null;

      // Calcular el precio con impuestos usando el sistema de impuestos de Odoo
      const taxDetails = product.getTaxDetails({
        overridedValues: {
          price: basePrice,
          pricelist: pricelist,
          fiscalPosition: fiscalPosition,
        },
      });

      // El precio total con impuestos está en total_included
      const priceWithTaxes = taxDetails.total_included;

      // Formatear el precio con la moneda
      return this.env.utils.formatCurrency(priceWithTaxes);
    } catch (error) {
      console.error(
        "Error al obtener precio con impuestos del producto:",
        error
      );
      // Fallback: calcular precio con impuestos de forma simplificada
      try {
        const pricelist = this.pos.config.pricelist_id;
        const basePrice = product.getPrice(pricelist, 1, 0, false, false);

        // Obtener los impuestos del producto
        const taxes = product.taxes_id;
        let totalTaxRate = 0;

        // Sumar las tasas de impuestos
        for (const tax of taxes) {
          if (tax.amount_type === "percent") {
            totalTaxRate += tax.amount;
          }
        }

        // Calcular precio con impuestos
        const priceWithTaxes = basePrice * (1 + totalTaxRate / 100);
        return this.env.utils.formatCurrency(priceWithTaxes);
      } catch (fallbackError) {
        console.error("Error en fallback:", fallbackError);
        // Último recurso: usar list_price
        if (product.list_price !== undefined) {
          return this.env.utils.formatCurrency(product.list_price);
        }
        return "$ 0.00";
      }
    }
  },

  /**
   * Extiende getProductName para también agregar el precio formateado al producto
   */
  getProductName(product) {
    // Agregar el precio formateado al objeto producto para que esté disponible en la plantilla
    if (product && !product.priceFormatted) {
      product.priceFormatted = this.getProductPrice(product);
    }
    return super.getProductName(product);
  },
});
