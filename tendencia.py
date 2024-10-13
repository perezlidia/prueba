#encoding=utf-8
import os, shutil
from datetime import datetime 
import sys
#libreria para archivos de excel .xls
import xlrd 
import xlwt
import pathlib

import glob
import time

from selenium.common.exceptions import TimeoutException


#usar idrisi
#import win32com.client
# usar arcGis
#import arcpy

#nomenclatura_proceso
"""
	********PREPARACION DE LAS VARIABLES******

	ds -- descarga

	ms -- mosaico
	gc -- grados centigrados

	ct -- corte

	proy -- proyeccion
	proym -- proyeccion mascara

	prm -- promedio mensual

	pra -- promedio anual

	cr 2 var H,EVA,P -- correccion
	fe -- factor escala	
	fed  var Temperratura-- promedio anual proyeccion tipodato	
	fedc var IDV--  promedio anual proyeccion tipodato corte	
	var_xxxxxx_2019 -- promedio anual proyeccion mascara

	******FACTORES*****

	varn_xxxxxx_2019 -- nan fix
	
	fu -- fuzzy

	fac_xxxx_2019 -- overlay

	******EVALUACIONES MULTICRITERIOS******

	mce -- MCE

	rec -- RECLASS
"""

#PREPARACION DE LAS VARIABLES
pixelesEnteros = "7985515"
urlPython27 = "C:/Python27/ArcGIS10.3/python"
urlPythonQgis = "D:/Program Files/QGIS 3.18/bin/python-qgis.bat"
directorio = 'D:\\zonas_aridas\\zonas-aridas'	
directorioAREATif = directorio + "/tendencia/utilerias/AREA_/AREA_.tif"
directorioAREA = directorio + "/tendencia/utilerias/AREA/AREA.shp" 
variables = ['precipitacion', 'evapotranspiracion', 'humedad', 'temperatura', 'indiceDeVegetacion']
valores_tendencia = ['-0.34', '1.87', '-0.74', '0.023', '-0.006_-0.001']


#FACTORES
factores = ['precipitacion', 'temperatura', 'indiceDeVegetacion', 'evapotranspiracion', 'humedad', 'pendientes', 'orientaciones']
directorioAREARst = directorio + "/tendencia/utilerias/AREA/AREA.rst" 
directorioAREARdc = directorio + "/tendencia/utilerias/AREA/AREA.RDC" 
factores_pesos = ['0.28', '0.22', '0.19', '0.13', '0.09', '0.06', '0.03']

##EVALUACIONES MULTICRITERIO
directorioAREABinaryRST = directorio + "/tendencia/utilerias/AREA_B/AREA_B.rst" 
directorioAREABinaryRdc = directorio + "/tendencia/utilerias/AREA_B/AREA_B.RDC" 

#ALMACENAMIENTO POSTGRES
db_name = 'zonas_aridas'
db_host = 'localhost'
db_user = 'postgres'
db_password = 'postgres'
directorioPosgrest = "C:/Program Files/PostgreSQL/10/bin/"

#SUBIR GEOSERVER
directorioConnectGeoServer = directorio + "/tendencia/utilerias/GEOSERVER/connect.pgraster.xml.inc" 
directorioMappingGeoServer = directorio + "/tendencia/utilerias/GEOSERVER/mapping.pgraster.xml.inc" 


#FACTORES
def proceso_multiplicacion_1(variable,prValorTendencia, year,datoConfig):

    if not os.path.exists(directorio + '/tendencia'):
        os.mkdir(directorio + '/tendencia')

    if not os.path.exists(directorio + '/tendencia/data'):
        os.mkdir(directorio + '/tendencia/data')

    if not os.path.exists(directorio + '/tendencia/data/factores'):
        os.mkdir(directorio + '/tendencia/data/factores') 

    if not os.path.exists(directorio + '/tendencia/data/factores/'+variable):
        os.mkdir(directorio + '/tendencia/data/factores/'+variable) 

    if not os.path.exists(directorio + '/tendencia/data/factores/'+variable+'/'+year):
        os.mkdir(directorio + '/tendencia/data/factores/'+variable+'/'+year)    

    print("Proceso de multiplicacion (" + variable + ") ...")			
    if os.system('"' + urlPythonQgis + '" '+ directorio+'/tendencia/procesos/factores/realizar_multiplicacion.py ' + variable + " " + year + " " + directorio + " " + directorioAREARst + " " + directorioAREARdc + " " + prValorTendencia) != 0:
        raise Exception('Error al momento de realizar el proceso de multiplicacion.')


