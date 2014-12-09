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

class registro_historico(osv.osv):

	_name = 'registro.historico'
        _columns = {
		'lote_id': fields.many2one('genera.lecturas','Período', readonly="True"),
		'numero_abonado': fields.integer('Número abonado', readonly="True"), 
		'nombre_cliente': fields.many2one('res.partner','Nombre del Cliente', readonly="True"),
		'numero_medidor': fields.many2one('datos.medidor','Número medidor', readonly="True"),
		'fecha_lectura': fields.date('Fecha lectura', readonly="True"),
		'lectura_anterior': fields.integer('Lectura anterior', readonly="True"),
		'orden_lectura': fields.integer('Orden de lectura', readonly="True"),
		'tipo_suscriptor': fields.selection([('residencial','Residencial'),('comercios','Comercios')], 'Tipo Suscriptor'),
		'unidades_habitacionales': fields.integer('Unidades habitacionales'),
		'lectura': fields.integer('Lectura'),
		'consumo': fields.integer('Consumo', readonly="True"),
		'fecha_vencimiento':fields.date('Fecha vencimiento', readonly="True"),
		'estado': fields.selection([('pagado','Pagado'),('al_cobro','Al cobro')], 'Estado'),
		'morosidad': fields.boolean('Morosidad'),
 	}
	_rec_name = "numero_medidor"

	# Permite guardar los cambios al editar una línea; además de realizar el cálculo de la diferencia entre la lectura anterior y lectura, esto al ingresar la lectura.
	def write(self, cr, uid, ids, data, context=None):
		
		lectura_anterior = 0.00
		for vals in self.browse(cr,uid,ids,context=context):
			lectura_anterior = vals.lectura_anterior
		lectura = data['lectura']
		
		new_c = ''
		x = 0
		lect_ant = str(lectura_anterior)

		if lectura_anterior < lectura or lectura_anterior == lectura:
			consumo = lectura - lectura_anterior
			data.update({'consumo': consumo,})
		else:
			if int(lect_ant[0]) == 9:
				while x < len(lect_ant):	
					new_c += '9'
					x += 1
				suma = lectura_anterior+lectura
				consumo_a = int(new_c)-int(lect_ant)
				consumo_b = int(consumo_a) + int(lectura)
				if lectura < lectura_anterior:
					data.update({
						'consumo': consumo_b,
					})
				elif lectura > lectura_anterior and lectura < int(new_c):
					consumo = lectura - lectura_anterior
					data.update({
						'consumo': consumo,
					})
			else:
				raise osv.except_osv(('Atencion.'), ('La lectura debe ser mayor a la lectura anterior.'))

		x = super(registro_historico,self).write(cr, uid, ids, data, context=context)
		return x

	def onchange_lectura(self, cr, uid, ids, lectura_anterior, lectura, context=None):
		print "\n 0 \n"	
registro_historico()
