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

from osv import osv, fields 

class datos_medidor(osv.osv):

	_name = 'datos.medidor'
        _columns = {
		'numero_medidor': fields.integer('Número medidor'),
		'cliente_id': fields.many2one('res.partner', 'Cliente', domain=[('customer','=',True),('is_company','=',True)]),
		'estado': fields.boolean('Activo'),
		'descripcion': fields.text('Ubicación'),
		# Nuevos
		'unidades_habitacionales': fields.integer('Unidades habitacionales'),
		'tipo_suscriptor': fields.selection([('residencial','Residencial'),('comercios','Comercios')], 'Tipo Suscriptor'),
		'orden_lectura': fields.integer('Orden de lectura'),
		'estado_moroso': fields.boolean('Medidor moroso'),
		'activar_linea_cr': fields.boolean('Activar línea de corta y reconexión'),
		'activar_reconexion': fields.boolean('Activar reconexión'),
		'notas': fields.text('Notas Adicionales'),
 	}
	_rec_name = "numero_medidor"
	_defaults = {'unidades_habitacionales': 1,}

	# Este método es para validar que el campo numero_medidor sea único; es decir, no se repita...
	def onchange_numero_medidor(self, cr, uid, ids,numero_medidor, context=None):
		res = {}
		id_medidor = self.search(cr, uid, [('numero_medidor', '=', int(numero_medidor))])
		if id_medidor != [ ]:
			return {'value':{'numero_medidor': '' }, 'warning':{'title':'¡Atención!','message':'\tEl medidor ya existe.'}}
		return True
	
	# Este método es para validar que el campo orden_lectura sea único; es decir, no se repita...
	def onchange_orden_lectura(self, cr, uid, ids,orden_lectura, context=None):
		res = {}
		id_orden = self.search(cr, uid, [('orden_lectura', '=', int(orden_lectura))])
		if id_orden != [ ]:
			return {'value':{'orden_lectura': '' }, 'warning':{'title':'¡Atención!','message':'\tLa orden de lectura ya existe.'}}
		return True
datos_medidor()
