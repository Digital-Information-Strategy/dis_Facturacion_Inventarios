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
import sys 
reload(sys)
sys.setdefaultencoding('utf-8')

class genera_facturas(osv.osv):
	# Nota importante: El proceso lo que genera son presupuestos, no facturas. Es necesario cambiar luego los nombres a la clase y objetos... a genera.presupuestos, aunque no afecta en nada el proceso.
	_name = 'genera.facturas'
        _columns = {
		'name': fields.char('Nombre', size=64),
		'periodo_id': fields.many2one('genera.lecturas','Período'),
		'estado': fields.selection([('draft','Borrador'),('generado','Generado')], 'Estado'),
 	}
	_defaults = {
		'estado': 'draft',
	}
	_sql_constraints = [
        	('periodo_id_uniq', 'unique(periodo_id)', '¡El período debe ser único!')
    	]

	# Método que permite autocompletar el campo name al seleccionar un período y a la vez validar que el campo periodo_id sea único; es decir, no se repita....
	def onchange_periodo(self, cr, uid, ids,periodo_id, context=None):
		nombre = ""
		periodo_obj = self.pool.get('genera.lecturas')
		for p in periodo_obj.read(cr,uid,[periodo_id],context=context): 
			nombre = p['name']
		return {'value':{'name': nombre}}

	# Este método genera los pedidos de venta según el periodo seleccionado en el formulario.
	def generar_presupuestos(self, cr, uid, ids, context=None):
		registro_obj = self.pool.get('registro.historico')
		pedido_obj = self.pool.get('sale.order')
		pedido_line_obj = self.pool.get('sale.order.line')
		consumo_obj = self.pool.get('consumo.linea')
		tarifas_obj = self.pool.get('tarifas.acueducto')
		datos_obj = self.pool.get('datos.medidor')
		montos_obj = self.pool.get('configuraciones.facturacion.inventarios')
		linea_de_tarifa = [] 
		medidores_morosos = []
		id_medidores_morosos = []
		med_morosos_id = []
		vect_id_med_moroso = []
		id_datos_medidor = []
		periodo_id = 0
		abonados = 0 
		producto_consumo_id = 0
		tarifa_base_id = 0
		consumo = 0.00
		consumo_metros_total = 0.00
		tarifa_base_abonado = 0.00
		tarifa_fija_abonado = 0.00
		rango_1 = 0.00
		rango_2 = 0.00
		rango_3 = 0.00
		rango_4 = 0.00
		res = {}
		lineas_pedido = {}
		rango_abonados_linea = "" 
		
		# Obtener el periodo seleccionado.
		for p in self.browse(cr, uid, ids, context=context):
			periodo_id = p.periodo_id.id

		# Obtener los datos previos para poder calificar un cliente como moroso.
		# 1. Recorremos todos los registros históricos donde el lote_id sea diferente al periodo actual. Esto para validar que los períodos estén pagados, si alguno está al cobro el cliente debe pasar a estado de moroso y se generará una línea con valor para corta y reconexión.
		id_lineas_morosas = registro_obj.search(cr, uid, [('lote_id', '!=', periodo_id),('estado','=','al_cobro')])

		if id_lineas_morosas != []:
			for m in registro_obj.read(cr,uid,id_lineas_morosas,context=context):
				# Acá sacamos el número de medidor moroso para aplicar la multa al medidor entrante. (REVISAR LUEGO: SI ESTE PERIODO ESTA INACTIVO Y DEBE EL PERIODO PASADO.) 
				medidores_morosos.append(int(m['numero_medidor'][1]))
				#id_medidores_morosos.append(m['id'])
		else:
			print "..."

		# Buscar en la tabla registro.historico los id que tienen el mismo lote.
		id_linea = registro_obj.search(cr, uid, [('lote_id', '=', periodo_id),('estado','=','al_cobro')])
		
 		# Marcar el check de morosidad en las líneas de registros históricos que aún no han sido pagadas.
		# Recorrer las líneas de cada registro histórico que pertenezcan al lote seleccionado. 		
		for l in registro_obj.read(cr,uid,id_linea,context=context): 
			# Obtener ids del objeto datos_medidor si su estado está activo y el campo activar_linea_cr también... 
			l_ids = datos_obj.search(cr, uid, [('estado', '=', True),('activar_linea_cr','=',True)])
			medidor_moroso = 0
			for m in medidores_morosos:
				if m == int(l['numero_medidor'][1]):
					medidor_moroso = m

			# Si el medidor está al día y no hay estados registros históricos "al_cobro"
			# Este caso es para cuando el medidor de linea del mes no esta en el vector de medidores morosos.
			if medidor_moroso == 0:
				consumo_total = 0.00
				# Crear el encabezado del pedido de venta en borrador (presupuesto).
				datos_pedido = {
					'partner_id': l['nombre_cliente'][0],
					'numero_abonado': l['numero_abonado'],
					'numero_medidor': int(l['numero_medidor'][1]),
					'unidades_habitacionales': l['unidades_habitacionales'] ,
					'periodo_id': int(ids[0]),
					'registro_id': int(l['id']),
					'fecha_vencimiento': l['fecha_vencimiento'],
					# Campos requeridos por el sistema.
					'pricelist_id': 1,
					'partner_invoice_id': l['nombre_cliente'][0],
					'partner_shipping_id': l['nombre_cliente'][0],
					}
				pedido_id = pedido_obj.create(cr, uid, datos_pedido , context=None)

				# Agregar líneas de pedido al presupuesto. 
				if float(l['consumo']) < 0:
					consumo = float(str((l['consumo'])).replace('-',''))
				else:
					consumo = float(l['consumo'])

				# Obtener el número de abonados en la tarifa de acueducto según el tipo de suscriptor.
				id_tarifa = tarifas_obj.search(cr, uid, [('tipo_suscriptor', '=', l['tipo_suscriptor'])]) # Búsqueda del id de la tarifa correspondiente al tipo de suscriptor de la línea del registro histórico.

				for tarifa in tarifas_obj.read(cr,uid,id_tarifa,context=context): 
					producto_consumo_id = tarifa['producto_consumo'][0]
					tarifa_base_id = tarifa['tarifa_base'][0]
					abonados = int(tarifa['rango_actual_abonados'])
					id_tarifas = tarifa['consumo_metros_cubicos']
					cant_id_tarifas = len(id_tarifas)
					# ALAMBRADO.	
					if abonados > 1 and abonados < 51:
						linea_de_tarifa = [id_tarifas[0]]
					if abonados > 50 and abonados < 101:
						linea_de_tarifa = [id_tarifas[1]]
					if abonados > 100 and abonados < 151:
						linea_de_tarifa = [id_tarifas[2]]
					if abonados > 150 and abonados < 301:
						linea_de_tarifa = [id_tarifas[3]]
					if abonados > 300 and abonados < 501:
						linea_de_tarifa = [id_tarifas[4]]
					if abonados > 500 and abonados < 1001:
						linea_de_tarifa = [id_tarifas[5]]
					if abonados > 1000:
						linea_de_tarifa = [id_tarifas[6]]

					for linea_tarifa in consumo_obj.read(cr,uid,linea_de_tarifa,context=context): # Debe entrar solo la linea que se va a utilizar...
						rango_abonados_linea = linea_tarifa['rango_abonados']
						tarifa_base_abonado = linea_tarifa['tarifa_base']
						tarifa_fija_abonado = linea_tarifa['tarifa_fija']
						rango_1 = linea_tarifa['1_al_10']
						rango_2 = linea_tarifa['11_al_30']
						rango_3 = linea_tarifa['31_al_60']
						rango_4 = linea_tarifa['mas_60']

				# Crear las líneas de producto según el consumo.
				# Distribución del consumo según la tabla...
				if consumo > 0:
					if consumo > 10:
						#print "CONSUMO MENOR A 10"
						consumo = consumo - 10
		
						linea_pedido = {
							'order_id': pedido_id,
							'product_id': producto_consumo_id,
							'name': 'Consumo 1-10',
							'product_uom_qty': 10,
							'price_unit': rango_1,			
							}
						pedido_line_obj.create(cr, uid, linea_pedido , context=None)
						consumo_total += rango_1 * 10
						if consumo > 30:
							#print "CONSUMO MENOR A 30"
							consumo = consumo - 20
							linea_pedido = {
								'order_id': pedido_id,
								'product_id': producto_consumo_id,
								'name': 'Consumo 11-30',
								'product_uom_qty': 20,
								'price_unit': rango_2,		
								}
							pedido_line_obj.create(cr, uid, linea_pedido , context=None)
							consumo_total += rango_2 * 20
							if consumo >= 60:
								#print "CONSUMO MENOR A 60"
								consumo = consumo - 30
								linea_pedido = {
									'order_id': pedido_id,
									'product_id': producto_consumo_id,
									'name': 'Consumo 31-60',
									'product_uom_qty': 30,
									'price_unit': rango_3,		
									}
								pedido_line_obj.create(cr, uid, linea_pedido , context=None)
								consumo_total += rango_3 * 30
								if consumo > 0:
									#print "CONSUMO ..."
									linea_pedido = {
										'order_id': pedido_id,
										'product_id': producto_consumo_id,
										'name': 'Consumo más de 60',
										'product_uom_qty': consumo,
										'price_unit': rango_4,			
										}
									pedido_line_obj.create(cr, uid, linea_pedido , context=None) # FIN DE VALIDACIONES.
									consumo_total += rango_4 * consumo
							else:
								linea_pedido = {
									'order_id': pedido_id,
									'product_id': producto_consumo_id,
									'name': 'Consumo 31-60',
									'product_uom_qty': consumo,
									'price_unit': rango_3,		
									}
								pedido_line_obj.create(cr, uid, linea_pedido , context=None)	
								consumo_total += rango_3 * consumo
						else:
							linea_pedido = {
								'order_id': pedido_id,
								'product_id': producto_consumo_id,
								'name': 'Consumo 11-30',
								'product_uom_qty': consumo,
								'price_unit': rango_2,			
								}
							pedido_line_obj.create(cr, uid, linea_pedido , context=None)
							consumo_total += rango_2 * consumo
					else:
						linea_pedido = {
							'order_id': pedido_id,
							'product_id': producto_consumo_id,
							'name': 'Consumo 1-10',
							'product_uom_qty': consumo,
							'price_unit': rango_1,			
							}
						pedido_line_obj.create(cr, uid, linea_pedido , context=None)
						consumo_total += rango_1 * consumo
				else:
					print "No hay consumo"

				# Monto para tarifa base.
				linea_pedido = {
					'order_id': pedido_id,
					'product_id': tarifa_base_id,
					'name': 'Tarifa base',
					'product_uom_qty': l['unidades_habitacionales'],
					'price_unit': tarifa_base_abonado,			
					}
				pedido_line_obj.create(cr, uid, linea_pedido , context=None)

				# Obtener ids del objeto configuraciones_facturacion_inventarios.
				m_ids = montos_obj.search(cr, uid, [])
				precio = 0.00
				
				# Generar línea de corta y reconexión a la factura pagada después del vencimiento y que no se haya generado facturas.. 
				if l_ids != []:
					for new_line in l_ids:
						if new_line == l['numero_medidor'][0]:
							#Este proceso esta relacionado también con la tabla de medidores: configuraciones_facturacion_inventarios.
							for m in montos_obj.read(cr,uid,m_ids,context=context):
								#CAMBIO SUBIR A LA ASADA 
								if l['consumo'] > 0:
									if str(m['producto_id'][1]).lower() == "hidrante":
										pc = m['monto']
										# Precio del hidrante será igual al monto por el consumo en m3.
										lineas_pedido = {
											'order_id': pedido_id,
											'product_id': m['producto_id'][0],
											'name': "Valor de " + str(m['producto_id'][1]),
											'product_uom_qty': l['consumo'],
											'price_unit': pc,	
										}
										pedido_line_obj.create(cr, uid, lineas_pedido , context=None)
								if str(m['producto_id'][1]).lower() == "reconexión" or str(m['producto_id'][1]).lower() == "reconexion":
									pc = m['monto']
									lineas_pedido = {
										'order_id': pedido_id,
										'product_id': m['producto_id'][0],
										'name': "Valor de " + str(m['producto_id'][1]),
										'product_uom_qty': 1,
										'price_unit': pc,	
									}
									pedido_line_obj.create(cr, uid, lineas_pedido , context=None)
								if str(m['producto_id'][1]).lower() == "corte" or str(m['producto_id'][1]).lower() == "corta":
									pc = m['monto']
									lineas_pedido = {
										'order_id': pedido_id,
										'product_id': m['producto_id'][0],
										'name': "Valor de " + str(m['producto_id'][1]),
										'product_uom_qty': 1,
										'price_unit': pc,	
									}
									pedido_line_obj.create(cr, uid, lineas_pedido , context=None)
								# Desactivar el check activar_linea_cr en el medidor.
								cr.execute('update datos_medidor set activar_linea_cr = False where numero_medidor='+str(l['numero_medidor'][1])+'')
					if l['numero_medidor'][0] not in l_ids:	
						#Este proceso esta relacionado también con la tabla de medidores: configuraciones_facturacion_inventarios.
						for m in montos_obj.read(cr,uid,m_ids,context=context):
							#CAMBIO SUBIR A LA ASADA 
							if l['consumo'] > 0:
								if str(m['producto_id'][1]).lower() == "hidrante":
									pc = m['monto']
									# Precio del hidrante será igual al monto por el consumo en m3.
									lineas_pedido = {
										'order_id': pedido_id,
										'product_id': m['producto_id'][0],
										'name': "Valor de " + str(m['producto_id'][1]),
										'product_uom_qty': l['consumo'],
										'price_unit': pc,	
									}
									pedido_line_obj.create(cr, uid, lineas_pedido , context=None)
				else:
					#Esta condición se ejecuta cuando no hay medidores con activar_linea_cr activos
					#Este proceso esta relacionado también con la tabla de medidores: configuraciones_facturacion_inventarios.
					for m in montos_obj.read(cr,uid,m_ids,context=context):
						if l['consumo'] != 0: 
							if str(m['producto_id'][1]).lower() == "hidrante":
								pc = m['monto']
								lineas_pedido = {
									'order_id': pedido_id,
									'product_id': m['producto_id'][0],
									'name': "Valor de " + str(m['producto_id'][1]),
									'product_uom_qty': l['consumo'],
									'price_unit': pc,	
								}
								pedido_line_obj.create(cr, uid, lineas_pedido , context=None)
							else:
								print ""

			# Este caso es para cuando el medidor de linea del mes esta en el vector de medidores morosos.
			else:
				
				consumo_total = 0.00
				# Crear el encabezado del pedido de venta en borrador (presupuesto).
				datos_pedido = {
					'partner_id': l['nombre_cliente'][0],
					'numero_abonado': l['numero_abonado'],
					'numero_medidor': int(l['numero_medidor'][1]),
					'unidades_habitacionales': l['unidades_habitacionales'] ,
					'periodo_id': int(ids[0]),
					'registro_id': int(l['id']),
					'fecha_vencimiento': l['fecha_vencimiento'],
					# Campos requeridos por el sistema.
					'pricelist_id': 1,
					'partner_invoice_id': l['nombre_cliente'][0],
					'partner_shipping_id': l['nombre_cliente'][0],
					}
				pedido_id = pedido_obj.create(cr, uid, datos_pedido , context=None)
				# Agregar líneas de pedido al presupuesto. 
				if float(l['consumo']) < 0:
					consumo = float(str((l['consumo'])).replace('-',''))
				else:
					consumo = float(l['consumo'])
				# Obtener el número de abonados en la tarifa de acueducto según el tipo de suscriptor.
				id_tarifa = tarifas_obj.search(cr, uid, [('tipo_suscriptor', '=', l['tipo_suscriptor'])]) # Búsqueda del id de la tarifa correspondiente al tipo de suscriptor de la línea del registro histórico.

				for tarifa in tarifas_obj.read(cr,uid,id_tarifa,context=context): 
					producto_consumo_id = tarifa['producto_consumo'][0]
					tarifa_base_id = tarifa['tarifa_base'][0]
					abonados = int(tarifa['rango_actual_abonados'])
					id_tarifas = tarifa['consumo_metros_cubicos']
					cant_id_tarifas = len(id_tarifas)
					# ALAMBRADO.	
					if abonados > 1 and abonados < 51:
						linea_de_tarifa = [id_tarifas[0]]
					if abonados > 50 and abonados < 101:
						linea_de_tarifa = [id_tarifas[1]]
					if abonados > 100 and abonados < 151:
						linea_de_tarifa = [id_tarifas[2]]
					if abonados > 150 and abonados < 301:
						linea_de_tarifa = [id_tarifas[3]]
					if abonados > 300 and abonados < 501:
						linea_de_tarifa = [id_tarifas[4]]
					if abonados > 500 and abonados < 1001:
						linea_de_tarifa = [id_tarifas[5]]
					if abonados > 1000:
						linea_de_tarifa = [id_tarifas[6]]
					for linea_tarifa in consumo_obj.read(cr,uid,linea_de_tarifa,context=context): # Debe entrar solo la linea que se va a utilizar...
						rango_abonados_linea = linea_tarifa['rango_abonados']
						tarifa_base_abonado = linea_tarifa['tarifa_base']
						tarifa_fija_abonado = linea_tarifa['tarifa_fija']
						rango_1 = linea_tarifa['1_al_10']
						rango_2 = linea_tarifa['11_al_30']
						rango_3 = linea_tarifa['31_al_60']
						rango_4 = linea_tarifa['mas_60']

				# Crear las líneas de producto según el consumo.
				# Distribución del consumo según la tabla...
				if consumo > 0:
					if consumo > 10:
						consumo = consumo - 10
						linea_pedido = {
							'order_id': pedido_id,
							'product_id': producto_consumo_id,
							'name': 'Consumo 1-10',
							'product_uom_qty': 10,
							'price_unit': rango_1,			
							}
						pedido_line_obj.create(cr, uid, linea_pedido , context=None)
						consumo_total += rango_1 * 10
						if consumo > 30:
							consumo = consumo - 20
							linea_pedido = {
								'order_id': pedido_id,
								'product_id': producto_consumo_id,
								'name': 'Consumo 11-30',
								'product_uom_qty': 20,
								'price_unit': rango_2,			
								}
							pedido_line_obj.create(cr, uid, linea_pedido , context=None)
							consumo_total += rango_2 * 20
							if consumo >= 60:
								consumo = consumo - 30
								linea_pedido = {
									'order_id': pedido_id,
									'product_id': producto_consumo_id,
									'name': 'Consumo 31-60',
									'product_uom_qty': 30,
									'price_unit': rango_3,			
									}
								pedido_line_obj.create(cr, uid, linea_pedido , context=None)
								consumo_total += rango_3 * 30
								if consumo > 0:
					
									linea_pedido = {
										'order_id': pedido_id,
										'product_id': producto_consumo_id,
										'name': 'Consumo más de 60',
										'product_uom_qty': consumo,
										'price_unit': rango_4,			
										}
									pedido_line_obj.create(cr, uid, linea_pedido , context=None) # FIN DE VALIDACIONES.
									consumo_total += rango_4 * consumo
							else:
								linea_pedido = {
									'order_id': pedido_id,
									'product_id': producto_consumo_id,
									'name': 'Consumo 31-60',
									'product_uom_qty': consumo,
									'price_unit': rango_3,			
									}
								pedido_line_obj.create(cr, uid, linea_pedido , context=None)	
								consumo_total += rango_3 * consumo
						else:
							linea_pedido = {
								'order_id': pedido_id,
								'product_id': producto_consumo_id,
								'name': 'Consumo 11-30',
								'product_uom_qty': consumo,
								'price_unit': rango_2,			
								}
							pedido_line_obj.create(cr, uid, linea_pedido , context=None)
							consumo_total += rango_2 * consumo
					else:
						linea_pedido = {
							'order_id': pedido_id,
							'product_id': producto_consumo_id,
							'name': 'Consumo 1-10',
							'product_uom_qty': consumo,
							'price_unit': rango_1,			
							}
						pedido_line_obj.create(cr, uid, linea_pedido , context=None)
						consumo_total += rango_1 * consumo
				else:
					print "No hay consumo"

				# Monto para tarifa base.
				linea_pedido = {
					'order_id': pedido_id,
					'product_id': tarifa_base_id,
					'name': 'Tarifa base',
					'product_uom_qty': l['unidades_habitacionales'],
					'price_unit': tarifa_base_abonado,			
					}
				pedido_line_obj.create(cr, uid, linea_pedido , context=None)
				# Obtener ids del objeto configuraciones_facturacion_inventarios.
				m_ids = montos_obj.search(cr, uid, [])
				precio = 0.00
				#Este proceso esta relacionado también con la tabla de medidores: configuraciones_facturacion_inventarios.
				for m in montos_obj.read(cr,uid,m_ids,context=context): 
					datos_medidor = datos_obj.search(cr, uid, [('numero_medidor', '=', medidor_moroso)])
					for dm in datos_obj.read(cr,uid,datos_medidor,context=context):
						if dm['estado_moroso'] == False:
							
							#CAMBIO SUBIR A LA ASADA 
							if l['consumo'] > 0:	
								if str(m['producto_id'][1]).lower() == "hidrante":
									pc = m['monto']
									lineas_pedido = {
										'order_id': pedido_id,
										'product_id': m['producto_id'][0],
										'name': "Valor de " + str(m['producto_id'][1]),
										'product_uom_qty': l['consumo'],
										'price_unit': pc,	
									}
									pedido_line_obj.create(cr, uid, lineas_pedido , context=None)
							# Esta condición es para el corte.
							if str(m['producto_id'][1]).lower() == "corte" or str(m['producto_id'][1]).lower() == "corta":
								pc = m['monto']
								lineas_pedido = {
									'order_id': pedido_id,
									'product_id': m['producto_id'][0],
									'name': "Valor de " + str(m['producto_id'][1]),
									'product_uom_qty': 1,
									'price_unit': pc,	
								}
								pedido_line_obj.create(cr, uid, lineas_pedido , context=None)
								
								

				#Si el medidor está abierto y hay estados de registros históricos "al_cobro".
				id_datos_medidor = datos_obj.search(cr, uid, [('numero_medidor', '=', medidor_moroso),('estado','=','al_cobro')])
				if id_datos_medidor != []:
					vect_id_med_moroso.append(id_datos_medidor)
					 
					id_med_moroso = registro_obj.search(cr, uid, [('numero_medidor', '=', id_datos_medidor[0]),('estado','=','al_cobro')])
					med_morosos_id.append(id_med_moroso)

					# Cambiar el medidor a estado inactivo
					#datos_obj.write(cr,uid,[id_datos_medidor[0]],{'estado': False},context=None) # Se quitó para que el medidor moroso pueda generar tarifa base.
				
			#  Verificar si el medidor tiene activo el check Activar reconexión.
			for medidor in datos_obj.read(cr,uid,[l['numero_medidor'][0]],context=None):
				reconexion=medidor['activar_reconexion']
				if reconexion == True:
					# Desactivar el check de activar_reconexion
					datos_obj.write(cr, uid, [medidor['id']], {'activar_reconexion': False})
					for m in montos_obj.read(cr,uid,m_ids,context=context):
						if str(m['producto_id'][1]).lower() == "reconexión" or str(m['producto_id'][1]).lower() == "reconexion":
							pc = m['monto']
							lineas_pedido = {
								'order_id': pedido_id,
								'product_id': m['producto_id'][0],
								'name': "Valor de " + str(m['producto_id'][1]),
								'product_uom_qty': 1,
								'price_unit': pc,	
							}
							pedido_line_obj.create(cr, uid, lineas_pedido , context=None)	

		# Desactiva el medidor a estado de morosidad para que no pueda generar consumo.
		for x in vect_id_med_moroso:
			cr.execute('update datos_medidor set estado_moroso = True where id='+str(x[0])+'')

		# Activa el check de morosidad para las líneas de registros al_cobro.		
		for a in med_morosos_id:
			for b in a:
				cr.execute('update registro_historico set morosidad = True where id='+str(b)+'')

		# Modificar el estado.
		self.write(cr, uid, ids, {'estado': 'generado' }, context = None)		
		# Redireccionar a otra vista
		data_pool = self.pool.get('ir.model.data')
		action_model = False
		action = {}
		#action_model,action_id = data_pool.get_object_reference(cr, uid, 'sale', "action_quotations")
		action_model,action_id = data_pool.get_object_reference(cr, uid, 'dis_Facturacion_Inventarios', "action_valida_presupuestos")	
		if action_model:
		    action_pool = self.pool.get(action_model)
		    action = action_pool.read(cr, uid, action_id, context=context)
		return action

genera_facturas()
