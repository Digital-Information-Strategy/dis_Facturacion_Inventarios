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

class configuraciones_facturacion_inventarios(osv.osv):

	# Nombre de la tabla en la base de datos.
	_name = 'configuraciones.facturacion.inventarios'
	# Describe los campos de la tabla y también serán utilizados en las vistas del OpenERP
        _columns = {
		'name': fields.char('Descripción', size=64),
		'monto': fields.integer('Monto'),
		'producto_id': fields.many2one('product.product','Producto'),
 	}
	
configuraciones_facturacion_inventarios()
