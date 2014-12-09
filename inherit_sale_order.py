# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2013 D.I.S S.A. (http://www.dis.co.cr) All Rights Reserved.
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields, osv
import time
from openerp import netsvc
from openerp.tools.translate import _

class sale_order(osv.osv):
    # inherit = herencia
    _inherit ='sale.order'
    _columns = {
	'numero_abonado': fields.integer('Número abonado', readonly="True"),
	'numero_medidor': fields.integer('Número medidor', readonly="True"),
	'unidades_habitacionales': fields.integer('Unidades habitacionales', readonly="True"),
	'periodo_id': fields.many2one('genera.facturas','Periodo'),
	'registro_id': fields.many2one('registro.historico','Registro'),
	'fecha_vencimiento': fields.date('Fecha vencimiento'),
    }

    # Acá se sobreescribe este método el cual está en la clase original. ¡Este genera una factura de cliente!
    def _prepare_invoice(self, cr, uid, order, lines, context=None):

        """Prepare the dict of values to create the new invoice for a
           sales order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: sale.order record to invoice
           :param list(int) line: list of invoice line IDs that must be
                                  attached to the invoice
           :return: dict of value to create() the invoice
        """
        if context is None:
            context = {}
        journal_ids = self.pool.get('account.journal').search(cr, uid,
            [('type', '=', 'sale'), ('company_id', '=', order.company_id.id)],
            limit=1)
        if not journal_ids:
            raise osv.except_osv(_('Error!'),
                _('Please define sales journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))
        invoice_vals = {
            'name': order.client_order_ref or '',
            'origin': order.name,
            'type': 'out_invoice',
            'reference': order.client_order_ref or order.name,
            'account_id': order.partner_id.property_account_receivable.id,
            'partner_id': order.partner_invoice_id.id,
            'journal_id': journal_ids[0],
            'invoice_line': [(6, 0, lines)],
            'currency_id': order.pricelist_id.currency_id.id,
            'comment': order.note,
            'payment_term': order.payment_term and order.payment_term.id or False,
            'fiscal_position': order.fiscal_position.id or order.partner_id.property_account_position.id,
            'date_invoice': context.get('date_invoice', False),
            'company_id': order.company_id.id,
            'user_id': order.user_id and order.user_id.id or False,
            # Nuevos en factura 
	    'numero_abonado': order.numero_abonado,
	    'numero_medidor': order.numero_medidor,
	    'unidades_habitacionales': order.unidades_habitacionales,
	    'periodo_id': order.periodo_id.id,
	    'registro_id': order.registro_id.id,
	    'fecha_vencimiento': order.fecha_vencimiento,
	    'date_due': order.fecha_vencimiento, 
        }
	#print "INVOICE - VALS: " + str(invoice_vals)
        # Care for deprecated _inv_get() hook - FIXME: to be removed after 6.1
        invoice_vals.update(self._inv_get(cr, uid, order, context=context))
        return invoice_vals
sale_order()
