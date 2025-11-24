import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
  setup() {
    super.setup(...arguments);
    this.currentProductPage = 1;
  },

  /**
   * Obtiene el número de productos por página desde la configuración
   */
  get productsPerPage() {
    // Usar el valor configurado en pos.config, o 20 por defecto
    return this.config.products_per_page || 20;
  },

  /**
   * Obtiene la lista base de productos según búsqueda o categoría
   * @private
   */
  _getBaseProductList(searchWord, allProducts) {
    const isSearchByWord = searchWord !== "";

    if (isSearchByWord) {
      if (!this._searchTriggered) {
        this.setSelectedCategory(0);
        this._searchTriggered = true;
      }
      return this.getProductsBySearchWord(
        searchWord,
        this.selectedCategory?.id
          ? this.selectedCategory.associatedProducts
          : allProducts
      );
    }

    this._searchTriggered = false;
    if (this.selectedCategory?.id) {
      return this.selectedCategory.associatedProducts;
    }
    return allProducts;
  },

  /**
   * Verifica si un producto debe ser incluido en la lista
   * @private
   */
  _shouldIncludeProduct(product, excludedProductIds, availableCateg) {
    // Verificar si está excluido o no puede ser mostrado
    if (excludedProductIds.has(product.id) || !product.canBeDisplayed) {
      return false;
    }

    // Verificar restricciones de categorías
    if (availableCateg.size) {
      const isSpecialProduct =
        this.config._pos_special_display_products_ids?.includes(product.id);
      const hasValidCategory = product.pos_categ_ids.some((c) =>
        availableCateg.has(c.id)
      );

      if (!isSpecialProduct && !hasValidCategory) {
        return false;
      }
    }

    return true;
  },

  /**
   * Filtra la lista de productos aplicando exclusiones y categorías
   * @private
   */
  _filterProducts(list) {
    const excludedProductIds = new Set(this.getExcludedProductIds());
    const availableCateg = new Set(
      (this.config.iface_available_categ_ids || []).map((c) => c.id)
    );

    return list.filter((product) =>
      this._shouldIncludeProduct(product, excludedProductIds, availableCateg)
    );
  },

  /**
   * Ordena los productos según el contexto (búsqueda o navegación)
   * @private
   */
  _sortProducts(products, isSearchByWord) {
    if (isSearchByWord) {
      // En búsqueda: ordenar por favoritos primero
      return products.sort((a, b) => b.is_favorite - a.is_favorite);
    }

    // Sin búsqueda: ordenar por productos más vendidos
    return products.sort((a, b) => {
      // Primero por favoritos
      if (b.is_favorite !== a.is_favorite) {
        return b.is_favorite - a.is_favorite;
      }
      // Luego por cantidad vendida (más vendidos primero)
      const qtyDiff = (b.pos_total_qty_sold || 0) - (a.pos_total_qty_sold || 0);
      if (qtyDiff !== 0) {
        return qtyDiff;
      }
      // Luego por secuencia
      if (a.pos_sequence !== b.pos_sequence) {
        return a.pos_sequence - b.pos_sequence;
      }
      // Finalmente por nombre
      return a.name.localeCompare(b.name);
    });
  },

  /**
   * Obtiene los productos a mostrar con paginación aplicada
   */
  get productsToDisplay() {
    const searchWord = this.searchProductWord.trim();
    const allProducts = this.models["product.template"].getAll();
    const isSearchByWord = searchWord !== "";

    // Obtener la lista base según búsqueda o categoría
    const list = this._getBaseProductList(searchWord, allProducts);

    if (!list || list.length === 0) {
      return [];
    }

    // Aplicar filtros de exclusión y categorías disponibles
    const filteredList = this._filterProducts(list);

    // Verificar si todos los productos son especiales (sin búsqueda ni categoría)
    if (
      !isSearchByWord &&
      !this.selectedCategory?.id &&
      this.areAllProductsSpecial(filteredList)
    ) {
      return [];
    }

    // Ordenar y retornar productos
    return this._sortProducts(filteredList, isSearchByWord);
  },

  /**
   * Retorna los productos de la página actual
   */
  get paginatedProducts() {
    const allProducts = this.productsToDisplay;
    const startIdx = (this.currentProductPage - 1) * this.productsPerPage;
    const endIdx = startIdx + this.productsPerPage;
    return allProducts.slice(startIdx, endIdx);
  },

  /**
   * Retorna el total de páginas
   */
  get totalProductPages() {
    const total = this.productsToDisplay.length;
    if (total === 0) {
      return 0;
    }
    return Math.ceil(total / this.productsPerPage);
  },

  /**
   * Retorna si hay página anterior
   */
  get hasPreviousPage() {
    return this.currentProductPage > 1;
  },

  /**
   * Retorna si hay página siguiente
   */
  get hasNextPage() {
    return this.currentProductPage < this.totalProductPages;
  },

  /**
   * Va a la página anterior
   */
  previousProductPage() {
    if (this.hasPreviousPage) {
      this.currentProductPage--;
    }
  },

  /**
   * Va a la página siguiente
   */
  nextProductPage() {
    if (this.hasNextPage) {
      this.currentProductPage++;
    }
  },

  /**
   * Reinicia la paginación a la primera página
   */
  resetProductPage() {
    this.currentProductPage = 1;
  },

  /**
   * Override para usar productos paginados
   */
  get productToDisplayByCateg() {
    const sortedProducts = this.paginatedProducts;

    // Si está configurado para agrupar por categoría
    if (this.config.iface_group_by_categ) {
      const groupedByCategory = {};
      for (const product of sortedProducts) {
        for (const categ of product.pos_categ_ids) {
          if (!groupedByCategory[categ.id]) {
            groupedByCategory[categ.id] = [];
          }
          groupedByCategory[categ.id].push(product);
        }
      }
      const res = Object.entries(groupedByCategory).sort(([a], [b]) => {
        const catA = this.models["pos.category"].get(a);
        const catB = this.models["pos.category"].get(b);

        const isRootA = !catA.parent_id;
        const isRootB = !catB.parent_id;

        // Si una es root y la otra no, la root va primero
        if (isRootA !== isRootB) {
          return isRootA ? -1 : 1;
        }

        // Si ambas son del mismo nivel, ordenar por secuencia
        return catA.sequence - catB.sequence;
      });
      return res;
    }

    // Sin agrupación por categoría, retornar lista plana
    return sortedProducts.length ? [[0, sortedProducts]] : [];
  },
});
