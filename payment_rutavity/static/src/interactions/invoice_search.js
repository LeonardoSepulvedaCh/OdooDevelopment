/**
 * Invoice Search Interaction
 * Handles the public invoice search form and results display
 */

import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class InvoiceSearchInteraction extends Interaction {
    static selector = "#invoice_search_form";

    /**
     * Setup event listeners and initial state
     */
    setup() {
        this.form = this.el;
        this.searchBtn = this.form.querySelector("#search_btn");
        this.invoiceNumbersInput = this.form.querySelector("#invoice_numbers");

        // UI elements
        this.loadingSpinner = document.querySelector("#loading_spinner");
        this.resultsContainer = document.querySelector("#results_container");

        // Bind form submit
        this.form.addEventListener("submit", this.onSubmit.bind(this));
    }

    /**
     * Handle form submission
     * 
     * @param {Event} ev - Submit event
     */
    async onSubmit(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        // Validate form
        if (!this.form.checkValidity()) {
            this.form.classList.add("was-validated");
            return;
        }

        // Get form data
        const invoiceNumbersText = this.invoiceNumbersInput.value.trim();

        if (!invoiceNumbersText) {
            this.services.notification.add(
                _t("Please enter at least one invoice number"),
                { type: "warning" }
            );
            return;
        }

        // Parse invoice numbers (comma or newline separated, flexible)
        const invoiceNumbers = invoiceNumbersText
            .split(/[,\n]+/)  // Split by comma OR newline (or both)
            .map(num => num.trim())
            .filter(num => num.length > 0);

        if (invoiceNumbers.length === 0) {
            this.services.notification.add(
                _t("Please enter valid invoice numbers"),
                { type: "warning" }
            );
            return;
        }

        // Show loading state
        this.setLoading(true);

        try {
            // Call backend search endpoint
            const result = await this._searchInvoices(invoiceNumbers);

            if (result.success) {
                this.displayResults(result);
            } else {
                this.services.notification.add(result.error, { type: "danger" });
            }
        } catch (error) {
            console.error("Invoice search error:", error);
            this.services.notification.add(
                _t("Connection error. Please try again."),
                { type: "danger" }
            );
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * Search invoices
     * 
     * @param {Array} invoiceNumbers - Array of invoice numbers
     * @return {Promise} Promise that resolves to the search results
     */
    async _searchInvoices(invoiceNumbers) {
        return await rpc("/invoice/search/results", {
            invoice_numbers: invoiceNumbers,
        });
    }

    /**
     * Display search results
     * 
     * @param {Object} data - Search results data
     */
    displayResults(data) {
        // Populate table
        const tbody = document.querySelector("#invoices_table_body");
        tbody.innerHTML = "";

        data.invoices.forEach(invoice => {
            const row = this.createInvoiceRow(invoice);
            tbody.appendChild(row);
        });

        // Update total
        const totalCell = document.querySelector("#total_amount_cell");
        const formattedTotal = this.formatCurrency(
            data.total_amount,
            data.invoices[0].currency_symbol
        );
        totalCell.textContent = formattedTotal;

        // Update payment button
        const paymentBtn = document.querySelector("#proceed_to_payment_btn");
        paymentBtn.href = data.payment_url;

        // Show results
        this.resultsContainer.classList.remove("d-none");

        // Scroll to results
        this.resultsContainer.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    /**
     * Create a table row for an invoice
     * 
     * @param {Object} invoice - Invoice data
     * @return {HTMLElement} Table row element
     */
    createInvoiceRow(invoice) {
        const row = document.createElement("tr");

        // Invoice number
        const invoiceCell = document.createElement("td");
        invoiceCell.className = "fw-bold";
        invoiceCell.textContent = invoice.name;
        row.appendChild(invoiceCell);

        // Amount due
        const amountCell = document.createElement("td");
        amountCell.className = "text-end fw-bold";
        amountCell.textContent = this.formatCurrency(
            invoice.amount_due,
            invoice.currency_symbol
        );
        row.appendChild(amountCell);

        return row;
    }

    /**
     * Format currency amount
     * 
     * @param {Number} amount - Amount to format
     * @param {String} symbol - Currency symbol
     * @return {String} Formatted amount
     */
    formatCurrency(amount, symbol) {
        const formatted = new Intl.NumberFormat(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(amount);

        return `${symbol} ${formatted}`;
    }

    /**
     * Set loading state
     * 
     * @param {Boolean} loading - Whether to show loading state
     */
    setLoading(loading) {
        if (loading) {
            this.searchBtn.disabled = true;
            this.loadingSpinner.classList.remove("d-none");
            this.resultsContainer.classList.add("d-none");
        } else {
            this.searchBtn.disabled = false;
            this.loadingSpinner.classList.add("d-none");
        }
    }
}

registry
    .category("public.interactions")
    .add("payment_rutavity.invoice_search", InvoiceSearchInteraction);
