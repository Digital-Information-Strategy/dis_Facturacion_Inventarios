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
from openerp import netsvc
from datetime import datetime
from datetime import *

# Esta clase permite validar presupuestos en estado borrador para posteriormente pasar a un estado de pedido de venta, donde se procederá a la facturación del mismo.
class valida_presupuestos(osv.osv):
    _name ='valida.presupuestos'
    _columns = {
	'name': fields.char('Fecha creación', size=64),
	'order_line': fields.one2many('valida.presupuestos.linea', 'orders_id', 'Order Lines'),
	'estado_validaciones': fields.selection([('draft','Borrador'),('presupuestos','Presupuestos'),('pedido_venta','Pedidos de Ventas'),('done','Facturado')], 'Estado'),
	'cant': fields.integer('Cantidad a confirmar'),
    }
    _defaults = {'estado_validaciones': 'draft', 'cant': 80}

    # Carga los presupuestos en estado borrador.
    def cargar_presupuestos(self, cr, uid, ids, context=None):
	id_form = 0
	for id in ids:
		id_form = id
	sale_obj = self.pool.get('sale.order')
	linea_presupuestos = []
	res = {}
	# Busca en la base de datos los presupuestos que están en estado borrador.
	ids_sale = sale_obj.search(cr, uid, [('state', '=', 'draft')])
	# Recorre el ids_sale
	for p in sale_obj.read(cr,uid,ids_sale,context=context):
		linea_presupuestos.append((0,0,{'orders_id': id_form,'name': p['name'],'date_order': p['date_order'],'partner_id': p['partner_id'][0] , 'user_id':  p['user_id'][0], 'amount_total': p['amount_total'], 'state': p['state'], 'id_sale_order': p['id']}))
	res.update({'order_line': linea_presupuestos,'estado_validaciones': 'presupuestos','name': str(datetime.now().strftime('%Y-%m-%d'))})  
	self.write(cr,uid,ids,res)
	return True	
    # Proceso para confirmar (validar) los presupuestos y pasar a un estado de pedido de ventas.
    def confirmar_presupuestos(self,cr,uid,ids,context=None):
	id_form = []
	linea_presupuestos = []
	unl=[]
	cont=0
	for a in self.browse(cr, uid, ids, context=None):
		limit=(a.cant == 0 and 80 or a.cant)		
		for b in a.order_line:
			if b.state=='draft':	
				id_form.append(b.id_sale_order.id)
				unl.append(b.id)
				cont+=1
				if cont ==limit:
					break
	for x_ids in id_form:
		#assert len(ids) == 1, 'This option should only be used for a single id at a time.'
		wf_service = netsvc.LocalService('workflow')
		wf_service.trg_validate(uid, 'sale.order', x_ids, 'order_confirm', cr)
		# redisplay the record as a sales order
		view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sale', 'view_order_form')
		view_id = view_ref and view_ref[1] or False,
		res = {
		    'type': 'ir.actions.act_window',
		    'name': _('Sales Order'),
		    'res_model': 'sale.order',
		    'res_id': x_ids,
		    'view_type': 'form',
		    'view_mode': 'form',
		    'view_id': view_id,
		    'target': 'current',
		    'nodestroy': True,
		}

	lineas = self.pool.get('valida.presupuestos.linea')
	lineas.write(cr,uid,unl,{'state':'manual','confirm':True})
	caant = lineas.search(cr, uid, [('state', '=', 'draft'),('orders_id','=',ids[0])])

	if len(caant)==0:
		self.write(cr,uid,ids,{'estado_validaciones':'pedido_venta'})
	return True
    # Crea facturas generados desde pedidos de ventas.
    def crear_facturas(self,cr,uid,ids,context=None):
	id_form = []
	invoice_vals = {}
	account_id = 0
	currency_id = 0
	fiscal_position = 0
	periodo_id = 0
	registro_id = 0
	e_mail = False
	impreso  = False
	unl=[]
	cont=0
	#dias_fact = 0
	reg_ = []
	sale_obj = self.pool.get('sale.order')
	sale_line_obj = self.pool.get('sale.order.line')
	partner_obj = self.pool.get('res.partner')
	currency_obj = self.pool.get('product.pricelist')
	product_obj = self.pool.get('product.product')
	lineas = self.pool.get('valida.presupuestos.linea')
	
	id_sale_order = 0
	for id_sale in ids:
		id_sale_order = id_sale

	for a in self.browse(cr, uid, ids, context=None):
		limit=(a.cant == 0 and 80 or a.cant)
		for b in a.order_line:
		    if b.state=='manual':		
			id_form.append(b.id_sale_order.id)
			unl.append(b.id)
			cont+=1
			if cont ==limit:
				break
	#lines = len(id_form) # Cantidad de línea a facturar

	for id_linea in id_form:
		for order in sale_obj.read(cr,uid,[id_linea],context=context):
			# Buscar cuenta contable del cliente
			datos_partner = partner_obj.search(cr, uid, [('id', '=',order['partner_id'][0])])
			for p in partner_obj.read(cr,uid,datos_partner,context=context):	
				account = str(p['property_account_receivable'][0]).replace("L",'')
				account_id = int(account)
				fiscal_position = p['property_account_position']
				e_mail = p['e_mail']
				impreso = p['impreso']
			# Buscar moneda
			datos_moneda = currency_obj.search(cr, uid, [('id', '=',order['pricelist_id'][0])])
			for c in currency_obj.read(cr,uid,datos_moneda,context=context):
				currency_id = c['currency_id'][0]
			# Para el diario
			if context is None:
            			context = {}
        		journal_ids = self.pool.get('account.journal').search(cr, uid, [('type', '=', 'sale'), ('company_id', '=', order['company_id'][0])], limit=1)
        		if not journal_ids:
           			raise osv.except_osv(_('Error!'),_('Please define sales journal for this company: "%s" (id:%d).') % (order['company_id'][1], order['company_id'][0]))

			periodo_id = order['periodo_id']
			if periodo_id == False:
				periodo_id = 0
			else:
				periodo_id = order['periodo_id'][0]
			registro_id = order['registro_id']
			if registro_id == False:
				registro_id = 0
			else:
				registro_id = order['registro_id'][0]

			#Acceder a datos de los registros historicos.
			if registro_id != 0:
				domain = self.pool.get('registro.historico').search(cr, uid, [('id', '=', registro_id)])
				reg = self.pool.get('registro.historico').read(cr, uid, domain)
				# sacar el registro historico del periodo anterior.
				periodo = str(reg[0]['lote_id'][1]).split('/')
				mes=int(periodo[0])
				year=int(periodo[1])
				year_val=0
				if mes ==1:
					mes=12
					year_val=year-1
				else:
					mes=mes-1
					year_val=year
				#Union del mes y año
				if mes < 10:
					mes = "0"+str(mes)
				
				periodo = str(mes)+"/"+str(year_val)
				id_periodo = self.pool.get('account.period').search(cr, uid, [('name', '=', periodo)])
				periodo_ = self.pool.get('account.period').read(cr, uid, id_periodo)
				periodo_id_ = periodo_[0]['id']
				id_lote = self.pool.get('genera.lecturas').search(cr, uid, [('periodo_id', '=', periodo_id_ )])
				lote_ = self.pool.get('genera.lecturas').read(cr, uid, id_lote)
				lote_id = lote_[0]['id']
				# Busco el id del medidor en medidores.
				domain_medidor = self.pool.get('datos.medidor').search(cr, uid, [('numero_medidor','=',int(order['numero_medidor']))])
				medidores_ = self.pool.get('datos.medidor').read(cr, uid, domain_medidor)
				medidor = medidores_[0]['id'] 				

				id_medidor = medidores_[0]['id']
				# Busco el lote y el medidor en registros historicos.
				domain_ = self.pool.get('registro.historico').search(cr, uid, [('lote_id', '=', lote_id),('numero_medidor','=',medidor)])	
				reg_ = self.pool.get('registro.historico').read(cr, uid, domain_)
				
				if reg_ != []:
					fl11= int(str(reg[0]['fecha_lectura']).split('-')[0])
					fl12= int(str(reg[0]['fecha_lectura']).split('-')[1])
					fl13= int(str(reg[0]['fecha_lectura']).split('-')[2])
					#-- --
					fl21= int(str(reg_[0]['fecha_lectura']).split('-')[0])
					fl22= int(str(reg_[0]['fecha_lectura']).split('-')[1])
					fl23= int(str(reg_[0]['fecha_lectura']).split('-')[2])

					resta_fechas = date(fl11,fl12,fl13)-date(fl21,fl22,fl23)
					dias_fact = int(str(resta_fechas).split(' ')[0])

					invoice_vals = {
					    'name': order['client_order_ref'] or '',
					    'origin': order['name'],
					    'type': 'out_invoice',
					    'reference': order['client_order_ref'] or order['name'],
					    'account_id': account_id, 
					    'partner_id': order['partner_invoice_id'][0],
					    'journal_id': journal_ids[0],
					    'currency_id': currency_id,
					    'comment': order['note'],
					    'payment_term': order['payment_term'] and order['payment_term'][0] or False,
					    'fiscal_position': fiscal_position,
					    'date_invoice': context.get('date_invoice', False),
					    'company_id': order['company_id'][0],
					    'user_id': order['user_id'][0] or False,
					    # Nuevos en factura 
					    'numero_abonado': order['numero_abonado'],
					    'numero_medidor': order['numero_medidor'],
					    'unidades_habitacionales': order['unidades_habitacionales'],
					    'periodo_id': periodo_id,
					    'registro_id': registro_id,
					    'fecha_vencimiento': order['fecha_vencimiento'],
					    'date_due': order['fecha_vencimiento'], 
					    'e_mail': e_mail,
					    'impreso': impreso,
					    # Aqui se agregan los nuevos campos que seran utiles para imprimir el reporte de factura.
					    'fecha_lect_ant': reg_[0]['fecha_lectura'],
					    'fecha_lect_act': reg[0]['fecha_lectura'],
					    'dias_fact': dias_fact,
					    'lectura_anterior': reg[0]['lectura_anterior'],
					    'lectura_actual': reg[0]['lectura'],
					    'consumo_mes': reg[0]['consumo'], 
					}
					factura_id = self.pool.get('account.invoice').create(cr, uid, invoice_vals)
				else:
					invoice_vals = {
					    'name': order['client_order_ref'] or '',
					    'origin': order['name'],
					    'type': 'out_invoice',
					    'reference': order['client_order_ref'] or order['name'],
					    'account_id': account_id, 
					    'partner_id': order['partner_invoice_id'][0],
					    'journal_id': journal_ids[0],
					    'currency_id': currency_id,
					    'comment': order['note'],
					    'payment_term': order['payment_term'] and order['payment_term'][0] or False,
					    'fiscal_position': fiscal_position,
					    'date_invoice': context.get('date_invoice', False),
					    'company_id': order['company_id'][0],
					    'user_id': order['user_id'][0] or False,
					    # Nuevos en factura 
					    'numero_abonado': order['numero_abonado'],
					    'numero_medidor': order['numero_medidor'],
					    'unidades_habitacionales': order['unidades_habitacionales'],
					    'periodo_id': periodo_id,
					    'registro_id': registro_id,
					    'fecha_vencimiento': order['fecha_vencimiento'],
					    'date_due': order['fecha_vencimiento'], 
					    'e_mail': e_mail,
					    'impreso': impreso,
					    # Aqui se agregan los nuevos campos que seran utiles para imprimir el reporte de factura.
					    #'fecha_lect_ant': reg_[0]['fecha_lectura'],
					    'fecha_lect_act': reg[0]['fecha_lectura'],
					    'dias_fact': 0,
					    'lectura_anterior': reg[0]['lectura_anterior'],
					    'lectura_actual': reg[0]['lectura'],
					    'consumo_mes': reg[0]['consumo'], 
					}
					factura_id = self.pool.get('account.invoice').create(cr, uid, invoice_vals)
	
				# Crear líneas de factura
				account_id = 0
				for o in order['order_line']:
					for order_line in sale_line_obj.read(cr,uid,[o],context=context):
						# Buscar cuenta contable
						for c in product_obj.read(cr,uid,[order_line['product_id'][0]],context=context):
							cuenta = str(c['property_account_income'][0]).replace("L",'')
							account_id = int(cuenta)
					
						invoice_line_vals = {
							'name': order_line['name'],
							'invoice_id': factura_id,
							'sequence': order_line['sequence'],
							'origin': order_line['order_id'][1],
							'account_id': account_id,
							'price_unit': order_line['price_unit'],
							'quantity': order_line['product_uom_qty'],
							'uos_id': order_line['product_uos_qty'],
							'product_id': order_line['product_id'][0] or False,
						    }
						self.pool.get('account.invoice.line').create(cr, uid, invoice_line_vals)
			
		# cambia el estado del pedido de venta.
		'''sale_obj.write(cr, uid, [id_linea], {'state': 'progress','invoice_exists': True}, context=context)'''	
		   
		# Elimina registro con estado manual.
		cr.execute('delete from valida_presupuestos_linea where id_sale_order='+str(id_linea)+'')

		sale_obj.write(cr, uid, [id_linea], {'state': 'progress','invoice_exists': True}, context=context)
		
	caant = lineas.search(cr, uid, [('state', '=', 'manual'),('orders_id','=',ids[0])])
	if len(caant)==0:
		self.write(cr,uid,ids,{'estado_validaciones': 'done'})	
		# Redireccionar a vista de facturas
		data_pool = self.pool.get('ir.model.data')
		action_model = False
		action = {}
		action_model,action_id = data_pool.get_object_reference(cr, uid, 'account', "action_invoice_tree")
		if action_model:
		    action_pool = self.pool.get(action_model)
		    action = action_pool.read(cr, uid, action_id, context=context)
		    return action
	return True

valida_presupuestos()

# Crea campos para almacenar allí los presupuestos, pedidos de ventas a los cuales se les aplicará las validaciones.
class valida_presupuestos_linea(osv.osv):

	_name= 'valida.presupuestos.linea'
	_columns = {
		'name': fields.char('Order Reference', size=64),
		'orders_id': fields.many2one('valida.presupuestos', 'Validaciones'),
		'date_order': fields.date('Date'),
		'partner_id': fields.many2one('res.partner', 'Customer'),
		'user_id': fields.many2one('res.users', 'Salesperson'),
		'amount_total': fields.float('Total'),
		'state': fields.char('Estado del pedido'),
		'id_sale_order': fields.many2one('sale.order','Presupuesto'),
		'confirm': fields.boolean('Validada'),
	}
	_order= 'confirm'

valida_presupuestos_linea()