def proceso_factores_1(factor, year,datoConfig):
	if not os.path.exists(directorio + '/tendencia/data/factores'):
		os.mkdir(directorio + '/tendencia/data/factores')
		
	if  not os.path.exists(directorio + "/tendencia/data/factores/pendientes"):
		os.mkdir(directorio + "/tendencia/data/factores/pendientes")
		shutil.copy(directorio + "/tendencia/utilerias/pendientes/fac_pendientes.rst", directorio + "/tendencia/data/factores/pendientes")
		shutil.copy(directorio + "/tendencia/utilerias/pendientes/fac_pendientes.RDC", directorio + "/tendencia/data/factores/pendientes")

	if  not os.path.exists(directorio + "/tendencia/data/factores/orientaciones"):
		os.mkdir(directorio + "/tendencia/data/factores/orientaciones")
		shutil.copy(directorio + "/tendencia/utilerias/orientaciones/fac_orientaciones.rst", directorio + "/tendencia/data/factores/orientaciones")
		shutil.copy(directorio + "/tendencia/utilerias/orientaciones/fac_orientaciones.RDC", directorio + "/tendencia/data/factores/orientaciones")

	print("Proceso de overlay (" + factor + ") ...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/tendencia/procesos/factores/realizar_overlay.py ' + factor + " " + year + " " + directorio + " " + directorioAREARst + " " + directorioAREARdc) != 0:
		raise Exception('Error al momento de realizar el proceso de overlay.')

	print("Proceso de CONVERSION VECTOR ..." + factor)			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/tendencia/procesos/factores/realizar_conversion_vector_variables.py ' + year + " " + directorio + " " + factor ) != 0:
		raise Exception('Error al momento de realizar el proceso de conversion a vector ' + factor)

	print("Proceso de CONVERSION SHAPE " + factor)			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/tendencia/procesos/factores/realizar_conversion_shape_variables.py ' + year + " " + directorio + " " + factor  ) != 0:
		raise Exception('Error al momento de realizar el proceso de conversion a shape ' + factor)
		

	print("Proceso de fuzzy (" + factor + ") ...")
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/tendencia/procesos/factores/realizar_fuzzy.py ' + factor + " " + year + " " + directorio + " " + directorioAREARst + " " + directorioAREARdc) != 0:
		raise Exception('Error al momento de realizar el proceso de fuzzy.')

	print("Proceso de overlay2 (" + factor + ") ...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/tendencia/procesos/factores/realizar_overlay_2.py ' + factor + " " + year + " " + directorio + " " + directorioAREARst + " " + directorioAREARdc) != 0:
		raise Exception('Error al momento de realizar el proceso de overlay2.')

#EVALUACIONES MULTICRITERIO
def proceso_evaluacionesMulticriterio_1(factores, imagenesFactores, factores_pesos, year, datoConfig):	
	factoresString = ','.join(imagenesFactores)
	pesosString = ','.join(factores_pesos)

	if not os.path.exists(directorio + '/tendencia/data/evaluacion_multicriterio'):
		os.mkdir(directorio + '/tendencia/data/evaluacion_multicriterio')

	print("Proceso de MCE ...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/tendencia/procesos/evaluacion_multicriterio/realizar_mce.py ' + factoresString + " " + pesosString + " " + year + " " + directorio + " " + directorioAREABinaryRST) != 0:
		raise Exception('Error al momento de realizar el proceso de MCE.')
	

	print("Proceso de RECLASS ...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/tendencia/procesos/evaluacion_multicriterio/realizar_reclass.py ' + year + " " + directorio ) != 0:
		raise Exception('Error al momento de realizar el proceso de RECLASS.')
	



	#GENERAR MAPA ARIDEZ POR ESTADOS
	print("Proceso de CrossTab estados ...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/tendencia/procesos/evaluacion_multicriterio/realizar_crosstab_estados.py ' + year + " " + directorio ) != 0:
		raise Exception('Error al momento de realizar el proceso de Crosstab estados.')	

	#leer los valores del html generado y generar un html con los nuevos datos
	print("Proceso de generar tabla crosstab estados ...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/tendencia/procesos/evaluacion_multicriterio/generar_tabla_crosstab_estados.py ' + year + " " + directorio ) != 0:
		raise Exception('Error al momento de realizar el proceso de generar tabla crosstab estados.')


	#GENERAR INDICADOR ARIDES
	print("Proceso de CrossTab INDICADOR ARIDES...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/tendencia/procesos/evaluacion_multicriterio/realizar_crosstab_indicador_aridez.py ' + year + " " + directorio ) != 0:
		raise Exception('Error al momento de realizar el proceso de Crosstab indicador aridez.')

	#leer los valores del html generado y generar un html con los nuevos datos
	print("Proceso de generar tabla crosstab INDICADOR ARIDES...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/tendencia/procesos/evaluacion_multicriterio/generar_tabla_crosstab_indicador_aridez.py ' + year + " " + directorio ) != 0:
		raise Exception('Error al momento de realizar el proceso de generar tabla crosstab indicador aridez.')
	

	#GENERAR MAPA ARIDEZ POR CUENCAS
	print("Proceso de CrossTab cuencas ...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/tendencia/procesos/evaluacion_multicriterio/realizar_crosstab_cuencas.py ' + year + " " + directorio ) != 0:
		raise Exception('Error al momento de realizar el proceso de Crosstab cuencas.')	

	#leer los valores del html generado y generar un html con los nuevos datos
	print("Proceso de generar tabla crosstab cuencas ...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/tendencia/procesos/evaluacion_multicriterio/generar_tabla_crosstab_cuencas.py ' + year + " " + directorio ) != 0:
		raise Exception('Error al momento de realizar el proceso de generar tabla crosstab cuencas.')


	#GENERAR MAPA ARIDEZ POR MUNICIPIOS
	print("Proceso de CrossTab municipios ...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/tendencia/procesos/evaluacion_multicriterio/realizar_crosstab_municipios.py ' + year + " " + directorio ) != 0:
		raise Exception('Error al momento de realizar el proceso de Crosstab municipios.')	

	#leer los valores del html generado y generar un html con los nuevos datos
	print("Proceso de generar tabla crosstab municipios ...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/tendencia/procesos/evaluacion_multicriterio/generar_tabla_crosstab_municipios.py ' + year + " " + directorio ) != 0:
		raise Exception('Error al momento de realizar el proceso de generar tabla crosstab municipios.')


	#GENERAR MAPA ARIDEZ POR USYV
	print("Proceso de CrossTab usyv ...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/tendencia/procesos/evaluacion_multicriterio/realizar_crosstab_usyv.py ' + year + " " + directorio ) != 0:
		raise Exception('Error al momento de realizar el proceso de Crosstab usyv.')	

	#leer los valores del html generado y generar un html con los nuevos datos
	print("Proceso de generar tabla crosstab usyv ...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/tendencia/procesos/evaluacion_multicriterio/generar_tabla_crosstab_usyv.py ' + year + " " + directorio ) != 0:
		raise Exception('Error al momento de realizar el proceso de generar tabla crosstab usyv.')





	#GENERAR EL MAPA DE ZONAS ARIDAS
	print("Proceso de CONVERSION VECTOR ZONAS ARIDAS...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/tendencia/procesos/evaluacion_multicriterio/realizar_conversion_vector.py ' + year + " " + directorio + " zonas_aridas" ) != 0:
		raise Exception('Error al momento de realizar el proceso de conversion a vector zonas aridas.')

	print("Proceso de CONVERSION SHAPE ZONAS ARIDAS...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/tendencia/procesos/evaluacion_multicriterio/realizar_conversion_shape.py ' + year + " " + directorio + " zonas_aridas" ) != 0:
		raise Exception('Error al momento de realizar el proceso de conversion a shape zonas aridas.')

#ALMACENAMIENTO POSTGRES
def proceso_almacenamientoPostgres_1(tipo, imagenAlmacenar, year, datoConfig):	
	print("Proceso de almacenamiento ...")			
	if os.system(urlPython27 + " "+ directorio + "/tendencia/procesos/almacenamiento_postgres/create_table_mapa.py " + tipo + " " + db_name + " " + db_host + " " + db_user + " " + db_password + " " + imagenAlmacenar + " " + year + " " + '"' + directorioPosgrest + '"') != 0:
		raise Exception('Error al momento de realizar el proceso de Almacenamiento.')

def proceso_actualizacionPostgres_2(year, datoConfig):	
	print("Proceso de actualizacion ...")			
	if os.system(urlPython27 + " "+ directorio + "/tendencia/procesos/almacenamiento_postgres/update_table_mapa1.py " + db_name + " " + db_host + " " + db_user + " " + db_password  + " " + year + " " + '"' + directorioPosgrest + '"') != 0:
		raise Exception('Error al momento de realizar el proceso de Almacenamiento1.')

	if os.system(urlPython27 + " "+ directorio + "/tendencia/procesos/almacenamiento_postgres/update_table_mapa2.py " + db_name + " " + db_host + " " + db_user + " " + db_password  + " " + year + " " + '"' + directorioPosgrest + '"') != 0:
		raise Exception('Error al momento de realizar el proceso de Almacenamiento2.')

#SUBIR GEOSERVER
def proceso_publicarMapaGeoServerVariables(mapa, variable, year, datoConfig):	
	print("Proceso de publicacion del mapa de  ..." + variable)			
	prMapa = mapa
	prVariable = variable
	year = year	

	#import descarga
	from src.procesos.subir_geoserver import acceder_geoserver_publicar_mapa_variables
	acceder_geoserver_publicar_mapa_variables.constructor(prMapa, prVariable, year, directorio)

def proceso_publicarMapaZonasAridasGeoServer(mapa, year, datoConfig):	
	print("Proceso de publicacion del mapa de  ..." + mapa)			
	prMapa = mapa
	year = year	

	#import descarga
	from src.procesos.subir_geoserver import acceder_geoserver_publicar_mapa_zonas_aridas
	acceder_geoserver_publicar_mapa_zonas_aridas.constructor(prMapa, year, directorio)

#utilerias
class Config: 
    def __init__(self, 
					year, #A
					finalizado, #B
					finalizoEtapaFactores, #C
					finalizoEtapaEvaluacionesMulticriterio, #D
					finalizoEtapaAlmacenamientoPostgres, #E
					finalizoEtapaSubirGeoserver #F
				): 
        self.year = year 
        self.finalizado = finalizado       
        self.finalizoEtapaFactores = finalizoEtapaFactores
        self.finalizoEtapaEvaluacionesMulticriterio = finalizoEtapaEvaluacionesMulticriterio
        self.finalizoEtapaAlmacenamientoPostgres = finalizoEtapaAlmacenamientoPostgres
        self.finalizoEtapaSubirGeoserver = finalizoEtapaSubirGeoserver


def leer_archivo_config(prYear):
	#Abrimos el fichero excel
	documento = xlrd.open_workbook(directorio + "/config_tendencia.xls")
	#Podemos guardar cada una de las hojas por separado
	fechaAnual = documento.sheet_by_index(0)

	for i in range(0, fechaAnual.nrows):
		year = str(int(fechaAnual.cell_value(i,0)))
		if year == prYear:
			finalizado = fechaAnual.cell_value(i, 1)				
			finalizoEtapaFactores = fechaAnual.cell_value(i, 2)
			finalizoEtapaEvaluacionesMulticriterio = fechaAnual.cell_value(i,3)
			finalizoEtapaAlmacenamientoPostgres = fechaAnual.cell_value(i, 4)
			finalizoEtapaSubirGeoserver = fechaAnual.cell_value(i, 5)

			return Config(year, 
				finalizado, 
		        finalizoEtapaFactores,
		        finalizoEtapaEvaluacionesMulticriterio,
		        finalizoEtapaAlmacenamientoPostgres,
				finalizoEtapaSubirGeoserver)
	
	return Config('', 'False', 'False', 'False', 'False', 'False')
			
def actualizar_archivo_config(oConfigYearNueva):

	#obtenemos los datos del archivo
	documentoRead = xlrd.open_workbook(directorio + "/config_tendencia.xls")

	fechaAnualSheetRead = documentoRead.sheet_by_index(0)
	datos = []
	for i in range(0, fechaAnualSheetRead.nrows):
		year = str(int(fechaAnualSheetRead.cell_value(i,0)))
		if year == oConfigYearNueva.year:
			finalizado = oConfigYearNueva.finalizado			
			finalizoEtapaFactores = oConfigYearNueva.finalizoEtapaFactores
			finalizoEtapaEvaluacionesMulticriterio = oConfigYearNueva.finalizoEtapaEvaluacionesMulticriterio
			finalizoEtapaAlmacenamientoPostgres = oConfigYearNueva.finalizoEtapaAlmacenamientoPostgres
			finalizoEtapaSubirGeoserver = oConfigYearNueva.finalizoEtapaSubirGeoserver
		else:
			finalizado = fechaAnualSheetRead.cell_value(i,1)			
			finalizoEtapaFactores = fechaAnualSheetRead.cell_value(i,8)
			finalizoEtapaEvaluacionesMulticriterio = fechaAnualSheetRead.cell_value(i,9)
			finalizoEtapaAlmacenamientoPostgres = fechaAnualSheetRead.cell_value(i,10)
			finalizoEtapaSubirGeoserver = fechaAnualSheetRead.cell_value(i,11)

		datos.append(Config(year, 
			finalizado, 
	        finalizoEtapaFactores,
	        finalizoEtapaEvaluacionesMulticriterio,
	        finalizoEtapaAlmacenamientoPostgres,
			finalizoEtapaSubirGeoserver))



	#reescribimos el archivo en excel con los nuevos datos
	documentoWrite = xlwt.Workbook(directorio + "config_tendencia.xls")

	#Podemos guardar cada una de las hojas por separado	
	fechaAnualSheetWrite = documentoWrite.add_sheet('config')

	for x in range(0,len(datos)):	
		fechaAnualSheetWrite.write(x,0,datos[x].year)
		fechaAnualSheetWrite.write(x,1,datos[x].finalizado)	
		fechaAnualSheetWrite.write(x,2,datos[x].finalizoEtapaFactores)
		fechaAnualSheetWrite.write(x,3,datos[x].finalizoEtapaEvaluacionesMulticriterio)
		fechaAnualSheetWrite.write(x,4,datos[x].finalizoEtapaAlmacenamientoPostgres)
		fechaAnualSheetWrite.write(x,5,datos[x].finalizoEtapaSubirGeoserver)

	documentoWrite.save(directorio + '/config_tendencia.xls')

def agregar_archivo_config(yearNuevo):
	#obtenemos los datos del archivo
	documentoRead = xlrd.open_workbook(directorio + "/config_tendencia.xls")

	fechaAnualSheetRead = documentoRead.sheet_by_index(0)
	datos = []
	for i in range(0, fechaAnualSheetRead.nrows):
		year = fechaAnualSheetRead.cell_value(i,0)
		finalizado = fechaAnualSheetRead.cell_value(i,1)		
		finalizoEtapaFactores = fechaAnualSheetRead.cell_value(i,2)
		finalizoEtapaEvaluacionesMulticriterio = fechaAnualSheetRead.cell_value(i,3)
		finalizoEtapaAlmacenamientoPostgres = fechaAnualSheetRead.cell_value(i,4)
		finalizoEtapaSubirGeoserver = fechaAnualSheetRead.cell_value(i,5)

		datos.append(Config(year, 
			finalizado, 
	        finalizoEtapaFactores,
	        finalizoEtapaEvaluacionesMulticriterio,
	        finalizoEtapaAlmacenamientoPostgres,
			finalizoEtapaSubirGeoserver))

	#agregamos el nuevo valor al arreglo
	datos.append(Config(yearNuevo, 'False', 'False', 'False', 'False', 'False'))

	#reescribimos el archivo en excel con los nuevos datos
	documentoWrite = xlwt.Workbook(directorio + "/config_tendencia.xls")

	#Podemos guardar cada una de las hojas por separado	
	fechaAnualSheetWrite = documentoWrite.add_sheet('config')

	for x in range(0,len(datos)):	
		fechaAnualSheetWrite.write(x,0,datos[x].year)
		fechaAnualSheetWrite.write(x,1,datos[x].finalizado)		
		fechaAnualSheetWrite.write(x,2,datos[x].finalizoEtapaFactores)
		fechaAnualSheetWrite.write(x,3,datos[x].finalizoEtapaEvaluacionesMulticriterio)
		fechaAnualSheetWrite.write(x,4,datos[x].finalizoEtapaAlmacenamientoPostgres)
		fechaAnualSheetWrite.write(x,5,datos[x].finalizoEtapaSubirGeoserver)

	documentoWrite.save(directorio + '/config_tendencia.xls')

#general
def limpiarImagenesGeneradas(year,datoConfig):
	for i in range(0,len(variables)):	
		ruta = directorio + "/tendencia/data/factores/" + variables[i] + "/" + year
		if os.path.exists(ruta):
			shutil.rmtree(ruta)

	ruta = directorio + "/tendencia/data/evaluacion_multicriterio/" + year
	if os.path.exists(ruta):
		ruta3 = directorio + "\\tendencia\\data\\evaluacion_multicriterio\\" + year + "\\*"
		for name in glob.glob(ruta3): 
			x = name.split('\\')
			file = x[len(x)-1]
			if file != 'table_cross_' + year + '.html':
				os.remove(name)
			


if __name__ == '__main__':
	if len(sys.argv) == 1:
		print('Proporcione el año a procesar...')
		exit(99)

	yearInicial = sys.argv[1] #2023

	#verificar que el año sea mayor al año actual del servidor
	currentData = datetime.now().date()
	yearActualServidor = currentData.strftime("%Y")
	if not int(yearInicial) > int(yearActualServidor): 
		print(f"El año tiene que se mayor a: {yearActualServidor}")
		exit()

	#aqui inicia el algoritmo
	dato = leer_archivo_config(yearInicial)
	if dato.year == '':			
		agregar_archivo_config(yearInicial)
	elif dato.finalizado == 'True':
		print('El año ya esta procesado...')
		exit(3)


	#agregamos el año como inconcluso al archivo
	datoConfig = leer_archivo_config(yearInicial)
	yearActual = datoConfig.year
	print("Procesando el año: " + yearActual)		

	intentos = 0
	#se da por echo que no ha finalizado el proceso
	estaFinalizado = False    
	while(not estaFinalizado):
		
		try:
			datoConfig = leer_archivo_config(yearInicial)
			yearActual = datoConfig.year

			print("Inicio la etapa de Factorizacion")	
			#verificar que aun no ha terminado la etapa de factores
			datoConfig = leer_archivo_config(yearInicial)
			print("Proceso de factorizacion...")	
			if datoConfig.finalizoEtapaFactores == "False":	                
				for i in range(0,len(variables)):
					proceso_multiplicacion_1(variables[i],valores_tendencia[i] , yearActual,datoConfig)         
					
				for i in range(0,len(factores)):
					if(factores[i] != 'pendientes' and factores[i] != 'orientaciones'):	
						proceso_factores_1(factores[i], yearActual,datoConfig)

				datoConfig2 = leer_archivo_config(yearInicial)
				datoConfig2.finalizoEtapaFactores = 'True'
				actualizar_archivo_config(datoConfig2)              
			print("Finalizo la etapa de Factorizacion")
			
			print('___')				

			print("Inicio la etapa de Evaluaciones Multicriterios")
			datoConfig = leer_archivo_config(yearInicial)
			if datoConfig.finalizoEtapaEvaluacionesMulticriterio == "False":	

				imagenesFactores = []
				for i in range(0,len(factores)):
					if(factores[i] != 'pendientes' and factores[i] != 'orientaciones'):	
						imagenesFactores.append(directorio + "/tendencia/data/factores/"+ factores[i] + "/"+yearActual + "/" + "fac_" + factores[i] + "_" + yearActual)
					else:
						imagenesFactores.append(directorio + "/tendencia/data/factores/"+ factores[i] + "/"+ "fac_" + factores[i])	
				
				proceso_evaluacionesMulticriterio_1(factores, imagenesFactores, factores_pesos, yearActual,datoConfig)

				datoConfig2 = leer_archivo_config(yearInicial)
				datoConfig2.finalizoEtapaEvaluacionesMulticriterio = 'True'
				actualizar_archivo_config(datoConfig2)
			print("Finalizo la etapa de Evaluaciones Multicriterios")

			print('___')			

			print("Inicio la etapa de Almacenamiento PostGres")
			datoConfig = leer_archivo_config(yearInicial)
			if datoConfig.finalizoEtapaAlmacenamientoPostgres == "False":	

				#variables
				for i in range(0,len(variables)):	
					dirImage = directorio + "/tendencia/data/factores/" + variables[i] + "/" + yearInicial + "/tend_var_" + variables[i] + "_" + yearInicial + ".shp" 
					
					proceso_almacenamientoPostgres_1(variables[i], dirImage, yearActual,datoConfig)
				
				#evaluacion_multicriterio
				dirImage = directorio + "/tendencia/data/evaluacion_multicriterio/" + yearInicial + "/tend_zonas_aridas_" + yearInicial + ".shp" 
				proceso_almacenamientoPostgres_1("evaluacion_multicriterio", dirImage, yearActual,datoConfig)

				#actualizar el mapa de zonas aridas para agregar la columna de las categorias
				proceso_actualizacionPostgres_2(yearActual,datoConfig)

				datoConfig2 = leer_archivo_config(yearInicial)
				datoConfig2.finalizoEtapaAlmacenamientoPostgres = 'True'
				actualizar_archivo_config(datoConfig2)
			print("Finalizo la etapa de Almacenamiento PostGres")

			print('___')

			print("Proceso eliminacion de imagenes generadas...")	
			#limpiarImagenesGeneradas(yearActual,datoConfig)


			print('___')			

			print("Inicio la etapa de Subir a Geoserver")
			if datoConfig.finalizoEtapaSubirGeoserver == "False":
				#SELENIUM
				#abrir el servidor de geoserver para hacer la publicacion de los mapas de variables
				for i in range(0,len(variables)):
					#proceso_publicarMapaGeoServer("var_" + variables[i]+ "_" + yearActual,variables[i],yearActual,datoConfig)
					proceso_publicarMapaGeoServerVariables("tend_var_" + variables[i]+ "_" + yearActual,variables[i],yearActual,datoConfig)
				
				#publicar el mapap de zonas_aridas
				proceso_publicarMapaZonasAridasGeoServer("tend_zonas_aridas_" + yearActual,yearActual,datoConfig)


				datoConfig2 = leer_archivo_config(yearInicial)
				datoConfig2.finalizoEtapaSubirGeoserver = 'True'
				actualizar_archivo_config(datoConfig2)
			print("Finalizo la etapa de Subir a Geoserver")

			estaFinalizado = True
			datoConfig2 = leer_archivo_config(yearInicial)
			datoConfig2.finalizado = 'True'
			actualizar_archivo_config(datoConfig2)

			exit(4)
		except Exception as e:
			print(e)
		except TimeoutException as ex:
			print(ex)

		intentos = intentos + 1
		if intentos == 1: #3
			estaFinalizado = True			
			print("El proceso se finalizo por que se produjerón 3 intentos erroneos.")
			exit(5)


