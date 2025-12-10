from odoo import models, fields, api


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _get_applicable_discount(self, move, payment_date):
        """
        Find the highest applicable discount from multi-discount configuration based on payment date.

        :param move: Invoice move record
        :param payment_date: Payment date to check against discount deadlines
        :return: Applicable discount record or False
        """
        if not move.invoice_payment_term_id.discount_ids:
            return False

        invoice_date = move.invoice_date or fields.Date.context_today(self)
        possible_discounts = []
        for discount in move.invoice_payment_term_id.discount_ids:
            discount_date = discount._get_discount_date(invoice_date)
            if payment_date <= discount_date:
                possible_discounts.append(discount)

        if possible_discounts:
            return max(possible_discounts, key=lambda d: d.discount_percentage)
        return False

    def _get_dynamic_net_and_discount(self, line, payment_date):
        """
        Calculate the Net Amount and Discount Amount dynamically based on payment date.
        Returns (Original Net Amount, Original Discount Amount) for the whole invoice/line.
        """
        move = line.move_id

        # Check Multi-Discount first
        if move.invoice_payment_term_id.discount_ids:
            discount = self._get_applicable_discount(move, payment_date)

            if discount:
                percentage = discount.discount_percentage / 100.0
                currency = line.currency_id

                if move.invoice_payment_term_id.early_pay_discount_computation in (
                    "excluded",
                    "mixed",
                ):
                    untaxed = move.amount_untaxed
                    total = move.amount_total
                    discount_on_untaxed = currency.round(untaxed * percentage)
                    net_amount = currency.round(total - discount_on_untaxed)
                else:
                    net_amount = currency.round(line.amount_currency * (1 - percentage))

                discount_amount = abs(line.amount_currency) - abs(net_amount)
                return abs(net_amount), discount_amount
            else:
                # Multi-discount configured but none applicable -> 0 Discount
                return abs(line.amount_currency), 0.0

        # Fallback to standard stored values if no multi-discount
        if move.invoice_payment_term_id.early_discount:
            return abs(line.discount_amount_currency), (
                abs(line.amount_currency) - abs(line.discount_amount_currency)
            )

        return abs(line.amount_currency), 0.0

    # --- Proportional Logic ---

    def _calculate_proportional_epd_ratio(self, batch_result):
        """
        Calculate payment ratio for proportional EPD based on Dynamic Net Amount.

        :param batch_result: Payment batch containing lines
        :return: Ratio (Amount Paid / Dynamic Net Amount)
        """
        original_net_amount = 0.0
        for line in batch_result["lines"]:
            if line.move_id._is_eligible_for_early_payment_discount(
                self.currency_id, self.payment_date
            ):
                net, _ = self._get_dynamic_net_and_discount(line, self.payment_date)
                original_net_amount += net

        if not self.currency_id.is_zero(original_net_amount):
            return self.amount / original_net_amount
        return 0.0

    def _prepare_epd_aml_values(self, batch_result):
        """
        Prepare account move line values for EPD write-off calculation.

        :param batch_result: Payment batch containing lines
        :return: List of AML values with amounts and balances
        """
        epd_aml_values_list = []
        for aml in batch_result["lines"]:
            if aml.move_id._is_eligible_for_early_payment_discount(
                self.currency_id, self.payment_date
            ):
                epd_aml_values_list.append(
                    {
                        "aml": aml,
                        "amount_currency": -aml.amount_residual_currency,
                        "balance": aml.currency_id._convert(
                            -aml.amount_residual_currency,
                            aml.company_currency_id,
                            self.company_id,
                            self.payment_date,
                        ),
                    }
                )
        return epd_aml_values_list

    def _calculate_full_discount_balance(self, total_amount_values):
        """
        Calculate the total discount balance in company currency for EPD write-off.

        :param total_amount_values: Dictionary containing payment lines
        :return: Total discount balance converted to company currency
        """
        full_discount_amount_unsigned = 0.0
        for line in total_amount_values["lines"]:
            if line.move_id._is_eligible_for_early_payment_discount(
                self.currency_id, self.payment_date
            ):
                _, discount = self._get_dynamic_net_and_discount(
                    line, self.payment_date
                )
                full_discount_amount_unsigned += discount

        sign = -1 if self.payment_type == "outbound" else 1
        open_amount_currency = full_discount_amount_unsigned * sign

        return self.currency_id._convert(
            open_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.payment_date,
        )

    def _scale_epd_writeoff_lines(self, early_payment_values, ratio):
        """
        Scale EPD write-off lines by the proportional payment ratio.

        :param early_payment_values: Dictionary of write-off line values by category
        :param ratio: Scaling factor for proportional discount
        :return: List of scaled write-off line values
        """
        scaled_writeoff_lines = []
        for aml_values_list in early_payment_values.values():
            for write_off_line in aml_values_list:
                write_off_line["amount_currency"] *= ratio
                write_off_line["balance"] *= ratio
            scaled_writeoff_lines += aml_values_list
        return scaled_writeoff_lines

    def _get_proportional_epd_writeoff_lines(self, batch_result, total_amount_values):
        """
        Generate proportional EPD write-off lines for partial payments.

        Orchestrates the calculation of proportional ratio, full discount balance,
        and scaling of write-off lines to match the partial payment amount.

        :param batch_result: Payment batch containing lines
        :param total_amount_values: Dictionary containing payment lines and totals
        :return: List of scaled write-off line values ready for payment creation
        """
        ratio = self._calculate_proportional_epd_ratio(batch_result)
        epd_aml_values_list = self._prepare_epd_aml_values(batch_result)
        open_balance = self._calculate_full_discount_balance(total_amount_values)

        # Note: We pass context payment_date so standard methods can use it if needed
        early_payment_values = (
            self.env["account.move"]
            .with_context(payment_date=self.payment_date)
            ._get_invoice_counterpart_amls_for_early_payment_discount(
                epd_aml_values_list, open_balance
            )
        )

        return self._scale_epd_writeoff_lines(early_payment_values, ratio)

    # --- Main Overrides ---
    def _get_total_amounts_to_pay(self, batch_results):
        """
        Override to recalculate suggested payment amount using dynamic discount percentages.

        When EPD is applicable, recalculates the suggested amount by determining the
        currently applicable discount percentage based on payment date, then applying
        proportional logic to the remaining balance.

        :param batch_results: List of payment batch dictionaries
        :return: Dictionary with total amounts, including dynamically calculated amount_by_default
        """
        # Get standard calculation (which uses AML _get_installments_data)
        total_amount_values = super()._get_total_amounts_to_pay(batch_results)

        if total_amount_values["epd_applied"]:
            new_amount_by_default = 0.0

            for line in total_amount_values["lines"]:
                if line.move_id._is_eligible_for_early_payment_discount(
                    self.currency_id, self.payment_date
                ):
                    residual = line.amount_residual_currency

                    # Calculate Dynamic Original Discount for this payment date
                    original_net, original_discount = (
                        self._get_dynamic_net_and_discount(line, self.payment_date)
                    )
                    total_original_gross = original_net + original_discount

                    if total_original_gross:
                        remaining_ratio = abs(residual) / total_original_gross
                        remaining_discount = original_discount * remaining_ratio
                        new_amount_by_default += abs(residual) - remaining_discount
                    else:
                        new_amount_by_default += abs(residual)
                else:
                    new_amount_by_default += line.amount_residual_currency

            if self.currency_id:
                new_amount_by_default = self.currency_id.round(new_amount_by_default)

            total_amount_values["amount_by_default"] = new_amount_by_default

        return total_amount_values

    @api.depends("can_edit_wizard", "payment_date", "currency_id", "amount")
    def _compute_early_payment_discount_mode(self):
        """
        Override to enable EPD mode for partial payments when applicable discount exists.

        Forces EPD mode activation even for partial payment amounts if a valid discount
        applies on the payment date, allowing proportional discount application.
        """
        super()._compute_early_payment_discount_mode()
        for wizard in self:
            if wizard.early_payment_discount_mode:
                continue

            if (
                not wizard.journal_id
                or not wizard.currency_id
                or not wizard.payment_date
            ):
                continue

            # Pass context for dynamic calculations in super if needed
            total_amount_values = wizard.with_context(
                payment_date=wizard.payment_date
            )._get_total_amounts_to_pay(wizard.batches)

            if total_amount_values["epd_applied"]:
                if not wizard.currency_id.is_zero(wizard.amount):
                    wizard.early_payment_discount_mode = True

    @api.depends("early_payment_discount_mode")
    def _compute_payment_difference_handling(self):
        """
        Override to set payment difference handling to 'open' for partial EPD payments.

        When paying less than the suggested amount with EPD active, keeps the invoice
        open instead of reconciling fully, allowing subsequent partial payments.
        """
        super()._compute_payment_difference_handling()
        for wizard in self:
            if wizard.early_payment_discount_mode and wizard.can_edit_wizard:
                total_amount_values = wizard._get_total_amounts_to_pay(wizard.batches)
                amount_by_default = total_amount_values["amount_by_default"]

                if (
                    wizard.currency_id.compare_amounts(wizard.amount, amount_by_default)
                    == -1
                ):
                    wizard.payment_difference_handling = "open"

    @api.depends("can_edit_wizard", "amount", "installments_mode")
    def _compute_payment_difference(self):
        """
        Override to display proportional discount amount in wizard UI.

        Calculates the proportional discount amount based on the payment ratio
        (Amount Paid / Dynamic Net Amount) to show users the actual discount being applied.
        """
        super()._compute_payment_difference()
        for wizard in self:
            if (
                wizard.early_payment_discount_mode
                and wizard.can_edit_wizard
                and wizard.batches
            ):
                batch = wizard.batches[0]

                original_net_amount = 0.0
                original_discount_amount = 0.0

                for line in batch["lines"]:
                    if line.move_id._is_eligible_for_early_payment_discount(
                        wizard.currency_id, wizard.payment_date
                    ):
                        net, discount = wizard._get_dynamic_net_and_discount(
                            line, wizard.payment_date
                        )
                        original_net_amount += net
                        original_discount_amount += discount

                if wizard.currency_id.is_zero(original_net_amount):
                    continue

                ratio = wizard.amount / original_net_amount
                proportional_discount = original_discount_amount * ratio
                wizard.payment_difference = proportional_discount

    def _create_payment_vals_from_wizard(self, batch_result):
        """
        Override to inject proportional EPD write-off lines with dynamic discount calculation.

        Passes payment_date and invoice_date in context to ensure dynamic discount
        percentage selection, then generates and injects scaled write-off lines
        for proportional discount application.

        :param batch_result: Payment batch dictionary
        :return: Payment values dictionary with scaled write-off lines
        """
        # Pass dates in context for any underlying standard method calls
        ctx = dict(self.env.context)
        ctx["payment_date"] = self.payment_date
        invoice_date = (
            batch_result["lines"][0].move_id.invoice_date
            if batch_result["lines"]
            else None
        )
        if invoice_date:
            ctx["invoice_date"] = invoice_date

        payment_vals = super(
            AccountPaymentRegister, self.with_context(**ctx)
        )._create_payment_vals_from_wizard(batch_result)

        if self.early_payment_discount_mode:
            total_amount_values = self._get_total_amounts_to_pay([batch_result])
            scaled_lines = self._get_proportional_epd_writeoff_lines(
                batch_result, total_amount_values
            )
            payment_vals["write_off_line_vals"] = scaled_lines

        return payment_vals
