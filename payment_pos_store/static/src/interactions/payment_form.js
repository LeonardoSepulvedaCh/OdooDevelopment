/**
 * Author: Sebastián Rodríguez
 * Description: Payment form extension for POS store payment method
 * to capture and send salesperson selection and order comments.
 */

import { PaymentForm } from '@payment/interactions/payment_form';
import { patch } from '@web/core/utils/patch';
import { rpc } from '@web/core/network/rpc';
import { _t } from '@web/core/l10n/translation';

patch(PaymentForm.prototype, {

    /**
     * Override submitForm to validate POS store payment method requirements
     * 
     * @override method from payment.payment_form
     * @param {Event} ev - The submit event
     */
    async submitForm(ev) {
        ev.stopPropagation();
        ev.preventDefault();

        // Get the selected payment method
        const checkedRadio = this.el.querySelector('input[name="o_payment_radio"]:checked');
        if (checkedRadio) {
            const paymentMethodCode = checkedRadio.dataset.paymentMethodCode;

            // Validate POS store payment method
            if (paymentMethodCode === 'pos_store') {
                const salespersonSelect = this.el.querySelector('#pos_store_salesperson');

                // Check if salesperson is selected
                if (!salespersonSelect?.value) {
                    this.services.notification.add(
                        _t('Please select a salesperson before proceeding with the payment.'),
                        { type: 'warning', sticky: false }
                    );
                    return; // Stop form submission
                }
            }
        }

        // Call parent submitForm if validation passes
        return await super.submitForm(ev);
    },

    /**
     * Override _prepareInlineForm to load salespeople for POS store payment
     * 
     * @override method from payment.payment_form
     * @private
     * @param {number} providerId - The id of the selected payment option's provider.
     * @param {string} providerCode - The code of the selected payment option's provider.
     * @param {number} paymentOptionId - The id of the selected payment option.
     * @param {string} paymentMethodCode - The code of the selected payment method, if any.
     * @param {string} flow - The online payment flow of the selected payment option.
     * @return {void}
     */
    async _prepareInlineForm(providerId, providerCode, paymentOptionId, paymentMethodCode, flow) {
        await super._prepareInlineForm(providerId, providerCode, paymentOptionId, paymentMethodCode, flow);

        // Check if this is a POS store payment method
        if (paymentMethodCode === 'pos_store') {
            const salespersonSelect = this.el.querySelector('#pos_store_salesperson');
            if (salespersonSelect) {
                const partnerId = Number.parseInt(salespersonSelect.dataset.partnerId);
                if (partnerId) {
                    try {
                        // Load available salespeople via RPC
                        const salespeople = await rpc('/payment/pos_store/get_salespeople', {
                            partner_id: partnerId,
                        });

                        // Clear existing options except the first one (placeholder)
                        salespersonSelect.innerHTML = '<option value="">Select a salesperson...</option>';

                        // Add salespeople options
                        salespeople.forEach(salesperson => {
                            const option = document.createElement('option');
                            option.value = salesperson.id;
                            option.textContent = salesperson.name;
                            salespersonSelect.appendChild(option);
                        });
                    } catch (error) {
                        console.error('Error loading salespeople:', error);
                    }
                }
            }
        }
    },

    /**
     * Override _processRedirectFlow to save POS store data before processing payment
     * 
     * @override method from payment.payment_form
     * @private
     * @param {string} providerCode - The code of the selected payment option's provider.
     * @param {number} paymentOptionId - The id of the selected payment option.
     * @param {string} paymentMethodCode - The code of the selected payment method, if any.
     * @param {object} processingValues - The processing values of the transaction.
     * @return {void}
     */
    async _processRedirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        // Check if this is a POS store payment method
        if (paymentMethodCode === 'pos_store') {
            const salespersonSelect = this.el.querySelector('#pos_store_salesperson');
            const commentsField = this.el.querySelector('#pos_store_comments');

            const salespersonId = salespersonSelect?.value ? Number.parseInt(salespersonSelect.value) : null;
            const comments = commentsField?.value?.trim().substring(0, 255) || null;

            // Save data if either field has a value
            if (salespersonId || comments) {
                try {
                    // Save order data via RPC before processing payment
                    await rpc('/payment/pos_store/save_order_data', {
                        salesperson_id: salespersonId,
                        comments: comments,
                    });
                } catch (error) {
                    console.error('Error saving POS store order data:', error?.data?.message);
                    this.services.notification.add(
                        error?.data?.message ?? _t('Error saving POS store order data'),
                        { type: 'danger', sticky: true }
                    );
                    throw error;
                }
            }
        }

        // Call parent method to continue normal flow
        return await super._processRedirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues);
    },
});
