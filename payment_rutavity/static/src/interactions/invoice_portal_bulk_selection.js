/** @odoo-module **/
/**
 * Author: Sebastián Rodríguez
 * 
 * Handles invoice bulk selection and payment flow on existing invoice list.
 */

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class InvoiceBulkSelection extends Interaction {
    static selector = ".o_invoice_bulk_controls";

    setup() {
        this.selectedInvoices = new Map(); // Store {id: {amount, currencySymbol}}
        
        // Clear all checkboxes on page load to ensure clean state
        this.clearAllSelections();
        
        // Bind event listeners
        this.setupEventListeners();
    }

    /**
     * Clear all checkbox selections and reset state
     * @returns {void}
     */
    clearAllSelections() {
        // Uncheck all invoice checkboxes
        const checkboxes = document.querySelectorAll('.invoice-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        
        // Uncheck select all checkbox
        const selectAllCheckbox = document.getElementById('select_all_invoices');
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = false;
        }
        
        // Clear selected invoices map
        this.selectedInvoices.clear();
        
        // Hide summary bar
        const bulkSummary = document.getElementById('bulk_payment_summary');
        if (bulkSummary) {
            bulkSummary.classList.add('d-none');
        }
    }

    /**
     * Setup all event listeners for bulk invoice selection
     * @returns {void}
     */
    setupEventListeners() {
        // Select all checkbox
        const selectAllCheckbox = document.getElementById('select_all_invoices');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', (e) => this.onSelectAll(e));
        }

        // Individual invoice checkboxes
        const checkboxes = document.querySelectorAll('.invoice-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => this.onInvoiceSelect(e));
        });

        // Proceed to payment button
        const proceedBtn = this.el.querySelector('#proceed_bulk_payment_btn');
        if (proceedBtn) {
            proceedBtn.addEventListener('click', () => this.onProceedToPayment());
        }
    }

    /**
     * Handle select all checkbox change
     * @param {Event} event
     */
    onSelectAll(event) {
        const isChecked = event.target.checked;
        const checkboxes = document.querySelectorAll('.invoice-checkbox');
        
        checkboxes.forEach(checkbox => {
            checkbox.checked = isChecked;
            const invoiceId = parseInt(checkbox.value);
            const amount = parseFloat(checkbox.dataset.amount);
            const currencySymbol = checkbox.dataset.currencySymbol;
            
            if (isChecked) {
                this.selectedInvoices.set(invoiceId, { amount, currencySymbol });
            } else {
                this.selectedInvoices.delete(invoiceId);
            }
        });
        
        this.updateSummary();
    }

    /**
     * Handle individual invoice checkbox change
     * @param {Event} event
     */
    onInvoiceSelect(event) {
        const checkbox = event.target;
        const invoiceId = parseInt(checkbox.value);
        const amount = parseFloat(checkbox.dataset.amount);
        const currencySymbol = checkbox.dataset.currencySymbol;
        
        if (checkbox.checked) {
            this.selectedInvoices.set(invoiceId, { amount, currencySymbol });
        } else {
            this.selectedInvoices.delete(invoiceId);
            // Uncheck select all if any invoice is unchecked
            const selectAllCheckbox = document.getElementById('select_all_invoices');
            if (selectAllCheckbox) {
                selectAllCheckbox.checked = false;
            }
        }
        
        this.updateSummary();
    }

    /**
     * Update bulk payment summary
     * @returns {void}
     */
    updateSummary() {
        const selectedCount = this.selectedInvoices.size;
        const totalAmount = this.calculateTotalAmount();
        const currencySymbol = this.getCurrencySymbol();
        
        // Update selected count
        const countElement = document.getElementById('selected_invoice_count');
        if (countElement) {
            countElement.textContent = selectedCount;
        }
        
        // Update total amount
        const amountElement = document.getElementById('bulk_total_amount');
        if (amountElement) {
            amountElement.textContent = this.formatCurrency(totalAmount, currencySymbol);
        }
        
        // Show/hide summary bar based on selection
        const bulkSummary = document.getElementById('bulk_payment_summary');
        if (bulkSummary) {
            if (selectedCount > 0) {
                bulkSummary.classList.remove('d-none');
            } else {
                bulkSummary.classList.add('d-none');
            }
        }
    }

    /**
     * Calculate total amount of selected invoices
     * @returns {number}
     */
    calculateTotalAmount() {
        let total = 0;
        this.selectedInvoices.forEach((data) => {
            total += data.amount;
        });
        return total;
    }

    /**
     * Get currency symbol from selected invoices
     * @returns {string}
     */
    getCurrencySymbol() {
        // Get from first selected invoice
        for (const [id, data] of this.selectedInvoices) {
            return data.currencySymbol;
        }
        return '$'; // fallback
    }

    /**
     * Format currency value
     * @param {number} amount
     * @param {string} currencySymbol
     * @returns {string}
     */
    formatCurrency(amount, currencySymbol) {
        const formatted = new Intl.NumberFormat('es-CO', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(amount);
        
        return `${currencySymbol} ${formatted}`;
    }

    /**
     * Handle proceed to payment button click
     * @returns {void}
     */
    onProceedToPayment() {
        if (this.selectedInvoices.size === 0) {
            return;
        }
        
        // Convert Map keys to comma-separated string
        const invoiceIds = Array.from(this.selectedInvoices.keys()).join(',');
        
        // Redirect to overdue invoices payment page with selected invoice IDs
        window.location.href = `/my/invoices/overdue?invoice_ids=${invoiceIds}`;
    }
}

registry
    .category("public.interactions")
    .add("payment_rutavity.invoice_bulk_selection", InvoiceBulkSelection);
