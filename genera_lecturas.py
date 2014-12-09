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

import time
from osv import fields, osv
from datetime import datetime

class genera_lecturas(osv.osv):

	_name = 'genera.lecturas'
        _columns = {
		'name': fields.char('Nombre', size=64),
		'periodo_id': fields.many2one('account.period', 'Período'),
		'fecha_lectura': fields.date('Fecha lectura'),
		'fecha_vencimiento': fields.date('Fecha vencimiento'),
		'estado_lectura': fields.selection([('draft','Borrador'),('generado','Generado')], 'Estado de línea'),
 	}
	_defaults = {
		'estado_lectura': 'draft'
	} 
	_sql_constraints = [
        	('periodo_id_uniq', 'unique(periodo_id)', '¡El período debe ser único!')
    	]
	# Autocompletar las fechas al seleccionar el período.
        def onchange_periodo(self, cr, uid, ids, periodo_id, context=None):
		nombre = ""
		fecha_lectura = ""	
		fecha_vencimiento = ""	
		periodo_obj = self.pool.get('account.period')
		for p in periodo_obj.read(cr,uid,[periodo_id],context=context): 
			nombre = p['name']
			fecha_lectura = p['date_start']
			fecha_vencimiento = p['date_stop']
		return {'value':{'name': nombre, 'fecha_lectura': fecha_lectura, 'fecha_vencimiento': fecha_vencimiento}}
	
	# Genera líneas de registros históricos
	def generar_lecturas(self, cr, uid, ids, context=None):
		
		registro_obj = self.pool.get('registro.historico') # Apunta a la tabla registro_historico
		medidor_obj = self.pool.get('datos.medidor') # Apunta a la tabla datos_medidor
		res = {}
		mes_anterior = 0
		year_anterior = 0 
		num_abonado = 0
		meses = []
		lectura_anterior = 0.00

		# Obtener ids del objeto datos_medidor si su estado está activo y no está moroso.
		v_ids = medidor_obj.search(cr, uid, [('estado', '=', True),('estado_moroso','=',False)])

		#Este proceso esta relacionado también con la tabla de medidores: datos_medidor.
		for r in medidor_obj.read(cr,uid,v_ids,context=context):
			# Permite crear una linea de registro para cada medidor.
			for registro_lectura in self.browse(cr, uid, ids, context=context):
			
				# Obtener la lectura anterior desde la base de datos.	
				cr.execute('select max(id) from registro_historico where numero_medidor='+str(r['id'])+' and nombre_cliente='+str(r['cliente_id'][0])+'') 
				for valor in cr.dictfetchall():
					
					if str(valor['max']) == 'None':
						lectura_anterior = 0.00#lectura_anterior
					else:
						for lectura_medidor in registro_obj.browse(cr,uid,[int(valor['max'])],context=context): 
							lectura_anterior = lectura_medidor.lectura
				cr.execute('select numero_abonado from res_partner where id='+str(r['cliente_id'][0])+'') 	
				for valor in cr.dictfetchall():
					num_abonado = valor['numero_abonado']

				vals_registro = {
					'numero_abonado': num_abonado, #max_numero_medidor + 1,
					'nombre_cliente': r['cliente_id'][0],
					'numero_medidor': r['id'],
					'fecha_lectura': registro_lectura.fecha_lectura,
					'fecha_vencimiento': registro_lectura.fecha_vencimiento,
					'lectura_anterior': lectura_anterior,
					'lectura': 0.00,
					'consumo': 0.00,
					'morosidad': False,
					'lote_id': ids[0],
					'estado': 'al_cobro',
					'unidades_habitacionales': r['unidades_habitacionales'],
					'orden_lectura': r['orden_lectura'],
					'tipo_suscriptor': r['tipo_suscriptor'],
				}
				registro_obj.create(cr, uid, vals_registro, context=None) # Crear las línea de registros históricos.

		# Obtener ids del objeto datos_medidor si su estado está activo y está moroso. --> Ya se hizo la factura con línea de multa.
		m_ids = medidor_obj.search(cr, uid, [('estado', '=', True),('estado_moroso','=',True)])
		#Este proceso esta relacionado también con la tabla de medidores: datos_medidor.
		for m in medidor_obj.read(cr,uid,m_ids,context=context): 
			# Permite crear una linea de registro para cada medidor.
			for registro_lectura in self.browse(cr, uid, ids, context=context):
				# Obtener la lectura anterior desde la base de datos.	
				cr.execute('select max(id) from registro_historico where numero_medidor='+str(m['id'])+' and nombre_cliente='+str(m['cliente_id'][0])+'') 
				for valor in cr.dictfetchall():
					for lectura_medidor in registro_obj.browse(cr,uid,[int(valor['max'])],context=context): 
						lectura_anterior = lectura_medidor.lectura

				cr.execute('select numero_abonado from res_partner where id='+str(m['cliente_id'][0])+'') 	
				for valor in cr.dictfetchall():
					num_abonado = valor['numero_abonado']

				vals_registro = {
					'numero_abonado': num_abonado, #max_numero_medidor + 1,
					'nombre_cliente': m['cliente_id'][0],
					'numero_medidor': m['id'],
					'fecha_lectura': registro_lectura.fecha_lectura,
					'fecha_vencimiento': registro_lectura.fecha_vencimiento,
					'lectura_anterior': lectura_anterior,
					'lectura':lectura_anterior, # este indicará que no hubo consumo porque el medidor a estado cortado.
					'consumo': 0.00,
					'morosidad': False,
					'lote_id': ids[0],
					'estado': 'al_cobro',
					'unidades_habitacionales': m['unidades_habitacionales'],
					'orden_lectura': m['orden_lectura'],
					'tipo_suscriptor': m['tipo_suscriptor'],
				}
				registro_obj.create(cr, uid, vals_registro, context=None) # Crear las línea de registros históricos.
		
		# Modificar el estado.
		self.write(cr, uid, ids, {'estado_lectura': 'generado' }, context = None)
		# Redireccionar a otra vista
		data_pool = self.pool.get('ir.model.data')
		action_model = False
		action = {}
		action_model,action_id = data_pool.get_object_reference(cr, uid, 'dis_Facturacion_Inventarios', "action_registro_historico")
		#action_model,action_id = data_pool.get_object_reference(cr, uid, 'dis_Facturacion_Inventarios', "action_genera_lecturas")
		if action_model:
		    action_pool = self.pool.get(action_model)
		    action = action_pool.read(cr, uid, action_id, context=context)
		return action

genera_lecturas()
