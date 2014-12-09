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
from openerp.tools.translate import _
from datetime import datetime

class account_voucher(osv.osv):
    # inherit = herencia
    _inherit ='account.voucher'
 
    # Acá se sobreescribe este método el cual está en la clase original. ¡Este valida un pago de factura de clientes!
    def action_move_line_create(self, cr, uid, ids, context=None):
        '''
        Confirm the vouchers given in ids and create the journal entries for each of them
        '''
        if context is None:
            context = {}
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
	# new
	asiento_obj = self.pool.get('account.voucher')
	account_voucher_line = self.pool.get('account.voucher.line')
        move_line = self.pool.get('account.move.line')
        account_invoice = self.pool.get('account.invoice')
	account_move = self.pool.get('account.move')
	datos_medidor_obj = self.pool.get('datos.medidor')
        id_asiento_contable = 0
	caso_activo_reconexion = False
	id_apunte = 0
	ln = []
	moroso = []
	numero_medidor = []
        fecha_voucher = ""
        fecha_vencimiento = ""
	# ---
        for voucher in self.browse(cr, uid, ids, context=context):
	    for apunte in asiento_obj.read(cr,uid,[voucher.id],context=context):
		    fecha_voucher = str(apunte['date'])
		    id_voucher_move_line = account_voucher_line.read(cr,uid,apunte['line_cr_ids'],context=context)
		    for mv in id_voucher_move_line:
		        id_apunte = int(mv['move_line_id'][0])
			for ap in move_line.read(cr,uid,[id_apunte],context=context):
				id_asiento_contable = int(ap['move_id'][0])
				id_invoice = account_invoice.search(cr, uid, [('move_id', '=', id_asiento_contable )])
				for inv in account_invoice.read(cr,uid,id_invoice,context=context):

					# ************************* VALIDACIONES ****************************
					# Busco el ultimo periodo generado.
					cr.execute('select max(id) from genera_lecturas')
					id_ = cr.dictfetchone()
					dict_lotes = self.pool.get('genera.lecturas').read(cr,uid,[id_['max']],context=context)[0]
					id_period = [dict_lotes['periodo_id'][0]] 
					dict_period = self.pool.get('account.period').read(cr,uid,id_period,context=context)[0]
					period_generated_end = int(str(dict_period['code']).split('/')[0])
					period_act = int(str(inv['period_id'][1]).split('/')[0])
					# ********************************************************************
					fecha_vencimiento = str(inv['date_due'])
					if fecha_voucher > fecha_vencimiento:
						moroso.append(1)
						numero_medidor.append(inv['numero_medidor'])
					#Aquí validar si el medidor esta moroso, favor cambiar a estado no moroso y crear la línea de reconexión.
					id_medidor = datos_medidor_obj.search(cr, uid, [('numero_medidor', '=', inv['numero_medidor'] )])		
					for x in datos_medidor_obj.read(cr,uid,id_medidor,context=context):
						
						if x['estado_moroso'] == True and x['activar_linea_cr'] == False:
							# ANTES de aplicar esto, se debe validar si en registros históricos hay más periodos del mismo medidor al cobro, con morosidad...
							med_morosos = self.pool.get('registro.historico').search(cr, uid, [('numero_medidor', '=', x['id']),('estado','=','al_cobro')]) 
							ln = self.pool.get('registro.historico').browse(cr, uid, med_morosos, context=context)
							if len(ln) == 1:
								datos_medidor_obj.write(cr, uid, [x['id']], {'estado_moroso': False, 'activar_reconexion': True, 'activar_linea_cr': False, 'estado': True})
								caso_activo_reconexion = True
	    if moroso != []:
		for nm in numero_medidor:
		#En esta parte cuando la fecha de pago sea mayor a la de vencimiento, no tenga activo el medidor el check de "Activar reconexión" y no se ha generado presupuestos, se debe activar el estado de línea cr(corta y reconexión)
			if caso_activo_reconexion == False:
				if period_generated_end == period_act and ln == 1:
					cr.execute('update datos_medidor set activar_linea_cr = True where numero_medidor='+str(nm)+'')

		# A partir de aquí se realiza el pago de la factura normalmente.
		if voucher.move_id:
		        continue
		company_currency = self._get_company_currency(cr, uid, voucher.id, context)
	        current_currency = self._get_current_currency(cr, uid, voucher.id, context)
		# we select the context to use accordingly if it's a multicurrency case or not
		context = self._sel_context(cr, uid, voucher.id, context)
		# But for the operations made by _convert_amount, we always need to give the date in the context
		ctx = context.copy()
		ctx.update({'date': voucher.date})
		# Create the account move record.
		move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, voucher.id, context=context), context=context)
		print 
		# Get the name of the account_move just created
		name = move_pool.browse(cr, uid, move_id, context=context).name
		# Create the first line of the voucher
		move_line_id = move_line_pool.create(cr, uid, self.first_move_line_get(cr,uid,voucher.id, move_id, company_currency, current_currency, context), context)
		move_line_brw = move_line_pool.browse(cr, uid, move_line_id, context=context)
		line_total = move_line_brw.debit - move_line_brw.credit
		rec_list_ids = []
		if voucher.type == 'sale':
			line_total = line_total - self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
		elif voucher.type == 'purchase':
		        line_total = line_total + self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
		# Create one move line per voucher line where amount is not 0.0
		line_total, rec_list_ids = self.voucher_move_line_create(cr, uid, voucher.id, line_total, move_id, company_currency, current_currency, context)

	        # Create the writeoff line if needed
		ml_writeoff = self.writeoff_move_line_get(cr, uid, voucher.id, line_total, move_id, name, company_currency, current_currency, context)
		if ml_writeoff:
		        move_line_pool.create(cr, uid, ml_writeoff, context)
		# We post the voucher.
		self.write(cr, uid, [voucher.id], {
		        'move_id': move_id,
		        'state': 'posted',
		        'number': name,
		})
		if voucher.journal_id.entry_posted:
		        move_pool.post(cr, uid, [move_id], context={})
		# We automatically reconcile the account move lines.
		reconcile = False
		for rec_ids in rec_list_ids:
			if len(rec_ids) >= 2:
		            reconcile = move_line_pool.reconcile_partial(cr, uid, rec_ids, writeoff_acc_id=voucher.writeoff_acc_id.id, writeoff_period_id=voucher.period_id.id, writeoff_journal_id=voucher.journal_id.id)

	    else:
		    if voucher.move_id:
		        continue
		    company_currency = self._get_company_currency(cr, uid, voucher.id, context)
		    current_currency = self._get_current_currency(cr, uid, voucher.id, context)
		    # we select the context to use accordingly if it's a multicurrency case or not
		    context = self._sel_context(cr, uid, voucher.id, context)
		    # But for the operations made by _convert_amount, we always need to give the date in the context
		    ctx = context.copy()
		    ctx.update({'date': voucher.date})
		    # Create the account move record.
		    move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, voucher.id, context=context), context=context)
		    print 
		    # Get the name of the account_move just created
		    name = move_pool.browse(cr, uid, move_id, context=context).name
		    # Create the first line of the voucher
		    move_line_id = move_line_pool.create(cr, uid, self.first_move_line_get(cr,uid,voucher.id, move_id, company_currency, current_currency, context), context)
		    move_line_brw = move_line_pool.browse(cr, uid, move_line_id, context=context)
		    line_total = move_line_brw.debit - move_line_brw.credit
		    rec_list_ids = []
		    if voucher.type == 'sale':
		        line_total = line_total - self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
		    elif voucher.type == 'purchase':
		        line_total = line_total + self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
		    # Create one move line per voucher line where amount is not 0.0
		    line_total, rec_list_ids = self.voucher_move_line_create(cr, uid, voucher.id, line_total, move_id, company_currency, current_currency, context)

		    # Create the writeoff line if needed
		    ml_writeoff = self.writeoff_move_line_get(cr, uid, voucher.id, line_total, move_id, name, company_currency, current_currency, context)
		    if ml_writeoff:
		        move_line_pool.create(cr, uid, ml_writeoff, context)
		    # We post the voucher.
		    self.write(cr, uid, [voucher.id], {
		        'move_id': move_id,
		        'state': 'posted',
		        'number': name,
		    })
		    if voucher.journal_id.entry_posted:
		        move_pool.post(cr, uid, [move_id], context={})
		    # We automatically reconcile the account move lines.
		    reconcile = False
		    for rec_ids in rec_list_ids:
		        if len(rec_ids) >= 2:
		            reconcile = move_line_pool.reconcile_partial(cr, uid, rec_ids, writeoff_acc_id=voucher.writeoff_acc_id.id, writeoff_period_id=voucher.period_id.id, writeoff_journal_id=voucher.journal_id.id)	    
		    
            return True

    # Métodos para el recibo de pago
    def linea_pago(self, cr, uid, ids, context=None):
	datos = {}
	res = []
	numero_factura = ''
	monto = 0
	for l in self.browse(cr, uid,ids,context=None):
		#print "\n"+str(l)+"\n"	
		linea_pago = l.line_cr_ids
		for ln in linea_pago:
			numero_factura = ln.name
			monto = ln.amount
			if monto != 0:
				datos = {'numero': numero_factura, 'monto': int(monto)}
				res.append(datos)
	return res
    # Calculo de total pago
    def total_pagado(self, cr, uid, ids, context=None):
	monto_total = 0
	for l in self.browse(cr, uid,ids,context=None):
		linea_pago = l.line_cr_ids
		for ln in linea_pago:
			monto_total += ln.amount
	return int(monto_total)
    # Formato para fecha
    def formato_fecha(self, cr, uid, ids, context=None):
	fecha  = ''
	for f in self.browse(cr, uid,ids,context=None):
		fecha = f.date
	f = datetime.strptime(fecha, '%Y-%m-%d')
	formato= f.strftime('%d/%m/%Y')
	return formato	

    def get_periodo(self, cr, uid, ids, context=None):
	'''Metodo para calcular el periodo en la impresion de los reportes, toma el period_id y le hace un split, luego le resta uno al
	mes y si el mes es enero tambien le resta un 1 al año
	'''
	res = {}
	data = self.browse(cr, uid, ids, context=context)[0]
	var =  (str(data.period_id.name)).split('/')

	mes=int(var[0])
	year=int(var[1])

	year_val=0

	if mes ==1:
		mes=12
		year_val=year-1
	else:
		mes=mes-1
		year_val=year

	mes_letras="ENERO"

	if mes==1:
		mes_letras="ENERO"
	if mes==2:
		mes_letras="FEBRERO"
	if mes==3:
		mes_letras="MARZO"
	if mes==4:
		mes_letras="ABRIL"
	if mes==5:
		mes_letras="MAYO"
	if mes==6:
		mes_letras="JUNIO"
	if mes==7:
		mes_letras="JULIO"
	if mes==8:
		mes_letras="AGOSTO"
	if mes==9:
		mes_letras="SETIEMBRE"
	if mes==10:
		mes_letras="OCTUBRE"
	if mes==11:
		mes_letras="NOVIEMBRE"
	if mes==12:
		mes_letras="DICIEMBRE"

	ret=str(mes_letras)+"/"+str(year_val)

	return ret

account_voucher()
