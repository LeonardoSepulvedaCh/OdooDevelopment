/**
 * Author: Sebastián Rodríguez
 * Description: Payment form extension for Rutavity PSE validation,
 * bank list management, pending transactions check and create gateway transaction.
 */

import { PaymentForm } from '@payment/interactions/payment_form';
import { patch } from '@web/core/utils/patch';
import { _t } from '@web/core/l10n/translation';
import { rpc } from '@web/core/network/rpc';

patch(PaymentForm.prototype, {

    setup() {
        super.setup();
        this.bankFieldElement = null;
        this.bankList = [];
        this.paymentContext.documentPaymentData = {
            documentsData: {},
            totalAmount: 0,
            documentIds: [],
            documentType: null,
            documentModel: null,
            documentErrorMessage: null
        };
    },

    /**
     * Collect document amounts data from current payment context
     * 
     * @private
     * @return {void}
     */
    _collectDocumentAmountData() {
        const transactionRoute = this.paymentContext.transactionRoute;

        // Route patterns mapping to document types
        const routePatterns = this._getRoutePatterns();

        // Try to match route and extract document info
        let documentIds = [];
        let documentType = null;
        let documentModel = null;
        let documentErrorMessage = null;
        let documentTotalAmount = 0;
        let documentDocumentsData = {
            type: null,
            data: [],
        };

        if (!transactionRoute) {
            console.warn('No transaction route found');
            return;
        }

        for (const { pattern, model, type, errorMessage } of routePatterns) {
            const matches = transactionRoute.match(pattern);
            if (matches) {
                documentModel = model;
                documentType = documentDocumentsData.type = type;
                documentErrorMessage = errorMessage;

                // For single invoice/order, extract ID from route and convert to array
                if (documentType === 'multiple_invoices') {
                    // Try to collect invoice amounts from the invoice payment cards
                    const invoicesPaymentCard = document.getElementById('invoices_payment_card');
                    const amountInputs = invoicesPaymentCard.querySelectorAll('.invoice-amount-input');

                    amountInputs.forEach(input => {
                        const invoiceId = parseInt(input.dataset.invoiceId);
                        const inputAmount = parseFloat(input.value) || 0;
                        const currencyId = parseInt(input.dataset.currencyId);

                        if (invoiceId && inputAmount > 0) {
                            documentDocumentsData.data.push({
                                id: invoiceId,
                                amount: inputAmount,
                                currency_id: currencyId
                            });

                            documentIds.push(invoiceId);
                            documentTotalAmount += inputAmount;
                        }
                    });
                } else {
                    documentIds = [parseInt(matches[1], 10)];
                    documentTotalAmount = this.paymentContext.amount;
                }
                break;
            }
        }

        // If we can't determine the document type, model or ids, allow to proceed
        if (!documentType || !documentModel || !documentIds || documentIds.length === 0 || !documentErrorMessage || !documentTotalAmount || !documentDocumentsData.type) {
            console.warn('Unable to determine document type, model, ids, total amount or documents data for pending transaction check');
            return;
        }

        // Update the document payment data
        this.paymentContext.documentPaymentData.documentsData = documentDocumentsData;
        this.paymentContext.documentPaymentData.totalAmount = documentTotalAmount;
        this.paymentContext.documentPaymentData.documentIds = documentIds;
        this.paymentContext.documentPaymentData.documentType = documentType;
        this.paymentContext.documentPaymentData.documentModel = documentModel;
        this.paymentContext.documentPaymentData.documentErrorMessage = documentErrorMessage;
    },

    /**
     * Get the route patterns for the document types
     * @private
     * @returns {Array} The route patterns
     */
    _getRoutePatterns() {
        return [
            {
                pattern: /\/invoice\/transaction\/overdue/,
                model: 'account.move',
                type: 'multiple_invoices',
                errorMessage: "Ya tiene una transacción pendiente para una o más facturas. Por favor, espere a que se complete antes de intentar un nuevo pago."
            },
            {
                pattern: /\/invoice\/transaction\/(\d+)/,
                model: 'account.move',
                type: 'single_invoice',
                errorMessage: "Ya tiene una transacción pendiente para esta factura. Por favor, espere a que se complete antes de intentar un nuevo pago."
            },
            {
                pattern: /\/shop\/payment\/transaction\/(\d+)/,
                model: 'sale.order',
                type: 'single_order',
                errorMessage: "Ya tiene una transacción pendiente para este pedido. Por favor, espere a que se complete antes de intentar un nuevo pago."
            },
        ];
    },

    /**
     * Prepare the params for the RPC to the transaction route.
     * Override to include documents_data for overdue invoices with custom amounts.
     * 
     * @override method from payment.payment_form
     * @private
     * @return {object} The transaction route params.
     */
    _prepareTransactionRouteParams() {
        const transactionRouteParams = super._prepareTransactionRouteParams(...arguments);

        // Check if we have invoice payment data
        if (Object.keys(this.paymentContext.documentPaymentData.documentsData).length > 0
            && this.paymentContext.documentPaymentData.documentType !== 'single_order'
        ) {
            transactionRouteParams.documents_data = this.paymentContext.documentPaymentData.documentsData;
            transactionRouteParams.amount = this.paymentContext.documentPaymentData.totalAmount;
        }

        return transactionRouteParams;
    },

    /**
     * Override _prepareInlineForm method to load the bank list asynchronously
     * and set direct flow
     * @private
     * @param {number} providerId - The id of the selected payment option's provider.
     * @param {string} providerCode - The code of the selected payment option's provider.
     * @param {number} paymentOptionId - The id of the selected payment option.
     * @param {string} paymentMethodCode - The code of the selected payment method, if any.
     * @param {string} flow - The online payment flow of the selected payment option.
     * @return {void}
     */
    async _prepareInlineForm(providerId, providerCode, paymentOptionId, paymentMethodCode, flow) {
        if (providerCode !== 'rutavity' || paymentMethodCode !== 'pse') {
            await super._prepareInlineForm(...arguments);
            return;
        }

        // Set the payment flow to 'direct'
        this._setPaymentFlow('direct');

        // Load bank list asynchronously
        if (!this.bankList.length) {
            this._initializeBankFieldElement();
            this._getBankList().then(bankList => {
                if (bankList && bankList.length > 0) {
                    this.bankList = bankList;
                    this._populateBankSelect();
                }
            });
        }
    },

    /**
     * Initialize the bank select element
     * @private
     * @returns {void}
     */
    _initializeBankFieldElement() {
        // Get the bank select element
        const checkedRadio = this.el.querySelector('input[name="o_payment_radio"]:checked');
        if (!checkedRadio) {
            console.warn('No payment option selected');
            return;
        }

        const inlineForm = this._getInlineForm(checkedRadio);
        if (!inlineForm) {
            console.warn('No inline form found');
            return;
        }

        const bankSelect = inlineForm.querySelector('[name="bank"]');
        if (!bankSelect) {
            console.warn('Bank select element not found');
            return;
        }

        this.bankFieldElement = bankSelect;
    },

    /**
     * Fetch bank list from server
     * @private
     * @returns {Promise<Array>} Array of banks or empty array on error
     */
    async _getBankList() {
        try {
            // Disable the bank select element
            this.bankFieldElement.disabled = true;
            // Fetch bank list from server
            const result = await rpc('/payment/gateway/get_bank_list');

            if (result?.error || result?.success === false || !result?.data) {
                throw new Error(result.error || result?.textResponse || 'Invalid response format');
            }

            return result.data;
        } catch (error) {
            console.error('Error fetching bank list:', error.message);
            return [];
        }
    },

    /**
     * Populate the bank select element with the provided bank list
     * @private
     * @returns {void}
     */
    _populateBankSelect() {
        try {
            // Create document fragment for better performance
            const fragment = document.createDocumentFragment();

            // Add bank options from the list
            this.bankList.forEach(bank => {
                const option = document.createElement('option');
                option.value = bank.bankCode;
                option.textContent = bank.bankName;
                fragment.appendChild(option);
            });

            // Update select efficiently with fragment
            this.bankFieldElement.innerHTML = '';
            this.bankFieldElement.appendChild(fragment);

            // Enable select
            this.bankFieldElement.disabled = false;
        } catch (error) {
            console.error('Error populating bank select:', error);
        }
    },

    /**
     * Check if there are pending transactions for the current order or invoice
     * @private
     * @returns {Promise<Object>} Object with canProceed flag
     */
    async _checkPendingTransactions() {
        try {
            // Check for pending transactions
            const result = await rpc('/payment/gateway/check_pending_transactions', {
                'document_type': this.paymentContext.documentPaymentData.documentType,
                'document_model': this.paymentContext.documentPaymentData.documentModel,
                'document_ids': this.paymentContext.documentPaymentData.documentIds,
            });

            if (!result.success) {
                this.services.notification.add(
                    _t("Error al verificar las transacciones pendientes. Por favor, intente nuevamente."),
                    { type: 'danger' }
                );
                console.error('Error checking pending transactions:', result.error);
                return { canProceed: false };
            }

            if (result.has_pending) {
                this.services.notification.add(
                    _t(this.paymentContext.documentPaymentData.documentErrorMessage ?? _t("Ya tiene una transacción pendiente para este documento. Por favor, espere a que se complete antes de intentar un nuevo pago.")),
                    { type: 'warning' }
                );
                return { canProceed: false };
            }

            return { canProceed: true };

        } catch (error) {
            console.error('Error checking pending transactions:', error);
            this.services.notification.add(
                _t('Error al verificar las transacciones pendientes. Por favor, intente nuevamente.'),
                { type: 'danger' }
            );
            return { canProceed: false };
        }
    },

    /**
     * Override submitForm to add Rutavity-specific validations
     * @param {Event} ev 
     */
    async submitForm(ev) {
        ev.stopPropagation();
        ev.preventDefault();

        // Block the entire UI to prevent fiddling with other interactions.
        this._disableButton(true);

        // Collect document amounts data
        this._collectDocumentAmountData();

        const checkedRadio = this.el.querySelector('input[name="o_payment_radio"]:checked');

        // Check for pending transactions before proceeding
        const pendingCheck = await this._checkPendingTransactions();
        if (!pendingCheck.canProceed) {
            ev.stopPropagation();
            ev.preventDefault();
            this._enableButton(true);
            return;
        }

        // Check if this is a Rutavity PSE payment method
        if (!this._isRutavityPsePayment(checkedRadio)) {
            this._enableButton(true);
            // Call the original submitForm method
            return await super.submitForm(ev);
        }

        // Perform Rutavity-specific validations
        const validationResult = this._validateRutavityPseForm(checkedRadio);
        if (!validationResult.isValid) {
            ev.stopPropagation();
            ev.preventDefault();

            // Show all error notifications
            validationResult.errors.forEach(errorMessage => {
                this.services.notification.add(errorMessage, { type: 'danger' });
            });
            this._enableButton(true);
            return;
        }

        this._enableButton(true);
        return await super.submitForm(ev);
    },

    /**
     * Override _processDirectFlow to handle Rutavity PSE payment processing
     * @private
     * @param {string} providerCode - The code of the selected payment option's provider.
     * @param {number} paymentOptionId - The id of the selected payment option.
     * @param {string} paymentMethodCode - The code of the selected payment method, if any.
     * @param {object} processingValues - The processing values of the transaction.
     * @return {void}
     */
    async _processDirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        if (providerCode !== 'rutavity' || paymentMethodCode !== 'pse') {
            await super._processDirectFlow(...arguments);
            return;
        }

        // Get the inline form data
        const checkedRadio = this.el.querySelector('input[name="o_payment_radio"]:checked');
        const inlineForm = this._getInlineForm(checkedRadio);

        if (!inlineForm) {
            this._displayErrorDialog(_t("Error al procesar el pago"), _t("Datos del formulario no encontrados"));
            this._enableButton();
            return;
        }

        // Collect form data
        const paymentData = {
            bank: inlineForm.querySelector('[name="bank"]')?.value,
            email: inlineForm.querySelector('[name="email"]')?.value,
            documentType: inlineForm.querySelector('[name="documentType"]')?.value,
            documentNumber: inlineForm.querySelector('[name="documentNumber"]')?.value,
            firstName: inlineForm.querySelector('[name="firstName"]')?.value,
            lastName: inlineForm.querySelector('[name="lastName"]')?.value,
            phone: inlineForm.querySelector('[name="phone"]')?.value,
            address: inlineForm.querySelector('[name="address"]')?.value,
            reference: processingValues.reference,
            txAmount: processingValues.amount,
            txProviderCode: providerCode,
            txPaymentMethodCode: paymentMethodCode,
            txPartnerId: processingValues.partner_id,
        };

        try {
            // Process the payment with Rutavity Gateway
            const result = await this.waitFor(rpc('/payment/gateway/create_transaction', {
                'payment_data': paymentData,
            }));

            if (result.success && result.redirect_url) {
                // Redirect to payment gateway
                window.location.href = result.redirect_url;
            } else {
                this._displayErrorDialog(
                    _t("Payment processing failed"),
                    result.error || _t("Ocurrió un error al procesar su pago")
                );
                this._enableButton();
            }
        } catch (error) {
            this._displayErrorDialog(
                _t("Payment processing failed"),
                error.data?.message || _t("Ocurrió un error al procesar su pago")
            );
            this._enableButton();
        }
    },

    /**
     * Check if the selected payment method is Rutavity PSE
     * @private
     * @param {HTMLInputElement} radio 
     * @returns {boolean}
     */
    _isRutavityPsePayment(radio) {
        if (!radio) return false;
        const providerCode = this._getProviderCode(radio);
        const pmCode = this._getPaymentMethodCode(radio);
        return providerCode === 'rutavity' && pmCode === 'pse';
    },

    /**
     * Validate Rutavity PSE form fields
     * @private
     * @param {HTMLInputElement} radio 
     * @returns {Object} Validation result with isValid flag and message
     */
    _validateRutavityPseForm(radio) {
        const inlineForm = this._getInlineForm(radio);
        if (!inlineForm) {
            return { isValid: true, message: '' };
        }

        // Get form elements
        const bank = inlineForm.querySelector('[name="bank"]');
        const email = inlineForm.querySelector('[name="email"]');
        const documentType = inlineForm.querySelector('[name="documentType"]');
        const documentNumber = inlineForm.querySelector('[name="documentNumber"]');
        const firstName = inlineForm.querySelector('[name="firstName"]');
        const lastName = inlineForm.querySelector('[name="lastName"]');
        const phone = inlineForm.querySelector('[name="phone"]');
        const address = inlineForm.querySelector('[name="address"]');

        // Validation rules
        const validations = [
            {
                field: bank,
                name: 'Bank',
                validator: (value) => value && value.trim() !== '' && value !== '0',
                message: _t("Por favor, seleccione un banco.")
            },
            {
                field: email,
                name: 'Email',
                validator: (value) => this._validateEmail(value),
                message: _t('Por favor, ingrese un correo electrónico válido.')
            },
            {
                field: documentType,
                name: 'Document Type',
                validator: (value) => value && value.trim() !== '',
                message: _t('Por favor, seleccione un tipo de documento.')
            },
            {
                field: documentNumber,
                name: 'Document Number',
                validator: (value) => this._validateDocumentNumber(value),
                message: _t('Por favor, ingrese un número de documento válido (números y guiones, 6-20 caracteres).')
            },
            {
                field: firstName,
                name: 'First Name',
                validator: (value) => this._validateName(value),
                message: _t('Por favor, ingrese un nombre válido (solo letras y espacios, 2-50 caracteres).')
            },
            {
                field: lastName,
                name: 'Last Name',
                validator: (value) => this._validateName(value),
                message: _t('Por favor, ingrese un apellido válido (solo letras y espacios, 2-50 caracteres).')
            },
            {
                field: phone,
                name: 'Phone',
                validator: (value) => this._validatePhone(value),
                message: _t('Por favor, ingrese un número de teléfono válido (solo números, 7-10 dígitos).')
            },
            {
                field: address,
                name: 'Address',
                validator: (value) => this._validateAddress(value),
                message: _t('Por favor, ingrese una dirección válida (5-200 caracteres).')
            }
        ];

        // Perform validations - collect all errors
        const errors = [];

        for (const validation of validations) {
            if (!validation.field) continue;

            const value = validation.field.value;
            if (!validation.validator(value)) {
                // Highlight the invalid field
                this._highlightInvalidField(validation.field);
                errors.push(validation.message);
            } else {
                // Remove highlight if field is now valid
                this._removeFieldHighlight(validation.field);
            }
        }

        // Return result with all error messages
        if (errors.length > 0) {
            return {
                isValid: false,
                errors: errors
            };
        }

        return { isValid: true, errors: [] };
    },

    /**
     * Validate email format
     * @private
     * @param {string} email 
     * @returns {boolean}
     */
    _validateEmail(email) {
        if (!email || email.trim() === '') return false;
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email.trim());
    },

    /**
     * Validate document number (only numbers and hyphens, 6-20 characters)
     * @private
     * @param {string} documentNumber 
     * @returns {boolean}
     */
    _validateDocumentNumber(documentNumber) {
        if (!documentNumber || documentNumber.trim() === '') return false;
        const docRegex = /^[\d\-]{6,20}$/;
        return docRegex.test(documentNumber.trim());
    },

    /**
     * Validate names (only letters, spaces, accents, 2-50 characters)
     * @private
     * @param {string} name 
     * @returns {boolean}
     */
    _validateName(name) {
        if (!name || name.trim() === '') return false;
        const nameRegex = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{2,50}$/;
        return nameRegex.test(name.trim());
    },

    /**
     * Validate international phone number
     * @private
     * @param {string} phone 
     * @returns {boolean}
     */
    _validatePhone(phone) {
        if (!phone || phone.trim() === '') return false;
        const cleanPhone = phone.replace(/[\s\-\(\)\.]/g, '');

        // International phone number validation
        // Accepts: optional + followed by 7-10 digits (international standard)
        // Allows country codes and standard phone formats
        const phoneRegex = /^\+?\d{7,10}$/;

        return phoneRegex.test(cleanPhone);
    },

    /**
     * Validate address (5-200 characters)
     * @private
     * @param {string} address 
     * @returns {boolean}
     */
    _validateAddress(address) {
        if (!address || address.trim() === '') return false;
        const trimmedAddress = address.trim();
        return trimmedAddress.length >= 5 && trimmedAddress.length <= 200;
    },

    /**
     * Highlight invalid field with red border
     * @private
     * @param {HTMLElement} field 
     */
    _highlightInvalidField(field) {
        field.classList.add('is-invalid');
        field.style.borderColor = '#dc3545';
        field.style.boxShadow = '0 0 0 0.2rem rgba(220, 53, 69, 0.25)';
    },

    /**
     * Remove highlight from field
     * @private
     * @param {HTMLElement} field 
     */
    _removeFieldHighlight(field) {
        field.classList.remove('is-invalid');
        field.style.borderColor = '';
        field.style.boxShadow = '';
    },
});
