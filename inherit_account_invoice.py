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
from datetime import datetime

class account_invoice(osv.osv):

    _inherit ='account.invoice'
    _columns = {
	'numero_abonado': fields.integer('Número abonado'),
	'numero_medidor': fields.integer('Número medidor'),
	'unidades_habitacionales': fields.integer('Unidades habitacionales'),
	'periodo_id': fields.many2one('genera.facturas','Periodo'),
	'registro_id': fields.many2one('registro.historico','Registro'),
	'fecha_vencimiento': fields.date('Vencimiento de Factura'), # No se esta usando, ya que se usa el original del sistema.
	'e_mail': fields.boolean('Correo electrónico'),
	'impreso': fields.boolean('Impreso'),
	'fecha_lect_ant': fields.date('Fecha lectura anterior'),
	'fecha_lect_act': fields.date('Fecha lectura actual'),
	'dias_fact': fields.integer('Días Factura'),
	'lectura_anterior': fields.integer('Lectura anterior'),
	'lectura_actual': fields.integer('Lectura actual'),
	'consumo_mes': fields.integer('Consumo del mes'),
    }

    def confirm_paid(self, cr, uid, ids, context=None):
	registro_obj = self.pool.get('registro.historico')
	registro_id = []
	id_registro = 0
	numero_medidor = 0
	numero_medidor_x = ''
	fecha_vencimiento_max = ""
	fecha_vencimiento_registro = ""
	for x in self.browse(cr, uid, ids, context=context):
		id_registro = int(x.registro_id.id)
		#print "* periodo_id " + str(x.periodo_id.name)
		#print "* registro_id " + str(x.registro_id.id)
		cr.execute('update registro_historico set estado = '+"'pagado'"+', morosidad = '+"'False'"+' where id='+str(id_registro)+'')
	# Buscar en account.invoice las facturas que tengan el número de medidor igual y de ahí sacar la última factura realizada.
	for r in registro_obj.read(cr,uid,[id_registro],context=None):
		numero_medidor = r['numero_medidor'][0]
		numero_medidor_x = r['numero_medidor'][1]
		fecha_vencimiento_max = r['fecha_vencimiento']
	cr.execute('select max(fecha_vencimiento) from registro_historico where numero_medidor='+str(numero_medidor)+' and estado='+str("'al_cobro'")+'')
	for valor in cr.dictfetchall():
		#print "Valor: " + str(valor['max'])
		fecha_vencimiento_registro = str(valor['max'])
	
	# Esta condición permitirá validar si ya todas las facturas están pagadas para cambiar estado de medidor.
	if fecha_vencimiento_registro == "None":
		cr.execute('select max(fecha_vencimiento) from registro_historico where numero_medidor='+str(numero_medidor)+' and estado='+str("'pagado'")+'')
		for valor in cr.dictfetchall():
			#print "............ valor: " + str(valor)
			#print "............ fecha_vencimiento_max: " + str(fecha_vencimiento_max)
			if fecha_vencimiento_max == str(valor['max']):
				#print "\n... Aqui cambiar estado_moroso de medidor "
				cr.execute('update datos_medidor set estado_moroso = '+"'False'"+' where numero_medidor = '+ str(numero_medidor_x) +'')
	
        if context is None:
            context = {}
        self.write(cr, uid, ids, {'state':'paid'}, context=context)
        return True
  
# Métodos para el reporte de recibo de pago
    def linea_factura(self, cr, uid, ids, context=None):
	
	datos = {}
	res = []
	descripcion = ''
	cantidad = 0
	precio_unidad = 0
	total = 0
	for lf in self.browse(cr, uid,ids,context=None):
		linea = lf.invoice_line
		for ln in linea:
			descripcion = ln.name
			cantidad = ln.quantity
			precio_unidad = ln.price_unit
			total = ln.price_subtotal
			find = descripcion.find("Consumo")
			#print "find: " + str(find)
			if find >= 0:
				descripcion = descripcion + " de agua"
			datos = {'descripcion': descripcion, 'cantidad': int(cantidad), 'precio_unidad': int(precio_unidad), 'total':int(total)}
			res.append(datos)
	return res
    # Calcula el monto subtotal
    def monto_subtotal(self, cr, uid, ids, context=None):
	monto_subtotal = 0
	for l in self.browse(cr, uid,ids,context=None):
		linea_pago = l.invoice_line
		for ln in linea_pago:
			monto_subtotal += ln.price_subtotal
	return int(monto_subtotal)
    # Calcula el monto de impuestos
    def monto_impuestos(self, cr, uid, ids, context=None):
	impuestos = 0
	return int(impuestos)
    # Calcula el monto total 
    def monto_total(self, cr, uid, ids, context=None):
	monto_subtotal = 0
	impuestos = 0
	monto_total= 0
	for l in self.browse(cr, uid,ids,context=None):
		linea_pago = l.invoice_line
		for ln in linea_pago:
			monto_subtotal += ln.price_subtotal
			'''if ln.amount_tax != False:
				impuestos += ln.amount_tax'''
		monto_total = monto_subtotal + impuestos
	return int(monto_total)
    # Da formato a fecha recibida del formulario.
    def formato_fecha(self, cr, uid, ids, context=None):
	fecha  = ''
	for f in self.browse(cr, uid,ids,context=None):
		fecha = f.date_invoice
	f = datetime.strptime(fecha, '%Y-%m-%d')
	formato= f.strftime('%d/%m/%Y')
	return formato
    def tipo_suscriptor(self, cr, uid, ids, numero_medidor, context=None):
        model_data=self.pool.get('datos.medidor')
        conditions = model_data.search(cr, uid, [('numero_medidor', '=', numero_medidor)])
        i = model_data.read(cr, uid, conditions)
        result=i[0]['tipo_suscriptor']   
        return result

    def get_periodo(self, cr, uid, ids, context=None):

	'''Metodo para calcular el periodo en la impresion de los reportes, toma el period_id y le hace un split, luego le resta uno al
	mes y si el mes es enero tambien le resta un 1 al año
	'''
	try:
		res = {}
		data = self.browse(cr, uid, ids, context=context)[0]

		var =(str(data.period_id.name)).split('/')

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

		#print "\n\n"+str(ret)+"\n\n"
	except:
		ret="ERROR SISTEMA"
	return ret

account_invoice()
