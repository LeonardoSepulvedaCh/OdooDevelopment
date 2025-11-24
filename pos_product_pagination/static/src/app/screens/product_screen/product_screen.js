import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { useEffect } from "@odoo/owl";

patch(ProductScreen.prototype, {
  setup() {
    super.setup(...arguments);

    // Resetear la página cuando cambia la categoría o la búsqueda
    useEffect(
      () => {
        this.pos.resetProductPage();
      },
      () => [this.pos.selectedCategory, this.pos.searchProductWord]
    );

    // Ajustar la página actual si es mayor que el total de páginas
    useEffect(
      () => {
        const totalPages = this.pos.totalProductPages;
        if (totalPages > 0 && this.pos.currentProductPage > totalPages) {
          this.pos.currentProductPage = totalPages;
        }
      },
      () => [this.pos.totalProductPages]
    );
  },

  /**
   * Navega a la página anterior de productos
   */
  goToPreviousPage() {
    this.pos.previousProductPage();
  },

  /**
   * Navega a la página siguiente de productos
   */
  goToNextPage() {
    this.pos.nextProductPage();
  },

  /**
   * Retorna la información de paginación para mostrar en la UI
   */
  get paginationInfo() {
    const totalProducts = this.pos.productsToDisplay.length;
    const totalPages = this.pos.totalProductPages;

    // Si no hay productos, retornar valores en cero
    if (totalProducts === 0 || totalPages === 0) {
      return {
        currentPage: 0,
        totalPages: 0,
        hasPrevious: false,
        hasNext: false,
        totalProducts: 0,
        startProduct: 0,
        endProduct: 0,
      };
    }

    return {
      currentPage: this.pos.currentProductPage,
      totalPages: totalPages,
      hasPrevious: this.pos.hasPreviousPage,
      hasNext: this.pos.hasNextPage,
      totalProducts: totalProducts,
      startProduct:
        (this.pos.currentProductPage - 1) * this.pos.productsPerPage + 1,
      endProduct: Math.min(
        this.pos.currentProductPage * this.pos.productsPerPage,
        totalProducts
      ),
    };
  },
});
