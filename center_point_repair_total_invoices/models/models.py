# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import models, fields, _
from odoo.exceptions import UserError


class MakeTotalInvoice(models.TransientModel):
    _inherit = 'repair.order.make_invoice'

    def make_total_invoices(self):

        # We have to update the state of the given repairs, otherwise they remain 'to be invoiced'.
        # Note that this will trigger another call to the method '_create_invoices',
        # but that second call will not do anything, since the repairs are already invoiced.

        if not self._context.get('active_ids'):
            return {'type': 'ir.actions.act_window_close'}
        new_invoice = {}
        for wizard in self:
            repairs = self.env['repair.order'].browse(self._context['active_ids']).filtered(
                lambda repair: repair.state not in ('draft', 'cancel')
                               and not repair.invoice_id
                               and repair.invoice_method != 'none')
            group = wizard.group
            grouped_invoices_vals = {}
            fr_repair = repairs[0]
            repair = fr_repair.with_company(fr_repair.company_id)
            partner_invoice = repair.partner_invoice_id or repair.partner_id
            if not partner_invoice:
                raise UserError(_('You have to select an invoice address in the repair form.'))

            narration = repair.quotation_notes
            currency = repair.pricelist_id.currency_id
            company = repair.env.company

            journal = repair.env['account.move'].with_context(type='out_invoice')._get_default_journal()
            if not journal:
                raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (
                    company.name, company.id))

            if (partner_invoice.id, currency.id) not in grouped_invoices_vals:
                grouped_invoices_vals[(partner_invoice.id, currency.id, company.id)] = []
            current_invoices_list = grouped_invoices_vals[(partner_invoice.id, currency.id, company.id)]

            if not group or len(current_invoices_list) == 0:
                fpos = self.env['account.fiscal.position'].get_fiscal_position(partner_invoice.id,
                                                                               delivery_id=repair.address_id.id)
                invoice_vals = {
                    'move_type': 'out_invoice',
                    'partner_id': partner_invoice.id,
                    'partner_shipping_id': repair.address_id.id,
                    'currency_id': currency.id,
                    'narration': narration,
                    'line_ids': [],
                    'invoice_origin': repair.name,
                    'repair_ids': [(4, repair.id)],
                    'invoice_line_ids': [],
                    'fiscal_position_id': fpos.id
                }
                if partner_invoice.property_payment_term_id:
                    invoice_vals['invoice_payment_term_id'] = partner_invoice.property_payment_term_id.id
                current_invoices_list.append(invoice_vals)
            else:
                # if group == True: concatenate invoices by partner and currency
                invoice_vals = current_invoices_list[0]
                invoice_vals['invoice_origin'] += ', ' + repair.name
                invoice_vals['repair_ids'].append((4, repair.id))
                if not invoice_vals['narration']:
                    invoice_vals['narration'] = narration
                else:
                    invoice_vals['narration'] += '\n' + narration

            for repair in repairs:
                print('partner_id... ', repair.partner_id.name)
                print('partner_invoice_id... ', repair.partner_invoice_id.name)
                # Create invoice lines from operations.
                for operation in repair.operations.filtered(lambda op: op.type == 'add'):
                    if group:
                        name = repair.name + '-' + operation.name
                    else:
                        name = operation.name

                    account = operation.product_id.product_tmpl_id._get_product_accounts()['income']
                    if not account:
                        raise UserError(_('No account defined for product "%s".', operation.product_id.name))

                    invoice_line_vals = {
                        'name': name,
                        'account_id': account.id,
                        'quantity': operation.product_uom_qty,
                        'tax_ids': [(6, 0, operation.tax_id.ids)],
                        'product_uom_id': operation.product_uom.id,
                        'price_unit': operation.price_unit,
                        'product_id': operation.product_id.id,
                        'partner_project': repair.new_field_project_id.id,
                        'repair_line_ids': [(4, operation.id)],
                    }

                    if currency == company.currency_id:
                        balance = -(operation.product_uom_qty * operation.price_unit)
                        invoice_line_vals.update({
                            'debit': balance > 0.0 and balance or 0.0,
                            'credit': balance < 0.0 and -balance or 0.0,
                        })
                    else:
                        amount_currency = -(operation.product_uom_qty * operation.price_unit)
                        balance = currency._convert(amount_currency, company.currency_id, company, fields.Date.today())
                        invoice_line_vals.update({
                            'amount_currency': amount_currency,
                            'debit': balance > 0.0 and balance or 0.0,
                            'credit': balance < 0.0 and -balance or 0.0,
                            'currency_id': currency.id,
                        })
                    invoice_vals['invoice_line_ids'].append((0, 0, invoice_line_vals))

                # Create invoice lines from fees.
                for fee in repair.fees_lines:
                    if group:
                        name = repair.name + '-' + fee.name
                    else:
                        name = fee.name

                    if not fee.product_id:
                        raise UserError(_('No product defined on fees.'))

                    account = fee.product_id.product_tmpl_id._get_product_accounts()['income']
                    if not account:
                        raise UserError(_('No account defined for product "%s".', fee.product_id.name))

                    invoice_line_vals = {
                        'name': name,
                        'account_id': account.id,
                        'quantity': fee.product_uom_qty,
                        'tax_ids': [(6, 0, fee.tax_id.ids)],
                        'product_uom_id': fee.product_uom.id,
                        'price_unit': fee.price_unit,
                        'product_id': fee.product_id.id,
                        'partner_project': repair.new_field_project_id.id,
                        'repair_fee_ids': [(4, fee.id)],
                    }

                    if currency == company.currency_id:
                        balance = -(fee.product_uom_qty * fee.price_unit)
                        invoice_line_vals.update({
                            'debit': balance > 0.0 and balance or 0.0,
                            'credit': balance < 0.0 and -balance or 0.0,
                        })
                    else:
                        amount_currency = -(fee.product_uom_qty * fee.price_unit)
                        balance = currency._convert(amount_currency, company.currency_id, company,
                                                    fields.Date.today())
                        invoice_line_vals.update({
                            'amount_currency': amount_currency,
                            'debit': balance > 0.0 and balance or 0.0,
                            'credit': balance < 0.0 and -balance or 0.0,
                            'currency_id': currency.id,
                        })
                    invoice_vals['invoice_line_ids'].append((0, 0, invoice_line_vals))
            new_invoice = self.env['account.move'].with_company(company).with_context(default_company_id=company.id,
                                                                        default_move_type='out_invoice').create(
                invoice_vals)

            repairs.write({'invoiced': True,
                           'state': 'done'})
            repairs.mapped('operations').filtered(lambda op: op.type == 'add').write({'invoiced': True})
            repairs.mapped('fees_lines').write({'invoiced': True})

        return {
            'res_id': new_invoice.id,
            'name': 'Invoices',
            'view_mode': 'form',
            'res_model': 'account.move',
            'view_id': self.env.ref('account.view_move_form').id,
            'views': [(self.env.ref('account.view_move_form').id, 'form')],
            'context': "{'move_type':'out_invoice'}",
            'type': 'ir.actions.act_window'
        }




    # def _create_invoice(self, group=False):
    #     """ Creates invoice(s) for repair order.
    #     @param group: It is set to true when group invoice is to be generated.
    #     @return: Invoice Ids.
    #     """
    #     grouped_invoices_vals = {}
    #     repairs = self.filtered(lambda repair: repair.state not in ('draft', 'cancel')
    #                                            and not repair.invoice_id
    #                                            and repair.invoice_method != 'none')

    #     # Create invoices.
    #     invoices_vals_list_per_company = defaultdict(list)
    #     for (partner_invoice_id, currency_id, company_id), invoices in grouped_invoices_vals.items():
    #         for invoice in invoices:
    #             invoices_vals_list_per_company[company_id].append(invoice)
    #
    #     for company_id, invoices_vals_list in invoices_vals_list_per_company.items():
    #         # VFE TODO remove the default_company_id ctxt key ?
    #         # Account fallbacks on self.env.company, which is correct with with_company
    #         self.env['account.move'].with_company(company_id).with_context(default_company_id=company_id,
    #                                                                        default_move_type='out_invoice').create(
    #             invoices_vals_list)
    #
    #     repairs.write({'invoiced': True})
    #     repairs.mapped('operations').filtered(lambda op: op.type == 'add').write({'invoiced': True})
    #     repairs.mapped('fees_lines').write({'invoiced': True})
    #
    #     return dict((repair.id, repair.invoice_id.id) for repair in repairs)
