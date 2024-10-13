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
directorioAREATif = directorio + "/src/utilerias/AREA_/AREA_.tif"
directorioAREA = directorio + "/src/utilerias/AREA/AREA.shp" 
variables = ['precipitacion', 'evapotranspiracion', 'humedad', 'temperatura', 'indiceDeVegetacion']


#FACTORES
factores = ['precipitacion', 'temperatura', 'indiceDeVegetacion', 'evapotranspiracion', 'humedad', 'pendientes', 'orientaciones']
directorioAREARst = directorio + "/src/utilerias/AREA/AREA.rst" 
directorioAREARdc = directorio + "/src/utilerias/AREA/AREA.RDC" 
factores_pesos = ['0.28', '0.22', '0.19', '0.13', '0.09', '0.06', '0.03']

##EVALUACIONES MULTICRITERIO
directorioAREABinaryRST = directorio + "/src/utilerias/AREA_B/AREA_B.rst" 
directorioAREABinaryRdc = directorio + "/src/utilerias/AREA_B/AREA_B.RDC" 


#ALMACENAMIENTO POSTGRES
db_name = 'zonas_aridas'
db_host = 'localhost'
db_user = 'postgres'
db_password = 'postgres'
directorioPosgrest = "C:/Program Files/PostgreSQL/10/bin/"

#SUBIR GEOSERVER
directorioConnectGeoServer = directorio + "/src/utilerias/GEOSERVER/connect.pgraster.xml.inc" 
directorioMappingGeoServer = directorio + "/src/utilerias/GEOSERVER/mapping.pgraster.xml.inc" 


#PREPARACION DE LAS VARIABLES
def proceso_descarga_1(variable, year,datoConfig):
	#creamos los directorios para cada varible asi como las fechas de cuando se realizara la descarga
	if not os.path.exists(directorio + '/src'):
		os.mkdir(directorio + '/src')

	if not os.path.exists(directorio + '/src/data'):
		os.mkdir(directorio + '/src/data')

	if not os.path.exists(directorio + '/src/data/variables'):
		os.mkdir(directorio + '/src/data/variables')
	#creamos el directorio variable actual
	if not os.path.exists(directorio + '/src/data/variables/' + variable):
		os.mkdir(directorio + '/src/data/variables/' + variable)

	#creamos el directorio año actual
	if not os.path.exists(directorio + '/src/data/variables/' + variable + '/' + year):
		os.mkdir(directorio + '/src/data/variables/' + variable + '/' + year)	
		

	if(variable == 'indiceDeVegetacion'):
			
		prVariable = variable
		year = year	
		nombreFile = r"\ds_" + variable + "_" + year
		rutaArchivo = directorio + "\\src\\data\\variables\\"+ variable + "\\"+year 

		from src.procesos.preparacion_variables.descargas import descarga_climate_engine_idv
		descarga_climate_engine_idv.constructor(prVariable, year, nombreFile, rutaArchivo, directorio)
		
	else:

		if variable == 'precipitacion':					
			nombreVariableSelect = 'pr'
		elif  variable == 'evapotranspiracion':	
			nombreVariableSelect = 'pet'
		elif  variable == 'temperatura':	
			nombreVariableSelect = 'tmmx'
		else:
			nombreVariableSelect = 'soil'

		prVariable = variable
		year = year	
		nombreFile = "ds_" + variable + "_" + year

		rutaArchivo = directorio + "\\src\\data\\variables\\"+ variable + "\\"+year 

		#import descarga
		from src.procesos.preparacion_variables.descargas import descarga_climate_engine
		descarga_climate_engine.constructor(nombreVariableSelect, prVariable, year, nombreFile, rutaArchivo,directorio)

def proceso_mosaicos_2(variable, year,datoConfig):		
	prVariable = variable
	year = year	

	#generar el mosaico		
	print("Proceso generar mosaico (IDV)...")
	tipoDato = "32_BIT_FLOAT"
	if os.system(urlPython27 + " "+ directorio + "/src/procesos/preparacion_variables/mosaicos/obtener_mosaicos.py " + prVariable + " " + year + " " + directorio + " " + tipoDato) != 0:
		raise Exception('Error al momento de generar los mosaicos.')
	
def proceso_corte_3(variable, year,datoConfig):	
	print("Proceso de corte (" + variable + ") ...")			
	if os.system(urlPython27 + " "+ directorio + "/src/procesos/preparacion_variables/corte/realizar_corte.py " + variable + " " + year + " " + directorio + " " + directorioAREA) != 0:
		raise Exception('Error al momento de realizar el corte.')

