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
from datetime import datetime

# Esta clase permite crear un filtro; con la fecha seleccionada en el formulario, que genere los clientes con medidor moroso los cuales hay que procederles a realizar la corta.
class clientes_morosos(osv.osv):

	_name = 'clientes.morosos'
        _columns = {
		'name': fields.char('Filtro', size=64),
		'fecha': fields.date('Fecha'), 
 	}
	_defaults = {'fecha': fields.date.context_today,}

	# Los métodos siguientes son utilizados en los reportes.

	# Devuelve vector con la información de los medidores y clientes morosos.
	def generar_morosos(self, cr, uid, ids, context=None):
		res = []
		datos = {}
		for x in self.browse(cr,uid,ids,context=None):
			# Busqueda de cliente morosos en la tabla de registros históricos
			registro_obj = self.pool.get('registro.historico')
			id_registros = registro_obj.search(cr, uid, [('estado','=','al_cobro'),('fecha_vencimiento', '<=', x.fecha)])
			for r in registro_obj.read(cr,uid,id_registros,context=None):
				datos = {
					  'numero_abonado': r['numero_abonado'],
					  'nombre_cliente': r['nombre_cliente'][1],
					  'orden_lectura': r['orden_lectura'],
					  'numero_medidor': r['numero_medidor'][1],
					  'fecha_lectura': self.formato_fecha(r['fecha_lectura']),
					  'fecha_vencimiento': self.formato_fecha(r['fecha_vencimiento']),
					}
				res.append(datos)		
		if res == []:
			res.append({
				  'numero_abonado': 0,
				  'nombre_cliente': "N/A",
				  'orden_lectura': 0,
				  'numero_medidor': "0",
				  'fecha_lectura': "00/00/0000",
				  'fecha_vencimiento': "00/00/0000",
				})
		return res

	# Cambio de formato a fecha entrate.
	def formato_fecha(self, fecha):
		f = datetime.strptime(fecha, '%Y-%m-%d')
		formato= f.strftime('%d/%m/%Y')
		return formato
	# Devuelve la fecha del día de hoy.
	def fecha_hoy(self, cr, uid, ids, context=None):
		hoy = datetime.now()
		formato= hoy.strftime('%d/%m/%Y')
		return formato	
	
clientes_morosos()
