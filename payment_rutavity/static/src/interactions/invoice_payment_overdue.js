/**
 * Author: Sebastián Rodríguez
 * Invoice Payment Amounts Management
 * Handles real-time validation and calculation of custom payment amounts per invoice
 */

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

/**
 * Interaction for managing editable invoice payment amounts
 * Allows users to customize the amount to pay for each invoice with real-time validation
 */
export class InvoicePaymentAmounts extends Interaction {
    static selector = "#invoices_payment_card";

    /**
     * Setup the interaction when the element is found
     */
    setup() {
        this.amountInputs = this.el.querySelectorAll('.invoice-amount-input');
        this.paymentOptionRadios = this.el.querySelectorAll('.payment-option-radio');
        this.totalAmountDisplay = document.getElementById('payment_total_amount');
        this.currencySymbol = document.getElementById('payment_total_currency')?.textContent || '$';
        
        // Try to detect locale from page language
        this.locale = document.documentElement.lang || 'en-US';
        
        // Bind event handlers
        this.setupEventListeners();
        
        // Initial calculation
        this.updateTotalAmount();
        
        // Intercept payment form submission
        this.setupFormValidation();
    }

    /**
     * Format currency amount with proper formatting (thousands separator, decimals)
     * 
     * @param {number} amount - The amount to format
     * @returns {string} Formatted currency string
     */
    formatCurrency(amount) {
        try {
            // Use Intl.NumberFormat for proper currency formatting
            const formatter = new Intl.NumberFormat(this.locale, {
                style: 'decimal',
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
                useGrouping: true, // Explicitly enable thousands separator
            });

            const formattedNumber = formatter.format(amount);
            return `${this.currencySymbol} ${formattedNumber}`;
        } catch (error) {
            // Fallback to simple formatting if Intl is not available
            return `${this.currencySymbol} ${amount.toFixed(2)}`;
        }
    }

    /**
     * Setup event listeners for all amount inputs and payment option radios
     */
    setupEventListeners() {
        this.amountInputs.forEach(input => {
            // Real-time validation on input
            input.addEventListener('input', () => this.updateTotalAmount());

            // Validate and auto-correct on blur
            input.addEventListener('blur', (e) => this.handleInputBlur(e.target));
        });
        
        // Setup listeners for payment option radio buttons
        this.paymentOptionRadios.forEach(radio => {
            radio.addEventListener('change', (e) => this.handlePaymentOptionChange(e.target));
        });
    }

    /**
     * Handle payment option radio change (installment or full payment)
     * Updates the editable input value and recalculates total
     */
    handlePaymentOptionChange(radio) {
        if (!radio.checked) {
            return;
        }
        
        const invoiceId = radio.dataset.invoiceId;
        const selectedAmount = parseFloat(radio.dataset.amount) || 0;
        
        // Find the corresponding input for this invoice
        const amountInput = this.el.querySelector(
            `.invoice-amount-input[data-invoice-id="${invoiceId}"]`
        );
        
        if (amountInput) {
            // Update the input with the selected amount
            amountInput.value = selectedAmount.toFixed(2);
            
            // Recalculate total
            this.updateTotalAmount();
        }
    }

    /**
     * Handle input blur event with validation and formatting
     */
    handleInputBlur(input) {
        let value = parseFloat(input.value) || 0;
        const maxAmount = parseFloat(input.dataset.maxAmount) || 0;

        // Auto-correct if exceeds max
        if (value > maxAmount) {
            value = maxAmount;
        }

        // Set minimum value
        if (value < 0.01) {
            value = 0.01;
        }

        // Format to 2 decimals
        input.value = value.toFixed(2);
        this.updateTotalAmount();
    }

    /**
     * Calculate and update the total payment amount
     */
    updateTotalAmount() {
        let total = 0;
        let isValid = true;

        this.amountInputs.forEach(input => {
            const value = parseFloat(input.value) || 0;
            const maxAmount = parseFloat(input.dataset.maxAmount) || 0;

            // Validate each input
            if (value <= 0 || value > maxAmount) {
                isValid = false;
                this.showValidationError(input, maxAmount);
            } else {
                this.hideValidationError(input);
                total += value;
            }
        });

        // Update total display with formatted currency
        if (this.totalAmountDisplay) {
            this.totalAmountDisplay.textContent = this.formatCurrency(total);
        }

        // Update payment form amount
        this.updatePaymentFormAmount(total);

        return isValid;
    }

    /**
     * Show validation error for an input
     */
    showValidationError(input, maxAmount) {
        const card = input.closest('.invoice-card');
        const errorMsg = card?.querySelector('.invalid-amount-msg');
        const maxDisplay = errorMsg?.querySelector('.max-amount-display');

        if (errorMsg && maxDisplay) {
            maxDisplay.textContent = maxAmount.toFixed(2);
            errorMsg.classList.remove('d-none');
            input.classList.add('is-invalid');
        }
    }

    /**
     * Hide validation error for an input
     */
    hideValidationError(input) {
        const card = input.closest('.invoice-card');
        const errorMsg = card?.querySelector('.invalid-amount-msg');

        if (errorMsg) {
            errorMsg.classList.add('d-none');
            input.classList.remove('is-invalid');
        }
    }

    /**
     * Update the amount in the payment form
     * This ensures the payment gateway receives the correct total
     */
    updatePaymentFormAmount(amount) {
        // Update the payment.summary_item (o_payment_summary_amount)
        const paymentSummaryAmount = document.getElementById('o_payment_summary_amount');
        if (paymentSummaryAmount) {
            // Format amount with proper currency formatting (thousands separators, decimals)
            const formattedAmount = this.formatCurrency(amount);
            paymentSummaryAmount.textContent = formattedAmount;
        }
    }

    /**
     * Setup form validation before submission
     */
    setupFormValidation() {
        const paymentForm = document.querySelector('#o_payment_form');
        if (paymentForm) {
            paymentForm.addEventListener('submit', (e) => this.validateBeforeSubmit(e));
        }

        // Listen for Odoo payment processing events
        document.addEventListener('payment_processing.submit', (e) => {
            if (!this.updateTotalAmount()) {
                e.preventDefault();
            }
        });
    }

    /**
     * Validate before payment submission
     */
    validateBeforeSubmit(event) {
        if (!this.updateTotalAmount()) {
            event.preventDefault();
            this.services.notification.add(
                _t('Please correct the invalid amounts before proceeding with payment.'),
                { type: 'warning' }
            );
            return false;
        }

        const total = parseFloat(this.totalAmountDisplay?.textContent || '0');
        if (total <= 0) {
            event.preventDefault();
            this.services.notification.add(
                _t('The total payment amount must be greater than zero.'),
                { type: 'warning' }
            );
            return false;
        }
        if (total < 500) {
            event.preventDefault();
            this.services.notification.add(
                _t('The total payment amount must be greater than 500.'),
                { type: 'warning' }
            );
            return false;
        }

        return true;
    }
}

registry
    .category("public.interactions")
    .add("payment_rutavity.invoice_payment_amounts", InvoicePaymentAmounts);

