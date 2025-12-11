/**
 * Author: Sebastián Rodríguez
 * Description: Express checkout implementation for POS Store payment method
 */

import { patch } from '@web/core/utils/patch';
import { patchDynamicContent } from '@web/public/utils';
import { _t } from '@web/core/l10n/translation';
import { rpc } from '@web/core/network/rpc';
import { ExpressCheckout } from '@payment/interactions/express_checkout';

patch(ExpressCheckout.prototype, {
    setup() {
        super.setup();
        patchDynamicContent(this.dynamicContent, {
            'button[name="o_payment_submit_button"]': {
                't-on-click.stop.prevent': this.debounced(
                    this.initiateExpressPayment.bind(this), 500, true
                ),
            },
        });
        
        // Enable submit buttons like Demo does
        document.querySelector('[name="o_payment_submit_button"]')?.removeAttribute('disabled');
        
        // Load salespeople when modal opens
        document.querySelectorAll('[id^="o_payment_pos_store_modal_"]').forEach(modal => {
            modal.addEventListener('shown.bs.modal', () => {
                this._loadSalespeople();
            });
        });
    },

    /**
     * Load available salespeople for the current partner
     * 
     * @private
     * @return {Promise<void>}
     */
    async _loadSalespeople() {
        const salespersonSelect = document.querySelector('#pos_store_salesperson');
        if (!salespersonSelect) return;

        const partnerId = Number.parseInt(salespersonSelect.dataset.partnerId);
        if (!partnerId) return;

        try {
            const salespeople = await rpc('/payment/pos_store/get_salespeople', {
                partner_id: partnerId,
            });

            // Clear existing options except the first one
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
    },

    /**
     * Override _prepareTransactionRouteParams to use POS Store payment method
     * 
     * @override
     * @param {number} providerId - The id of the provider handling the transaction.
     * @returns {object} - The transaction route params.
     */
    _prepareTransactionRouteParams(providerId) {
        const params = super._prepareTransactionRouteParams(providerId);
        
        // Get provider code to check if it's the POS store provider
        const providerElement = document.querySelector(`[data-provider-id="${providerId}"]`);
        const providerCode = providerElement?.dataset?.providerCode;
        
        if (providerCode === 'rutavity') {
            // Get POS Store payment method ID
            const posStoreMethodId = this._getPosStorePaymentMethodId();
            if (posStoreMethodId) {
                params['payment_method_id'] = posStoreMethodId;
                params['flow'] = 'redirect';  // POS Store uses redirect flow
            }
        }
        
        return params;
    },

    /**
     * Get the POS Store payment method ID
     * 
     * @private
     * @returns {number|null} - The POS Store payment method ID
     */
    _getPosStorePaymentMethodId() {
        // Try to get from data attribute if available
        const posStoreButton = document.querySelector('[data-payment-method-code="pos_store"]');
        if (posStoreButton?.dataset?.paymentMethodId) {
            return Number.parseInt(posStoreButton.dataset.paymentMethodId);
        }
        
        // Fallback: return null to use default
        return null;
    },

    /**
     * Process the express payment for POS Store
     *
     * @param {Event} ev
     * @return {Promise<void>}
     */
    async initiateExpressPayment(ev) {
        // Get provider ID like Demo does
        const providerId = ev.target.parentElement.dataset.providerId;
        const providerCode = ev.target.parentElement.dataset.providerCode;
        
        
        // If not POS store, delegate to parent
        if (providerCode !== 'rutavity') {
            return;
        }
        
        // Get salesperson and comments from the modal
        const modal = document.querySelector(`#o_payment_pos_store_modal_${providerId}`);
        if (!modal) {
            console.error('POS Store modal not found');
            return;
        }
        
        const salespersonSelect = modal.querySelector('#pos_store_salesperson');
        const commentsField = modal.querySelector('#pos_store_comments');

        // Validate salesperson selection
        if (!salespersonSelect?.value) {
            this.services.notification.add(
                _t('Please select a salesperson before proceeding with the payment.'),
                { type: 'warning', sticky: false }
            );
            return;
        }

        const salespersonId = Number.parseInt(salespersonSelect.value);
        const comments = commentsField?.value?.trim().substring(0, 255) || null;

        try {
            // Save order data (salesperson, comments, POS configs, team)
            await this.waitFor(rpc('/payment/pos_store/save_order_data', {
                salesperson_id: salespersonId,
                comments: comments,
            }));

            // Process the transaction
            const processingValues = await this.waitFor(rpc(
                this.paymentContext['transactionRoute'],
                this._prepareTransactionRouteParams(providerId),
            ));

            // For redirect flow, submit the form
            if (processingValues?.redirect_form_html) {
                document.body.insertAdjacentHTML('beforeend', processingValues.redirect_form_html);
                
                // Wait a bit for the form to be inserted
                await new Promise(resolve => setTimeout(resolve, 100));
                
                const redirectForm = document.body.querySelector('form[name="o_payment_redirect_form"]');
                if (redirectForm) {
                    redirectForm.submit();
                    return;
                }
            }

            // Fallback: Redirect to the landing route with the transaction reference
            if (processingValues?.reference && this.paymentContext?.['landingRoute']) {
                globalThis.location.href = `${this.paymentContext['landingRoute']}?reference=${processingValues.reference}`;
            } else {
                console.error('No redirect action taken!');
            }
        } catch (error) {
            console.error('ERROR in POS store payment:', error);
            this.services.notification.add(
                error?.data?.message ?? _t('Error processing POS store payment'),
                { type: 'danger', sticky: true }
            );
        }
    },
});