def proceso_proyeccion_4(variable, year,datoConfig):
	print("Proceso de proyeccion (" + variable + ") ...")

	#cambiar la proyeccion
	if os.system(urlPython27 + " "+ directorio + "/src/procesos/preparacion_variables/proyeccion/cambiar_proyeccion.py " + variable + " " + year + " " + directorio) != 0:
		raise Exception('Error al momento cambiar la proyeccion.')

	#cambiar la mascara de los pixeles
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/src/procesos/preparacion_variables/proyeccion/cambiar_mascara.py ' + variable + " " + year + " " + directorio + " " + directorioAREATif) != 0:	
		raise Exception('Error al momento de cambiar la mascara.')

def proceso_correccion_7(variable, year,datoConfig):
	print("Proceso de correccion (" + variable + ") ...")
	if os.system(urlPython27 + " "+ directorio + "/src/procesos/preparacion_variables/correccion/realizar_correccion.py " + variable + " " + year + " " + directorio + " " + directorioAREA + " " + directorioAREATif + " " + '"' + urlPythonQgis + '"' + " " + pixelesEnteros + " " + urlPython27) != 0:
		raise Exception('Error al momento de realizar la corrección.')
	
#FACTORES
def proceso_factores_1(factor, year,datoConfig):
	if not os.path.exists(directorio + '/src/data/factores'):
		os.mkdir(directorio + '/src/data/factores')
		
	if  not os.path.exists(directorio + "/src/data/factores/pendientes"):
		os.mkdir(directorio + "/src/data/factores/pendientes")
		shutil.copy(directorio + "/src/utilerias/pendientes/fac_pendientes.rst", directorio + "/src/data/factores/pendientes")
		shutil.copy(directorio + "/src/utilerias/pendientes/fac_pendientes.RDC", directorio + "/src/data/factores/pendientes")

	if  not os.path.exists(directorio + "/src/data/factores/orientaciones"):
		os.mkdir(directorio + "/src/data/factores/orientaciones")
		shutil.copy(directorio + "/src/utilerias/orientaciones/fac_orientaciones.rst", directorio + "/src/data/factores/orientaciones")
		shutil.copy(directorio + "/src/utilerias/orientaciones/fac_orientaciones.RDC", directorio + "/src/data/factores/orientaciones")

	print("Proceso de fuzzy (" + factor + ") ...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/src/procesos/factores/realizar_fuzzy.py ' + factor + " " + year + " " + directorio + " " + directorioAREARst + " " + directorioAREARdc) != 0:
		raise Exception('Error al momento de realizar el proceso de fuzzy.')

	print("Proceso de overlay (" + factor + ") ...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/src/procesos/factores/realizar_overlay.py ' + factor + " " + year + " " + directorio + " " + directorioAREARst + " " + directorioAREARdc) != 0:
		raise Exception('Error al momento de realizar el proceso de overlay.')


#EVALUACIONES MULTICRITERIO
def proceso_evaluacionesMulticriterio_1(factores, imagenesFactores, factores_pesos, year, datoConfig):	
	factoresString = ','.join(imagenesFactores)
	pesosString = ','.join(factores_pesos)

	if not os.path.exists(directorio + '/src/data/evaluacion_multicriterio'):
		os.mkdir(directorio + '/src/data/evaluacion_multicriterio')
	
	print("Proceso de MCE ...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/src/procesos/evaluacion_multicriterio/realizar_mce.py ' + factoresString + " " + pesosString + " " + year + " " + directorio + " " + directorioAREABinaryRST) != 0:
		raise Exception('Error al momento de realizar el proceso de MCE.')

	print("Proceso de RECLASS ...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/src/procesos/evaluacion_multicriterio/realizar_reclass.py ' + year + " " + directorio ) != 0:
		raise Exception('Error al momento de realizar el proceso de MCE.')
		
	#GENERAR MAPA ARIDEZ POR ESTADOS
	print("Proceso de CrossTab estados ...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/src/procesos/evaluacion_multicriterio/realizar_crosstab_estados.py ' + year + " " + directorio ) != 0:
		raise Exception('Error al momento de realizar el proceso de Crosstab estados.')	

	#leer los valores del html generado y generar un html con los nuevos datos
	print("Proceso de generar tabla crosstab estados ...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/src/procesos/evaluacion_multicriterio/generar_tabla_crosstab_estados.py ' + year + " " + directorio ) != 0:
		raise Exception('Error al momento de realizar el proceso de generar tabla crosstab estados.')
	
	#GENERAR INDICADOR ARIDES
	print("Proceso de CrossTab INDICADOR ARIDES...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/src/procesos/evaluacion_multicriterio/realizar_crosstab_indicador_aridez.py ' + year + " " + directorio ) != 0:
		raise Exception('Error al momento de realizar el proceso de Crosstab indicador aridez.')

	#leer los valores del html generado y generar un html con los nuevos datos
	print("Proceso de generar tabla crosstab INDICADOR ARIDES...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/src/procesos/evaluacion_multicriterio/generar_tabla_crosstab_indicador_aridez.py ' + year + " " + directorio ) != 0:
		raise Exception('Error al momento de realizar el proceso de generar tabla crosstab indicador aridez.')
	

	#GENERAR MAPA ARIDEZ POR CUENCAS
	print("Proceso de CrossTab cuencas ...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/src/procesos/evaluacion_multicriterio/realizar_crosstab_cuencas.py ' + year + " " + directorio ) != 0:
		raise Exception('Error al momento de realizar el proceso de Crosstab cuencas.')	

	#leer los valores del html generado y generar un html con los nuevos datos
	print("Proceso de generar tabla crosstab cuencas ...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/src/procesos/evaluacion_multicriterio/generar_tabla_crosstab_cuencas.py ' + year + " " + directorio ) != 0:
		raise Exception('Error al momento de realizar el proceso de generar tabla crosstab cuencas.')
	

	#GENERAR MAPA ARIDEZ POR MUNICIPIOS
	print("Proceso de CrossTab municipios ...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/src/procesos/evaluacion_multicriterio/realizar_crosstab_municipios.py ' + year + " " + directorio ) != 0:
		raise Exception('Error al momento de realizar el proceso de Crosstab municipios.')	

	#leer los valores del html generado y generar un html con los nuevos datos
	print("Proceso de generar tabla crosstab municipios ...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/src/procesos/evaluacion_multicriterio/generar_tabla_crosstab_municipios.py ' + year + " " + directorio ) != 0:
		raise Exception('Error al momento de realizar el proceso de generar tabla crosstab municipios.')
	

	#GENERAR MAPA ARIDEZ POR USYV
	print("Proceso de CrossTab usyv ...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/src/procesos/evaluacion_multicriterio/realizar_crosstab_usyv.py ' + year + " " + directorio ) != 0:
		raise Exception('Error al momento de realizar el proceso de Crosstab usyv.')	

	#leer los valores del html generado y generar un html con los nuevos datos
	print("Proceso de generar tabla crosstab usyv ...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/src/procesos/evaluacion_multicriterio/generar_tabla_crosstab_usyv.py ' + year + " " + directorio ) != 0:
		raise Exception('Error al momento de realizar el proceso de generar tabla crosstab usyv.')
	

	#GENERAR EL MAPA DE ZONAS ARIDAS
	print("Proceso de CONVERSION VECTOR ZONAS ARIDAS...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/src/procesos/evaluacion_multicriterio/realizar_conversion_vector.py ' + year + " " + directorio + " zonas_aridas" ) != 0:
		raise Exception('Error al momento de realizar el proceso de conversion a vector zonas aridas.')

	print("Proceso de CONVERSION SHAPE ZONAS ARIDAS...")			
	if os.system('"' + urlPythonQgis + '" '+ directorio+'/src/procesos/evaluacion_multicriterio/realizar_conversion_shape.py ' + year + " " + directorio + " zonas_aridas" ) != 0:
		raise Exception('Error al momento de realizar el proceso de conversion a shape zonas aridas.')
	
#ALMACENAMIENTO POSTGRES
def proceso_almacenamientoPostgres_1(tipo, imagenAlmacenar, year, datoConfig):	
	print("Proceso de almacenamiento ...")			
	if os.system(urlPython27 + " "+ directorio + "/src/procesos/almacenamiento_postgres/create_table_mapa.py " + tipo + " " + db_name + " " + db_host + " " + db_user + " " + db_password + " " + imagenAlmacenar + " " + year + " " + '"' + directorioPosgrest + '"') != 0:
		raise Exception('Error al momento de realizar el proceso de Almacenamiento.')

def proceso_actualizacionPostgres_2(year, datoConfig):	
	print("Proceso de actualizacion ...")			
	if os.system(urlPython27 + " "+ directorio + "/src/procesos/almacenamiento_postgres/update_table_mapa1.py " + db_name + " " + db_host + " " + db_user + " " + db_password  + " " + year + " " + '"' + directorioPosgrest + '"') != 0:
		raise Exception('Error al momento de realizar el proceso de Almacenamiento1.')

	if os.system(urlPython27 + " "+ directorio + "/src/procesos/almacenamiento_postgres/update_table_mapa2.py " + db_name + " " + db_host + " " + db_user + " " + db_password  + " " + year + " " + '"' + directorioPosgrest + '"') != 0:
		raise Exception('Error al momento de realizar el proceso de Almacenamiento2.')

def proceso_insertarMosaic(mapa, year, datoConfig):	
	print("Proceso de insertar en la tabla mosaic ..." + mapa)			
	if os.system(urlPython27 + " "+ directorio + "/src/procesos/almacenamiento_postgres/insert_table_mosaic.py " + mapa + " " + db_name + " " + db_host + " " + db_user + " " + db_password  + " " + year + " " + '"' + directorioPosgrest + '"') != 0:
		raise Exception('Error al momento de realizar el proceso de insert en la tabla mosaic.' + mapa)

def proceso_crearTableMosaic(table, year, datoConfig):	
	print("Proceso de creacion de la tabla ..." + table)			
	if os.system(urlPython27 + " "+ directorio + "/src/procesos/almacenamiento_postgres/create_table_mosaic.py " + table + " " + db_name + " " + db_host + " " + db_user + " " + db_password  + " " + year + " " + '"' + directorioPosgrest + '"') != 0:
		raise Exception('Error al momento de realizar el proceso de creacion de la tabla ' + table)

#SUBIR GEOSERVER
"""def proceso_crearXmlMapa(mapa, year, datoConfig):	
	if not os.path.exists(directorio + '/src/data/subir_geoserver'):
		os.mkdir(directorio + '/src/data/subir_geoserver')

	print("Proceso de creacion del archivo .xml ..." + mapa)			
	if os.system(urlPython27 + " "+ directorio + "/src/procesos/subir_geoserver/crear_archivo_xml.py " + mapa + " " + directorio + " " + directorioConnectGeoServer + " " + directorioMappingGeoServer + " " + year) != 0:
		raise Exception('Error al momento de realizar el proceso de creacion del archivo .xml ... ' + mapa)

def proceso_publicarMapaGeoServer(mapa, variable, year, datoConfig):	
	print("Proceso de publicacion del mapa de  ..." + mapa)			
	prMapa = mapa
	prVariable = variable
	year = year	
	nombreFile = mapa + ".xml"
	rutaXml = directorio + "\\src\\data\\subir_geoserver\\"+ year + "\\" + nombreFile 

	#import descarga
	from src.procesos.subir_geoserver import acceder_geoserver_publicar_mapa
	acceder_geoserver_publicar_mapa.constructor(prMapa, prVariable, year, nombreFile, rutaXml)"""

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
					finalizoProcesoDescargas, #C
					finalizoProcesoMosaicos, #D
					finalizoProcesoCortes, #E
					finalizoProcesoProyeccion, #F
					finalizoProcesoCorrecciones, #G
					finalizoEtapaPreparacion, #H
					finalizoEtapaFactores, #I
					finalizoEtapaEvaluacionesMulticriterio, #J
					finalizoEtapaAlmacenamientoPostgres, #K
					finalizoEtapaSubirGeoserver #L
				): 
        self.year = year 
        self.finalizado = finalizado       
        self.finalizoProcesoDescargas = finalizoProcesoDescargas
        self.finalizoProcesoMosaicos = finalizoProcesoMosaicos
        self.finalizoProcesoCortes = finalizoProcesoCortes
        self.finalizoProcesoProyeccion = finalizoProcesoProyeccion      
        self.finalizoProcesoCorrecciones = finalizoProcesoCorrecciones
        self.finalizoEtapaPreparacion = finalizoEtapaPreparacion
        self.finalizoEtapaFactores = finalizoEtapaFactores
        self.finalizoEtapaEvaluacionesMulticriterio = finalizoEtapaEvaluacionesMulticriterio
        self.finalizoEtapaAlmacenamientoPostgres = finalizoEtapaAlmacenamientoPostgres
        self.finalizoEtapaSubirGeoserver = finalizoEtapaSubirGeoserver


def leer_archivo_config(prYear):
	#Abrimos el fichero excel
	documento = xlrd.open_workbook(directorio + "/config.xls")
	#Podemos guardar cada una de las hojas por separado
	fechaAnual = documento.sheet_by_index(0)

	for i in range(0, fechaAnual.nrows):
		year = str(int(fechaAnual.cell_value(i,0)))
		if year == prYear:
			finalizado = fechaAnual.cell_value(i, 1)	
			finalizoProcesoDescargas = fechaAnual.cell_value(i, 2)
			finalizoProcesoMosaicos = fechaAnual.cell_value(i, 3)
			finalizoProcesoCortes = fechaAnual.cell_value(i, 4)
			finalizoProcesoProyeccion = fechaAnual.cell_value(i, 5)
			finalizoProcesoCorrecciones = fechaAnual.cell_value(i, 6)
			finalizoEtapaPreparacion = fechaAnual.cell_value(i, 7)
			finalizoEtapaFactores = fechaAnual.cell_value(i, 8)
			finalizoEtapaEvaluacionesMulticriterio = fechaAnual.cell_value(i, 9)
			finalizoEtapaAlmacenamientoPostgres = fechaAnual.cell_value(i, 10)
			finalizoEtapaSubirGeoserver = fechaAnual.cell_value(i, 11)

			return Config(year, 
				finalizado, 
				finalizoProcesoDescargas,
				finalizoProcesoMosaicos,
				finalizoProcesoCortes,
				finalizoProcesoProyeccion,
				finalizoProcesoCorrecciones,
				finalizoEtapaPreparacion,
		        finalizoEtapaFactores,
		        finalizoEtapaEvaluacionesMulticriterio,
		        finalizoEtapaAlmacenamientoPostgres,
				finalizoEtapaSubirGeoserver)
	
	return Config('', 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False')
			

def actualizar_archivo_config(oConfigYearNueva):

	#obtenemos los datos del archivo
	documentoRead = xlrd.open_workbook(directorio + "/config.xls")

	fechaAnualSheetRead = documentoRead.sheet_by_index(0)
	datos = []
	for i in range(0, fechaAnualSheetRead.nrows):
		year = str(int(fechaAnualSheetRead.cell_value(i,0)))
		if year == oConfigYearNueva.year:
			finalizado = oConfigYearNueva.finalizado
			finalizoProcesoDescargas = oConfigYearNueva.finalizoProcesoDescargas
			finalizoProcesoMosaicos = oConfigYearNueva.finalizoProcesoMosaicos
			finalizoProcesoCortes = oConfigYearNueva.finalizoProcesoCortes
			finalizoProcesoProyeccion = oConfigYearNueva.finalizoProcesoProyeccion
			finalizoProcesoCorrecciones = oConfigYearNueva.finalizoProcesoCorrecciones
			finalizoEtapaPreparacion = oConfigYearNueva.finalizoEtapaPreparacion
			finalizoEtapaFactores = oConfigYearNueva.finalizoEtapaFactores
			finalizoEtapaEvaluacionesMulticriterio = oConfigYearNueva.finalizoEtapaEvaluacionesMulticriterio
			finalizoEtapaAlmacenamientoPostgres = oConfigYearNueva.finalizoEtapaAlmacenamientoPostgres
			finalizoEtapaSubirGeoserver = oConfigYearNueva.finalizoEtapaSubirGeoserver
		else:
			finalizado = fechaAnualSheetRead.cell_value(i,1)
			finalizoProcesoDescargas = fechaAnualSheetRead.cell_value(i,2)
			finalizoProcesoMosaicos = fechaAnualSheetRead.cell_value(i,3)
			finalizoProcesoCortes = fechaAnualSheetRead.cell_value(i,4)
			finalizoProcesoProyeccion = fechaAnualSheetRead.cell_value(i,5)
			finalizoProcesoCorrecciones = fechaAnualSheetRead.cell_value(i,6)
			finalizoEtapaPreparacion = fechaAnualSheetRead.cell_value(i,7)
			finalizoEtapaFactores = fechaAnualSheetRead.cell_value(i,8)
			finalizoEtapaEvaluacionesMulticriterio = fechaAnualSheetRead.cell_value(i,9)
			finalizoEtapaAlmacenamientoPostgres = fechaAnualSheetRead.cell_value(i,10)
			finalizoEtapaSubirGeoserver = fechaAnualSheetRead.cell_value(i,11)

		datos.append(Config(year, 
			finalizado, 
			finalizoProcesoDescargas,
			finalizoProcesoMosaicos,
			finalizoProcesoCortes,
			finalizoProcesoProyeccion,
			finalizoProcesoCorrecciones,
			finalizoEtapaPreparacion,
	        finalizoEtapaFactores,
	        finalizoEtapaEvaluacionesMulticriterio,
	        finalizoEtapaAlmacenamientoPostgres,
			finalizoEtapaSubirGeoserver))



	#reescribimos el archivo en excel con los nuevos datos
	documentoWrite = xlwt.Workbook(directorio + "config.xls")

	#Podemos guardar cada una de las hojas por separado	
	fechaAnualSheetWrite = documentoWrite.add_sheet('config')

	for x in range(0,len(datos)):	
		fechaAnualSheetWrite.write(x,0,datos[x].year)
		fechaAnualSheetWrite.write(x,1,datos[x].finalizado)
		fechaAnualSheetWrite.write(x,2,datos[x].finalizoProcesoDescargas)
		fechaAnualSheetWrite.write(x,3,datos[x].finalizoProcesoMosaicos)
		fechaAnualSheetWrite.write(x,4,datos[x].finalizoProcesoCortes)
		fechaAnualSheetWrite.write(x,5,datos[x].finalizoProcesoProyeccion)
		fechaAnualSheetWrite.write(x,6,datos[x].finalizoProcesoCorrecciones)
		fechaAnualSheetWrite.write(x,7,datos[x].finalizoEtapaPreparacion)
		fechaAnualSheetWrite.write(x,8,datos[x].finalizoEtapaFactores)
		fechaAnualSheetWrite.write(x,9,datos[x].finalizoEtapaEvaluacionesMulticriterio)
		fechaAnualSheetWrite.write(x,10,datos[x].finalizoEtapaAlmacenamientoPostgres)
		fechaAnualSheetWrite.write(x,11,datos[x].finalizoEtapaSubirGeoserver)

	documentoWrite.save(directorio + '/config.xls')

def agregar_archivo_config(yearNuevo):
	#obtenemos los datos del archivo
	documentoRead = xlrd.open_workbook(directorio + "/config.xls")

	fechaAnualSheetRead = documentoRead.sheet_by_index(0)
	datos = []
	for i in range(0, fechaAnualSheetRead.nrows):
		year = fechaAnualSheetRead.cell_value(i,0)
		finalizado = fechaAnualSheetRead.cell_value(i,1)
		finalizoProcesoDescargas = fechaAnualSheetRead.cell_value(i,2)
		finalizoProcesoMosaicos = fechaAnualSheetRead.cell_value(i,3)
		finalizoProcesoCortes = fechaAnualSheetRead.cell_value(i,4)
		finalizoProcesoProyeccion = fechaAnualSheetRead.cell_value(i,5)
		finalizoProcesoCorrecciones = fechaAnualSheetRead.cell_value(i,6)
		finalizoEtapaPreparacion = fechaAnualSheetRead.cell_value(i,7)
		finalizoEtapaFactores = fechaAnualSheetRead.cell_value(i,8)
		finalizoEtapaEvaluacionesMulticriterio = fechaAnualSheetRead.cell_value(i,9)
		finalizoEtapaAlmacenamientoPostgres = fechaAnualSheetRead.cell_value(i,10)
		finalizoEtapaSubirGeoserver = fechaAnualSheetRead.cell_value(i,11)

		datos.append(Config(year, 
			finalizado, 
			finalizoProcesoDescargas,
			finalizoProcesoMosaicos,
			finalizoProcesoCortes,
			finalizoProcesoProyeccion,
			finalizoProcesoCorrecciones,
			finalizoEtapaPreparacion,
	        finalizoEtapaFactores,
	        finalizoEtapaEvaluacionesMulticriterio,
	        finalizoEtapaAlmacenamientoPostgres,
			finalizoEtapaSubirGeoserver))

	#agregamos el nuevo valor al arreglo
	datos.append(Config(yearNuevo, 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False'))

	#reescribimos el archivo en excel con los nuevos datos
	documentoWrite = xlwt.Workbook(directorio + "/config.xls")

	#Podemos guardar cada una de las hojas por separado	
	fechaAnualSheetWrite = documentoWrite.add_sheet('config')

	for x in range(0,len(datos)):	
		fechaAnualSheetWrite.write(x,0,datos[x].year)
		fechaAnualSheetWrite.write(x,1,datos[x].finalizado)
		fechaAnualSheetWrite.write(x,2,datos[x].finalizoProcesoDescargas)
		fechaAnualSheetWrite.write(x,3,datos[x].finalizoProcesoMosaicos)
		fechaAnualSheetWrite.write(x,4,datos[x].finalizoProcesoCortes)
		fechaAnualSheetWrite.write(x,5,datos[x].finalizoProcesoProyeccion)		
		fechaAnualSheetWrite.write(x,6,datos[x].finalizoProcesoCorrecciones)
		fechaAnualSheetWrite.write(x,7,datos[x].finalizoEtapaPreparacion)
		fechaAnualSheetWrite.write(x,8,datos[x].finalizoEtapaFactores)
		fechaAnualSheetWrite.write(x,9,datos[x].finalizoEtapaEvaluacionesMulticriterio)
		fechaAnualSheetWrite.write(x,10,datos[x].finalizoEtapaAlmacenamientoPostgres)
		fechaAnualSheetWrite.write(x,11,datos[x].finalizoEtapaSubirGeoserver)

	documentoWrite.save(directorio + '/config.xls')

#general
def verificar_datos_descarga_por_year(prYearActual):
	from src.procesos.preparacion_variables.descargas import verificar_datos_descargar_por_year_climate
	resultadoClimate = verificar_datos_descargar_por_year_climate.constructor("pr", prYearActual, directorio)
	return resultadoClimate

def limpiarImagenesGeneradas(year,datoConfig):
	for i in range(0,len(variables)):	
		ruta = directorio + "/src/data/variables/" + variables[i] + "/" + year
		if os.path.exists(ruta):
			if year == '2020':
				ruta2 = directorio + "\\src\\data\\variables\\" + variables[i] + "\\" + year + "\\*"
				for name in glob.glob(ruta2): 
					x = name.split('\\')
					file = x[len(x)-1]
					if file != 'var_' + variables[i] + '_' + year + '.rst' and file != 'var_' + variables[i] + '_' + year + '.rdc':
						os.remove(name)
			else:		
				shutil.rmtree(ruta)

		ruta = directorio + "/src/data/factores/" + variables[i] + "/" + year
		if os.path.exists(ruta):
			shutil.rmtree(ruta)

	ruta = directorio + "/src/data/evaluacion_multicriterio/" + year
	if os.path.exists(ruta):
		ruta3 = directorio + "\\src\\data\\evaluacion_multicriterio\\" + year + "\\*"
		for name in glob.glob(ruta3): 
			x = name.split('\\')
			file = x[len(x)-1]
			if file != 'table_cross_' + year + '.html':
				os.remove(name)
			


if __name__ == '__main__':
	if len(sys.argv) == 1:
		print('Proporcione el año a procesar...')
		exit(99)
	
	yearInicial = sys.argv[1] #2019

	#aqui inicia el algoritmo
	dato = leer_archivo_config(yearInicial)
	if dato.year == '':
		if verificar_datos_descarga_por_year(yearInicial) == True:			
			agregar_archivo_config(yearInicial)
		else:
			print('El año ' + yearInicial+  'no se puede procesar...')
			exit(2)

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

			print("Inicio la etapa de Prepacion de Variables")		
			#verificar que aun no ha terminado la etapa de preparacion de variables
			if datoConfig.finalizoEtapaPreparacion == "False":	

				#proceso numero 1 descargas
				datoConfig = leer_archivo_config(yearInicial)	
				print("Proceso descargas...")
				if datoConfig.finalizoProcesoDescargas == "False":			
					for i in range(0,len(variables)):	
						proceso_descarga_1(variables[i], yearActual,datoConfig)

					datoConfig2 = leer_archivo_config(yearInicial)
					datoConfig2.finalizoProcesoDescargas = 'True'
					actualizar_archivo_config(datoConfig2)

				#crear los mosaicos de las variables temperatura y indice_vegetacion
				datoConfig = leer_archivo_config(yearInicial)	
				print("Proceso mosaicos...")	
				if datoConfig.finalizoProcesoMosaicos == "False":
					for i in range(0,len(variables)):	
						#sacar mosaicos
						if(variables[i] == 'indiceDeVegetacion'):		
							proceso_mosaicos_2(variables[i], yearActual,datoConfig)

					datoConfig2 = leer_archivo_config(yearInicial)
					datoConfig2.finalizoProcesoMosaicos = 'True'
					actualizar_archivo_config(datoConfig2)

				#realizar el corte a todas las variables
				datoConfig = leer_archivo_config(yearInicial)
				print("Proceso corte...")	
				if datoConfig.finalizoProcesoCortes == "False":	
					for i in range(0,len(variables)):	
						#sacar mosaicos
						proceso_corte_3(variables[i], yearActual,datoConfig)

					datoConfig2 = leer_archivo_config(yearInicial)
					datoConfig2.finalizoProcesoCortes = 'True'
					actualizar_archivo_config(datoConfig2)

				#realizar cambio de proyeccion a todas las variables
				datoConfig = leer_archivo_config(yearInicial)
				print("Proceso proyeccion...")
				if datoConfig.finalizoProcesoProyeccion == "False":		
					for i in range(0,len(variables)):	
						#sacar mosaicos
						proceso_proyeccion_4(variables[i], yearActual,datoConfig)

					datoConfig2 = leer_archivo_config(yearInicial)
					datoConfig2.finalizoProcesoProyeccion = 'True'
					actualizar_archivo_config(datoConfig2)
			
				#realizar la correcion a todas las variables
				datoConfig = leer_archivo_config(yearInicial)
				print("Proceso correcciones...")
				if datoConfig.finalizoProcesoCorrecciones == "False":	
					for i in range(0,len(variables)):	
						#sacar mosaicos
						proceso_correccion_7(variables[i], yearActual,datoConfig)

					datoConfig2 = leer_archivo_config(yearInicial)
					datoConfig2.finalizoProcesoCorrecciones = 'True'
					actualizar_archivo_config(datoConfig2)

				#finalizar la etapa de prepacion de variables	
				datoConfig2 = leer_archivo_config(yearInicial)
				datoConfig2.finalizoEtapaPreparacion = 'True'
				actualizar_archivo_config(datoConfig2)	
			print("Finalizo la etapa de Prepacion de Variables")

			print('___')

			print("Inicio la etapa de Factorizacion")	
			#verificar que aun no ha terminado la etapa de factores
			datoConfig = leer_archivo_config(yearInicial)
			print("Proceso de factorizacion...")	
			if datoConfig.finalizoEtapaFactores == "False":	
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
						imagenesFactores.append(directorio + "/src/data/factores/"+ factores[i] + "/"+yearActual + "/" + "fac_" + factores[i] + "_" + yearActual)
					else:
						imagenesFactores.append(directorio + "/src/data/factores/"+ factores[i] + "/"+ "fac_" + factores[i])	
				
				proceso_evaluacionesMulticriterio_1(factores, imagenesFactores, factores_pesos, yearActual,datoConfig)

				datoConfig2 = leer_archivo_config(yearInicial)
				datoConfig2.finalizoEtapaEvaluacionesMulticriterio = 'True'
				actualizar_archivo_config(datoConfig2)
			print("Finalizo la etapa de Evaluaciones Multicriterios")

			print('___')			

			print("Inicio la etapa de Almacenamiento PostGres")
			datoConfig = leer_archivo_config(yearInicial)
			if datoConfig.finalizoEtapaAlmacenamientoPostgres == "False":	
				#create table mosaic
				#proceso_crearTableMosaic("MOSAIC",yearActual,datoConfig)		

				"""#variables
				for i in range(0,len(variables)):	
					dirImage = directorio + "/src/data/variables/" + variables[i] + "/" + yearInicial + "/var_" + variables[i] + "_" + yearInicial + ".tif" 
					
					proceso_almacenamientoPostgres_1(variables[i], dirImage, yearActual,datoConfig)
				"""
				#variables
				for i in range(0,len(variables)):	
					dirImage = directorio + "/src/data/variables/" + variables[i] + "/" + yearInicial + "/rec_" + variables[i] + "_" + yearInicial + ".shp" 
					
					proceso_almacenamientoPostgres_1(variables[i], dirImage, yearActual,datoConfig)
				
				#evaluacion_multicriterio
				dirImage = directorio + "/src/data/evaluacion_multicriterio/" + yearInicial + "/zonas_aridas_" + yearInicial + ".shp" 
				proceso_almacenamientoPostgres_1("evaluacion_multicriterio", dirImage, yearActual,datoConfig)

				#actualizar el mapa de zonas aridas para agregar la columna de las categorias
				proceso_actualizacionPostgres_2(yearActual,datoConfig)

				"""#insertar en la tabla mosaic cada mapa
				for i in range(0,len(variables)):
					proceso_insertarMosaic("var_" + variables[i]+ "_" + yearActual,yearActual,datoConfig)
				"""
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
				#creamos los xml de todos los mapas
				#variables
				"""for i in range(0,len(variables)):
					proceso_crearXmlMapa("var_" + variables[i]+ "_" + yearActual,yearActual,datoConfig)
				"""
				#SELENIUM
				#abrir el servidor de geoserver para hacer la publicacion de los mapas de variables
				for i in range(0,len(variables)):
					#proceso_publicarMapaGeoServer("var_" + variables[i]+ "_" + yearActual,variables[i],yearActual,datoConfig)
					proceso_publicarMapaGeoServerVariables("var_" + variables[i]+ "_" + yearActual,variables[i],yearActual,datoConfig)
				
				#publicar el mapap de zonas_aridas
				proceso_publicarMapaZonasAridasGeoServer("zonas_aridas_" + yearActual,yearActual,datoConfig)				

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


