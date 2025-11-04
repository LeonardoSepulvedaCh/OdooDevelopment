import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

// Interacción para cargar dinámicamente facturas y productos en formularios de garantía
export class HelpdeskWarrantyFormLoader extends Interaction {
    static selector = "#helpdesk_warranty_ticket_form";
    
    dynamicContent = {
        "#warranty_invoice": {
            "t-on-change": this.onInvoiceChange,
        },
        'input[name="product_ids"]': {
            "t-on-change": this.onProductCheckboxChange,
        },
    };
    
    // Inicializar la interacción
    setup() {
        this.selectedProducts = [];
        this.loadInvoices();
    }
    
    // Cargar las facturas del usuario autenticado mediante JSON-RPC
    async loadInvoices() {
        const invoiceSelect = this.el.querySelector("#warranty_invoice");
        
        if (!invoiceSelect) {
            return;
        }
        
        invoiceSelect.innerHTML = '<option value="">Cargando facturas...</option>';
        invoiceSelect.disabled = true;
        
        try {
            const result = await rpc('/helpdesk/warranty/get_partner_invoices', {});
            
            if (result.error) {
                console.error('Error al cargar facturas:', result.error);
                invoiceSelect.innerHTML = '<option value="">Error al cargar facturas</option>';
                return;
            }
            
            invoiceSelect.innerHTML = '<option value="">Seleccione una factura</option>';
            
            if (result.invoices && result.invoices.length > 0) {
                result.invoices.forEach((invoice) => {
                    const option = document.createElement('option');
                    option.value = invoice.id;
                    option.textContent = invoice.display_name;
                    invoiceSelect.appendChild(option);
                });
                invoiceSelect.disabled = false;
            } else {
                invoiceSelect.innerHTML = '<option value="">No hay facturas disponibles</option>';
            }
        } catch (error) {
            console.error('Error en la llamada JSON-RPC:', error);
            invoiceSelect.innerHTML = '<option value="">Error al cargar facturas</option>';
        }
    }
    
    // Manejar el cambio de factura seleccionada
    onInvoiceChange(ev) {
        const invoiceId = ev.currentTarget.value;
        
        if (!invoiceId) {
            this.hideProducts();
            return;
        }
        
        this.loadProducts(invoiceId);
    }
    
    // Cargar los productos de una factura específica
    async loadProducts(invoiceId) {
        const productsField = this.el.querySelector("#warranty_products_field");
        const productsContainer = this.el.querySelector("#warranty_products_container");
        
        if (!productsField || !productsContainer) {
            return;
        }
        
        productsContainer.innerHTML = '<small class="text-muted">Cargando productos...</small>';
        productsField.style.display = 'block';
        
        this.selectedProducts = [];
        
        try {
            const result = await rpc('/helpdesk/warranty/get_invoice_products', {
                invoice_id: invoiceId
            });
            
            if (result.error) {
                console.error('Error al cargar productos:', result.error);
                productsContainer.innerHTML = '<small class="text-danger">Error al cargar productos</small>';
                return;
            }
            
            if (result.products && result.products.length > 0) {
                this.renderProducts(result.products);
            } else {
                productsContainer.innerHTML = '<small class="text-muted">Esta factura no tiene productos</small>';
            }
        } catch (error) {
            console.error('Error en la llamada JSON-RPC:', error);
            productsContainer.innerHTML = '<small class="text-danger">Error al cargar productos</small>';
        }
    }
    
    // Renderizar los productos como checkboxes
    renderProducts(products) {
        const productsContainer = this.el.querySelector("#warranty_products_container");
        
        if (!productsContainer) {
            return;
        }
        
        productsContainer.innerHTML = '';
        
        products.forEach((product) => {
            const checkboxId = `product_${product.id}`;
            
            const checkboxWrapper = document.createElement('div');
            checkboxWrapper.className = 'form-check mb-2';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = checkboxId;
            checkbox.name = 'product_ids';
            checkbox.value = product.id;
            checkbox.className = 'form-check-input';
            
            const label = document.createElement('label');
            label.htmlFor = checkboxId;
            label.className = 'form-check-label';
            
            const productCode = product.default_code 
                ? ` <span class="text-muted">(${product.default_code})</span>` 
                : '';
            
            label.innerHTML = `
                <strong>${product.name}</strong>
                ${productCode}
                <span class="text-muted"> - Cant: ${product.quantity}</span>
            `;
            
            checkboxWrapper.appendChild(checkbox);
            checkboxWrapper.appendChild(label);
            productsContainer.appendChild(checkboxWrapper);
        });
    }
    
    // Manejar el cambio en los checkboxes de productos
    onProductCheckboxChange() {
        this.selectedProducts = [];
        
        const checkedCheckboxes = this.el.querySelectorAll('input[name="product_ids"]:checked');
        checkedCheckboxes.forEach((checkbox) => {
            this.selectedProducts.push(checkbox.value);
        });
        
        const existingHiddenInputs = this.el.querySelectorAll('input[name="product_ids"][type="hidden"]');
        existingHiddenInputs.forEach((input) => input.remove());
        
        this.selectedProducts.forEach((productId) => {
            const hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.name = 'product_ids';
            hiddenInput.value = productId;
            this.el.appendChild(hiddenInput);
        });
    }
    
    // Ocultar el campo de productos
    hideProducts() {
        const productsField = this.el.querySelector("#warranty_products_field");
        const productsContainer = this.el.querySelector("#warranty_products_container");
        
        if (productsField) {
            productsField.style.display = 'none';
        }
        
        if (productsContainer) {
            productsContainer.innerHTML = '<small class="text-muted">Seleccione una factura primero</small>';
        }
        
        this.selectedProducts = [];
        
        const productInputs = this.el.querySelectorAll('input[name="product_ids"]');
        productInputs.forEach((input) => input.remove());
    }
}

// Interacción de validación para desactivar formularios de garantía
export class HelpdeskWarrantyFormValidation extends Interaction {
    static selector = "#helpdesk_ticket_form";
    
    dynamicContent = {
        _root: {
            "t-on-submit.prevent": (ev) => {
                if (this.isFormDisabled) {
                    ev.stopPropagation();
                    return false;
                }
            },
        },
    };
    
    setup() {
        this.isFormDisabled = this.el.classList.contains('o_warranty_form_disabled');
        
        if (this.isFormDisabled) {
            this.disableForm();
        }
    }
    
    disableForm() {
        const formElements = this.el.querySelectorAll('input, textarea, select, button');
        formElements.forEach((element) => {
            element.disabled = true;
        });
    }
}

// Registrar las interacciones en el registro de Odoo
registry
    .category("public.interactions")
    .add("helpdesk_custom_fields.warranty_form_loader", HelpdeskWarrantyFormLoader);

registry
    .category("public.interactions")
    .add("helpdesk_custom_fields.warranty_form_validation", HelpdeskWarrantyFormValidation);

export default {
    HelpdeskWarrantyFormLoader,
    HelpdeskWarrantyFormValidation,
};

