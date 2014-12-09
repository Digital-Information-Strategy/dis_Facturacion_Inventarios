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

# Clase crea campos para tabla donde se almacenarán las tarifas fijas junto con montos de consumo. 
class consumo_linea(osv.osv):
	_name = 'consumo.linea'
        _columns = {
		
		'line_id': fields.many2one('tarifas.acueducto', 'Tarifa acueducto'),
		'rango_abonados': fields.char('Rango de abonados'),
		'tarifa_base': fields.integer('Tarifa base'),
		'1_al_10': fields.integer('1 al 10'),
		'11_al_30': fields.integer('11 al 30'),
		'31_al_60': fields.integer('31 al 60'),
		'mas_60': fields.integer('Más de 60'),
		'tarifa_fija': fields.integer('Tarifa fija'),
 	}
consumo_linea()

# Clase crea campos para formulario de tarifas.
class tarifas_acueducto(osv.osv):

	_name = 'tarifas.acueducto'
        _columns = {
		'rango_actual_abonados': fields.integer('Rango actual de abonados'),
		'tipo_tarifa': fields.char('Tipo de tarifa'),
		'tipo_suscriptor': fields.selection([('residencial','Residencial'),('comercios','Comercios')], 'Tipo Suscriptor'),
		'consumo_metros_cubicos': fields.one2many('consumo.linea', 'line_id', 'Consumo en metros cúbicos'),	
		'producto_consumo': fields.many2one('product.product','Producto de consumo'),
		'tarifa_base': fields.many2one('product.product','Tarifa base'),
 	}
	
tarifas_acueducto()
