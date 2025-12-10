from odoo import models, api


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _get_total_amounts_to_pay(self, batch_results):
        """
        Override to recalculate net amount when EPD is active with partial payments.

        Standard calculation uses static 'discount_amount_currency' from invoice lines,
        which doesn't update dynamically after partial payments. This override recalculates
        the suggested payment amount based on current residual and discount percentage.

        :param batch_results: List of payment batches
        :return: Dictionary with recalculated 'amount_by_default' and other EPD values
        """
        total_amount_values = super()._get_total_amounts_to_pay(batch_results)

        # Recalculate amount_by_default (Net to Pay) if EPD is active and we have partials
        if total_amount_values["epd_applied"]:
            new_amount_by_default = 0.0

            for line in total_amount_values["lines"]:
                # Move is eligible (checked by super or our override)
                if line.move_id._is_eligible_for_early_payment_discount(
                    self.currency_id, self.payment_date
                ):
                    # Current Residual (Debt)
                    residual = line.amount_residual_currency
                    term = line.move_id.invoice_payment_term_id
                    discount_percentage = term.discount_percentage or 0.0

                    if discount_percentage:
                        if term.early_pay_discount_computation in ("excluded", "mixed"):
                            # Calculate Total Original Discount Amount
                            total_original_discount = abs(line.amount_currency) - abs(
                                line.discount_amount_currency
                            )
                            total_original_gross = abs(line.amount_currency)

                            if total_original_gross:
                                remaining_ratio = abs(residual) / total_original_gross
                                remaining_discount = (
                                    total_original_discount * remaining_ratio
                                )
                                new_amount_by_default += (
                                    abs(residual) - remaining_discount
                                )
                            else:
                                new_amount_by_default += abs(residual)
                        else:
                            net_to_pay = residual * (1 - (discount_percentage / 100.0))
                            new_amount_by_default += net_to_pay
                    else:
                        new_amount_by_default += residual
                else:
                    # Non-eligible lines (overdue etc)
                    new_amount_by_default += line.amount_residual_currency

            # Update the suggestion if different
            if self.currency_id:
                new_amount_by_default = self.currency_id.round(new_amount_by_default)

            total_amount_values["amount_by_default"] = new_amount_by_default

        return total_amount_values

    @api.depends("can_edit_wizard", "payment_date", "currency_id", "amount")
    def _compute_early_payment_discount_mode(self):
        """
        Override to enable EPD mode for partial payment amounts.

        Standard behavior only activates EPD mode if amount matches exactly the full
        discounted or full gross amount. This override allows EPD mode for any non-zero
        amount when discount is applicable, enabling proportional discounts.
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

            # Check if EPD would apply if we ignored the amount mismatch
            total_amount_values = wizard._get_total_amounts_to_pay(wizard.batches)

            if total_amount_values["epd_applied"]:
                # Allow EPD even for partial amounts
                # But only if amount is not zero (avoid div by zero later)
                if not wizard.currency_id.is_zero(wizard.amount):
                    wizard.early_payment_discount_mode = True

    @api.depends("early_payment_discount_mode")
    def _compute_payment_difference_handling(self):
        """
        Override to set correct handling mode for partial EPD payments.

        For partial payments with EPD, sets handling to 'open' (keep invoice open)
        instead of 'reconcile' (mark as fully paid), since debt remains after partial payment.
        """
        super()._compute_payment_difference_handling()
        for wizard in self:
            if wizard.early_payment_discount_mode and wizard.can_edit_wizard:
                # Standard sets it to 'reconcile' (Mark as fully paid).
                # We want 'open' if it's a partial payment.
                total_amount_values = wizard._get_total_amounts_to_pay(wizard.batches)
                amount_by_default = total_amount_values["amount_by_default"]

                # If amount is strictly less than the full discounted amount, keep open
                # Using 0.01 tolerance just in case, or strict compare
                if (
                    wizard.currency_id.compare_amounts(wizard.amount, amount_by_default)
                    == -1
                ):
                    wizard.payment_difference_handling = "open"

    @api.depends("can_edit_wizard", "amount", "installments_mode")
    def _compute_payment_difference(self):
        """
        Override to calculate proportional discount amount for display in wizard.

        The 'payment_difference' field is displayed as "Early Payment Discount of X"
        in the UI. This override calculates X as a proportional discount based on
        the ratio: (Amount Paid / Original Net Amount) * Total Discount.
        """
        super()._compute_payment_difference()
        for wizard in self:
            if (
                wizard.early_payment_discount_mode
                and wizard.can_edit_wizard
                and wizard.batches
            ):
                # We calculate proportional discount for ALL EPD cases (partial or full)
                # to ensure consistency (e.g. final partial payment).

                batch = wizard.batches[0]

                original_net_amount = 0.0
                original_discount_amount = 0.0
                for line in batch["lines"]:
                    if line.move_id._is_eligible_for_early_payment_discount(
                        wizard.currency_id, wizard.payment_date
                    ):
                        original_net_amount += abs(line.discount_amount_currency)
                        original_discount_amount += abs(line.amount_currency) - abs(
                            line.discount_amount_currency
                        )

                if wizard.currency_id.is_zero(original_net_amount):
                    continue

                ratio = wizard.amount / original_net_amount

                proportional_discount = original_discount_amount * ratio
                wizard.payment_difference = proportional_discount

    def _calculate_proportional_epd_ratio(self, batch_result):
        """
        Calculate the payment ratio for proportional EPD based on Original Net Amount.

        Use the Original Net Amount (discount_amount_currency) stored on the AMLs
        as the denominator to ensure consistent ratio calculation across partial payments.

        :param batch_result: Payment batch containing lines
        :return: Ratio (Amount Paid / Original Net Amount)
        """
        original_net_amount = 0.0
        for line in batch_result["lines"]:
            # Check if line is EPD eligible to include in base
            if line.move_id._is_eligible_for_early_payment_discount(
                self.currency_id, self.payment_date
            ):
                # discount_amount_currency holds the Original Net (Discounted) Amount
                # It is usually static and doesn't update with partials.
                # We use abs() to handle credit/debit signs correctly.
                original_net_amount += abs(line.discount_amount_currency)

        if not self.currency_id.is_zero(original_net_amount):
            return self.amount / original_net_amount
        return 0.0

    def _prepare_epd_aml_values(self, batch_result):
        """
        Prepare EPD account move line values for eligible lines.

        :param batch_result: Payment batch dictionary
        :return: List of EPD AML value dictionaries
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
        Calculate the full discount balance for EPD write-off.

        :param total_amount_values: Dictionary with amount values
        :return: Open balance in company currency
        """
        full_discount_amount = (
            total_amount_values["amount_for_difference"]
            - total_amount_values["amount_by_default"]
        )
        sign = -1 if self.payment_type == "outbound" else 1
        open_amount_currency = full_discount_amount * sign

        return self.currency_id._convert(
            open_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.payment_date,
        )

    def _scale_epd_writeoff_lines(self, early_payment_values, ratio):
        """
        Scale EPD write-off lines by proportional ratio.

        :param early_payment_values: Dictionary of EPD write-off line values
        :param ratio: Proportional ratio to scale by
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
        Generate proportional EPD write-off lines.

        :param batch_result: Payment batch dictionary
        :param total_amount_values: Dictionary with calculated amounts
        :return: List of write-off line values
        """
        # Calculate ratio based on Original Net Amount (consistent across partials)
        ratio = self._calculate_proportional_epd_ratio(batch_result)

        epd_aml_values_list = self._prepare_epd_aml_values(batch_result)
        open_balance = self._calculate_full_discount_balance(total_amount_values)

        early_payment_values = self.env[
            "account.move"
        ]._get_invoice_counterpart_amls_for_early_payment_discount(
            epd_aml_values_list, open_balance
        )

        return self._scale_epd_writeoff_lines(early_payment_values, ratio)

    def _create_payment_vals_from_wizard(self, batch_result):
        """
        Override to inject proportional EPD write-off lines for partial payments.

        When a partial payment is made with EPD active, this method:
        1. Calculates the payment ratio relative to net amount (Amount Paid / Net Amount)
        2. Retrieves full EPD write-off lines from standard Odoo method
        3. Scales those write-off lines by the calculated ratio
        4. Injects them into payment vals for proper accounting

        This ensures partial payments receive proportional discount application.

        :param batch_result: Payment batch dictionary containing lines and values
        :return: Payment values dictionary with scaled write-off lines
        """
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)

        if self.early_payment_discount_mode:
            # Always apply proportional logic when EPD is active.
            # This covers partial payments and the final "full" payment (which Odoo might miscalculate as full original discount).
            # Since our logic handles 100% ratio correctly, it's safe to use universally for EPD.

            total_amount_values = self._get_total_amounts_to_pay([batch_result])
            scaled_lines = self._get_proportional_epd_writeoff_lines(
                batch_result, total_amount_values
            )

            # Overwrite any standard write-off lines with our correct proportional ones
            payment_vals["write_off_line_vals"] = scaled_lines

        return payment_vals
