# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2013 D.I.S S.A. (http://www.dis.co.cr) All Rights Reserved.
#
#    $Id$
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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


# Información general del módulo.
{
    "name" : "Facturación Inventarios",
    "version" : "1.0",
    "author" : "D.I.S S.A.",
    "website": "www.dis.co.cr",
    "license" : "AGPL-3",
    "category" : "",
    "description": """ Realiza los procesos de:
1. Manejo de lecturas de medidores.
2. Registros de cobros.
3. Facturaciones.
4. Afectar el inventario.
 """,
    "depends" : ["base","account","sale","dis_inherit_clientes","trey_sale_auto_validate_picking","account_voucher"],
    "init_xml" : [ ],
    "update_xml" : [ "genera_lecturas_view.xml","configuraciones_view.xml","datos_medidor_view.xml","registro_historico_view.xml","genera_facturas_view.xml", "tarifas_acueducto_view.xml","inherit_sale_order_view.xml","inherit_account_invoice_view.xml","valida_presupuestos_view.xml","clientes_morosos_view.xml"],
    'images' : [ ],
    "active": False,
    "installable": True
}
