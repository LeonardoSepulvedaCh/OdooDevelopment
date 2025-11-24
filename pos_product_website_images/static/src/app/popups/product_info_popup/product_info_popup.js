import { ProductInfoPopup } from "@point_of_sale/app/components/popups/product_info_popup/product_info_popup";
import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";

/**
 * Extiende el ProductInfoPopup para mostrar las imágenes del sitio web
 * asociadas al producto.
 */
patch(ProductInfoPopup.prototype, {
  setup() {
    super.setup();
    // Estado para controlar qué imagen se está mostrando actualmente
    this.imageState = useState({
      currentImageIndex: 0,
    });
  },

  /**
   * Obtiene la lista de imágenes del producto desde la información cargada
   */
  get productImages() {
    return this.props.info?.productInfo?.product_images || [];
  },

  /**
   * Verifica si el producto tiene imágenes adicionales para mostrar
   */
  get hasImages() {
    return this.productImages.length > 0;
  },

  /**
   * Obtiene la imagen actual que se está mostrando
   */
  get currentImage() {
    if (this.hasImages) {
      return this.productImages[this.imageState.currentImageIndex];
    }
    return null;
  },

  /**
   * Navega a la siguiente imagen en la galería
   */
  nextImage() {
    if (this.hasImages) {
      this.imageState.currentImageIndex =
        (this.imageState.currentImageIndex + 1) % this.productImages.length;
    }
  },

  /**
   * Navega a la imagen anterior en la galería
   */
  previousImage() {
    if (this.hasImages) {
      this.imageState.currentImageIndex =
        (this.imageState.currentImageIndex - 1 + this.productImages.length) %
        this.productImages.length;
    }
  },

  /**
   * Selecciona una imagen específica por su índice
   */
  selectImage(index) {
    this.imageState.currentImageIndex = index;
  },
});
