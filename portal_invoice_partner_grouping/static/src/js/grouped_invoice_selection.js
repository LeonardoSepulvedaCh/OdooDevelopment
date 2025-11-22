/** @odoo-module **/
/**
 * Extends invoice bulk selection to support grouped invoices by partner
 * Handles "Select All" per partner group
 */

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class GroupedInvoiceSelection extends Interaction {
    static selector = ".o_invoice_bulk_controls";

    setup() {
        // Clear all selections on page load
        this.clearAllSelectionsOnLoad();
        
        // Wait for parent interaction to initialize
        setTimeout(() => {
            this.setupGroupedListeners();
            this.initializeTooltips();
        }, 100);
    }
    
    /**
     * Inicializa los tooltips para los iconos de estado
     * Usa el sistema nativo de tooltips de Odoo/Bootstrap
     */
    initializeTooltips() {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        
        // Intentar usar Bootstrap si está disponible globalmente
        if (typeof window.bootstrap !== 'undefined' && window.bootstrap.Tooltip) {
            [...tooltipTriggerList].forEach(tooltipTriggerEl => {
                new window.bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
        // Fallback: Los navegadores modernos muestran tooltips automáticamente con el atributo title
    }

    /**
     * Clear all checkbox selections when page loads
     * This prevents checkboxes from staying checked after pagination
     * @returns {void}
     */
    clearAllSelectionsOnLoad() {
        // Clear master checkbox
        const masterCheckbox = document.getElementById('master_select_all');
        if (masterCheckbox) {
            masterCheckbox.checked = false;
            masterCheckbox.indeterminate = false;
        }

        // Clear global "Select All" checkbox
        const globalSelectAll = document.getElementById('select_all_invoices');
        if (globalSelectAll) {
            globalSelectAll.checked = false;
            globalSelectAll.indeterminate = false;
        }

        // Clear all partner group "Select All" checkboxes
        const partnerCheckboxes = document.querySelectorAll('.select-all-partner');
        partnerCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
            checkbox.indeterminate = false;
        });

        // Clear all individual invoice checkboxes
        const invoiceCheckboxes = document.querySelectorAll('.invoice-checkbox');
        invoiceCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
    }

    /**
     * Setup event listeners for grouped invoice selection
     * @returns {void}
     */
    setupGroupedListeners() {
        // Handle master "Select All" checkbox
        const masterCheckbox = document.getElementById('master_select_all');
        if (masterCheckbox) {
            masterCheckbox.addEventListener('change', (e) => this.onMasterSelectAll(e));
        }

        // Handle "Select All" per partner group
        const selectAllPartnerCheckboxes = document.querySelectorAll('.select-all-partner');
        selectAllPartnerCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => this.onSelectAllPartner(e));
        });

        // Also add listener to global select all to handle grouped view
        const globalSelectAll = document.getElementById('select_all_invoices');
        if (globalSelectAll) {
            // Remove existing listeners and add our enhanced one
            const newCheckbox = globalSelectAll.cloneNode(true);
            globalSelectAll.parentNode.replaceChild(newCheckbox, globalSelectAll);
            newCheckbox.addEventListener('change', (e) => this.onGlobalSelectAll(e));
        }

        // Listen to individual checkbox changes to update partner "Select All"
        const invoiceCheckboxes = document.querySelectorAll('.invoice-checkbox');
        invoiceCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => this.onIndividualCheckboxChange());
        });
    }

    /**
     * Handle master "Select All" checkbox
     * This selects ALL invoices across all partner groups
     * @param {Event} event
     */
    onMasterSelectAll(event) {
        const isChecked = event.target.checked;
        
        // Select/deselect ALL checkboxes on the page
        
        // 1. Global select all (if exists in non-grouped view)
        const globalSelectAll = document.getElementById('select_all_invoices');
        if (globalSelectAll) {
            globalSelectAll.checked = isChecked;
        }

        // 2. All partner group checkboxes
        const partnerCheckboxes = document.querySelectorAll('.select-all-partner');
        partnerCheckboxes.forEach(checkbox => {
            checkbox.checked = isChecked;
        });

        // 3. All individual invoice checkboxes
        const invoiceCheckboxes = document.querySelectorAll('.invoice-checkbox');
        invoiceCheckboxes.forEach(checkbox => {
            checkbox.checked = isChecked;
            // Trigger change event to update parent interaction
            checkbox.dispatchEvent(new Event('change', { bubbles: true }));
        });
    }

    /**
     * Handle individual checkbox change to update partner group checkboxes
     * @returns {void}
     */
    onIndividualCheckboxChange() {
        // Update each partner group checkbox state
        const partnerCheckboxes = document.querySelectorAll('.select-all-partner');
        partnerCheckboxes.forEach(partnerCheckbox => {
            const partnerId = partnerCheckbox.dataset.partnerId;
            const partnerInvoices = document.querySelectorAll(
                `.invoice-checkbox[data-partner-id="${partnerId}"]`
            );
            const checkedInvoices = document.querySelectorAll(
                `.invoice-checkbox[data-partner-id="${partnerId}"]:checked`
            );

            if (partnerInvoices.length === 0) {
                partnerCheckbox.checked = false;
                partnerCheckbox.indeterminate = false;
            } else if (checkedInvoices.length === partnerInvoices.length) {
                partnerCheckbox.checked = true;
                partnerCheckbox.indeterminate = false;
            } else if (checkedInvoices.length > 0) {
                partnerCheckbox.checked = false;
                partnerCheckbox.indeterminate = true;
            } else {
                partnerCheckbox.checked = false;
                partnerCheckbox.indeterminate = false;
            }
        });

        // Update global "Select All" state
        this.updateGlobalSelectAll();
        
        // Update master checkbox state
        this.updateMasterCheckbox();
    }

    /**
     * Update master checkbox state based on all selections
     * @returns {void}
     */
    updateMasterCheckbox() {
        const masterCheckbox = document.getElementById('master_select_all');
        if (!masterCheckbox) return;

        const allCheckboxes = document.querySelectorAll('.invoice-checkbox');
        const checkedCheckboxes = document.querySelectorAll('.invoice-checkbox:checked');

        if (allCheckboxes.length === 0) {
            masterCheckbox.checked = false;
            masterCheckbox.indeterminate = false;
        } else if (checkedCheckboxes.length === allCheckboxes.length) {
            masterCheckbox.checked = true;
            masterCheckbox.indeterminate = false;
        } else if (checkedCheckboxes.length > 0) {
            masterCheckbox.checked = false;
            masterCheckbox.indeterminate = true;
        } else {
            masterCheckbox.checked = false;
            masterCheckbox.indeterminate = false;
        }
    }

    /**
     * Handle global "Select All" for both grouped and non-grouped views
     * @param {Event} event
     */
    onGlobalSelectAll(event) {
        const isChecked = event.target.checked;
        
        // Select/deselect all invoice checkboxes
        const checkboxes = document.querySelectorAll('.invoice-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = isChecked;
            // Trigger change event to update parent interaction
            checkbox.dispatchEvent(new Event('change', { bubbles: true }));
        });

        // Also update all partner group checkboxes
        const partnerCheckboxes = document.querySelectorAll('.select-all-partner');
        partnerCheckboxes.forEach(checkbox => {
            checkbox.checked = isChecked;
        });
    }

    /**
     * Handle "Select All" for a specific partner group
     * @param {Event} event
     */
    onSelectAllPartner(event) {
        const checkbox = event.target;
        const isChecked = checkbox.checked;
        const partnerId = checkbox.dataset.partnerId;
        
        // Find all invoice checkboxes for this partner
        const partnerInvoices = document.querySelectorAll(
            `.invoice-checkbox[data-partner-id="${partnerId}"]`
        );
        
        // Select/deselect all invoices in this group
        partnerInvoices.forEach(invoiceCheckbox => {
            invoiceCheckbox.checked = isChecked;
            // Trigger change event to update parent interaction
            invoiceCheckbox.dispatchEvent(new Event('change', { bubbles: true }));
        });

        // Update global "Select All" state
        this.updateGlobalSelectAll();
    }

    /**
     * Update global "Select All" checkbox state based on individual selections
     * @returns {void}
     */
    updateGlobalSelectAll() {
        const globalSelectAll = document.getElementById('select_all_invoices');
        if (!globalSelectAll) return;

        const allCheckboxes = document.querySelectorAll('.invoice-checkbox');
        const checkedCheckboxes = document.querySelectorAll('.invoice-checkbox:checked');

        if (allCheckboxes.length === 0) {
            globalSelectAll.checked = false;
            globalSelectAll.indeterminate = false;
        } else if (checkedCheckboxes.length === allCheckboxes.length) {
            globalSelectAll.checked = true;
            globalSelectAll.indeterminate = false;
        } else if (checkedCheckboxes.length > 0) {
            globalSelectAll.checked = false;
            globalSelectAll.indeterminate = true;
        } else {
            globalSelectAll.checked = false;
            globalSelectAll.indeterminate = false;
        }
    }
}

registry
    .category("public.interactions")
    .add("portal_invoice_partner_grouping.grouped_selection", GroupedInvoiceSelection);

