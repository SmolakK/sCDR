# -*- coding: utf-8 -*-

import sip
# switch off QString in Python2
sip.setapi('QString', 2)

import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.utils import *
from qgis.core import *
from qgis.gui import *
from form import Ui_Dialog
import random
import numpy as np
from numpy.linalg import eig,inv
import csv
import os
import datetime
from datetime import timedelta
import math
import processing
import operator
import cProfile
import pstats
import gc
import itertools
import time

QDir.setCurrent(QDir.homePath()+"\.qgis2\python\plugins\CDR_synthetic_generator")

global ro
global wgs
global wgsps
ro = 2*math.pi/200
wgs = QgsCoordinateReferenceSystem(4326,QgsCoordinateReferenceSystem.EpsgCrsId)
wgsps = QgsCoordinateReferenceSystem(3857,QgsCoordinateReferenceSystem.EpsgCrsId)

class cdr_gen:
	

	def __init__(self,iface):
		self.iface=iface

	def initGui(self):
		self.action = QAction(QIcon("icon.png"), "Synthetic CDR Generator",self.iface.mainWindow())
		self.action.setObjectName("Open")
		self.action.setWhatsThis("Desc")
		self.action.setStatusTip("Tip")
		
		self.menu = QMenu(self.iface.mainWindow())
		self.menu.setObjectName("CDR")
		self.menu.setTitle("CDR")
		self.menu.addAction(self.action)
		
		self.action.triggered.connect(self.run)
		
		menuBar = self.iface.mainWindow().menuBar()
		menuBar.insertMenu(self.iface.firstRightStandardMenu().menuAction(), self.menu)
		
	def unload(self):
		self.menu.deleteLater()
		
	def run(self):
		self.okno = QDialog()
		form = Ui_Dialog()
		form.setupUi(self.okno)
		self.time_resolution = 24.0
		self.time_denominator = (self.time_resolution/24.0)
		#Canvas
		#ComboBoxes
		self.time_agg = form.comboBox_4
		self.time_agg.addItem(QIcon("low.png"),'1 Hour')
		self.time_agg.addItem(QIcon("mid.png"),'30 Minutes')
		self.time_agg.addItem(QIcon("high.png"),'15 Minutes')
		self.time_agg.activated.connect(self.timeAggChanged)
		#Buttons
		self.cdr_list = form.listWidget
		self.home = form.tableWidget
		self.work = form.tableWidget_2
		self.third = form.tableWidget_3
		self.home_weekend = form.tableWidget_4
		self.work_weekend = form.tableWidget_5
		self.third_weekend = form.tableWidget_6
		self.home_loc = form.pushButton
		self.work_loc = form.pushButton_2
		self.home_loc.setEnabled(False)
		self.work_loc.setEnabled(False)
		self.track_file_load = form.pushButton_4
		#self.track_file_load.setEnabled(False)
		#CheckBoxes
		self.checkBox = form.checkBox
		#TexEdits
		self.home_coor = form.textEdit
		self.work_coor = form.textEdit_2
		self.home_layer = form.textEdit_3
		self.work_layer = form.textEdit_4
		self.home_coor2 = form.textEdit_5
		self.work_coor2 = form.textEdit_6
		#SpinBox
		self.home_from_hour = form.spinBox.value()
		self.home_from_min = form.spinBox_2.value()
		self.home_to_hour = form.spinBox_4.value()
		self.home_to_min = form.spinBox_3.value()
		self.work_from_hour = form.spinBox_8.value()
		self.work_from_min = form.spinBox_6.value()
		self.work_to_hour = form.spinBox_5.value()
		self.work_to_min = form.spinBox_7.value()
		#DoubleSpinBox
		self.spread_rate = form.doubleSpinBox
		#Label
		self.track_label = form.label_17
		#Buttons
		form.pushButton_5.clicked.connect(self.set_file_CDR)
		form.pushButton_6.clicked.connect(self.load_layer)
		form.pushButton_11.clicked.connect(self.load_layer2)
		form.pushButton_8.clicked.connect(self.load_home_layer)
		form.pushButton_9.clicked.connect(self.load_work_layer)
		form.pushButton_lff.clicked.connect(self.load_prob)
		form.pushButton_lff_2.clicked.connect(self.load_prob_weekend)
		self.track_file_load.clicked.connect(self.points_to_distribution)
		form.pushButton_10.clicked.connect(self.randomize_home_work)
		form.pushButton_12.clicked.connect(self.load_census_file)
		form.pushButton_13.clicked.connect(self.statistical)
		form.pushButton_14.clicked.connect(self.prob_per_time)
		#Home Loc
		form.pushButton.clicked.connect(self.select_localization_home)
		#Work Loc
		form.pushButton_2.clicked.connect(self.select_localization_work)
		#Generate
		form.pushButton_3.clicked.connect(self.generate)
		#TEMP
		form.Temp_button.clicked.connect(self.generate_from_positions)
		form.Temp_button_2.clicked.connect(self.where2)
		#exec
		self.okno.show()
		
	def set_file_CDR(self,form):
		self.fname = QFileDialog.getOpenFileName(self.okno,"Open File","C:",'*.csv')
		if QFileDialog.accepted:
			file = open(self.fname,'r')
			cdrlist = []
			for line in file:
   				cdrlist.append(line.split(';'))
   		  	del cdrlist[0]
   		   	cust_ind = []
   		
   			for num in cdrlist:
   			 	if num[0] in cust_ind:
   			 		pass
   			  	else:
   			  		cust_ind.append(num[0])
   			  		self.cdr_list.addItem(num[0])
   		   	file.close()
   	
   	def load_layer(self):
   		fname = QFileDialog.getOpenFileName(self.okno,"Open File","C:",'*.shp')
   		self.grid = iface.addVectorLayer(fname,"grid","ogr")
   		crs=QgsCoordinateReferenceSystem("epsg:4326")
   		self.grid.setCrs(crs)
   		self.track_file_load.setEnabled(True)
   		self.home_loc.setEnabled(True)
		self.work_loc.setEnabled(True)
		if self.grid.wkbType()==QGis.WKBPolygon:
			result = "Temp\grid_centroid.shp"
			processing.runalg('qgis:polygoncentroids', self.grid, result)
			QgsMapLayerRegistry.instance().removeMapLayer(self.grid.id())
			self.grid = iface.addVectorLayer(result,"grid","ogr")
			
	def load_layer2(self):
   		fname = QFileDialog.getOpenFileName(self.okno,"Open File","C:",'*.shp')
   		self.polygon_layer= iface.addVectorLayer(fname,"grid","ogr")
   		crs=QgsCoordinateReferenceSystem("epsg:4326")
   		self.polygon_layer.setCrs(crs)
   		self.track_file_load.setEnabled(True)
   		self.home_loc.setEnabled(True)
		self.work_loc.setEnabled(True)
		
	def load_home_layer(self):
   		fname = QFileDialog.getOpenFileName(self.okno,"Open File","C:",'*.shp')
   		self.home_drop_layer = iface.addVectorLayer(fname,"grid","ogr")
   		crs=QgsCoordinateReferenceSystem("epsg:4326")
   		self.home_drop_layer.setCrs(crs)
   		self.home_layer.setText(str(fname))
   		if self.home_drop_layer.wkbType()==QGis.WKBPolygon:
			result = "Temp\home_drop_layer_centroid.shp"
			#processing.runalg('saga:polygoncentroids', self.home_drop_layer, True, result)
			processing.runalg('qgis:polygoncentroids', self.home_drop_layer, result)
			QgsMapLayerRegistry.instance().removeMapLayer(self.home_drop_layer.id())
			self.home_drop_layer = iface.addVectorLayer(result,"home_drop_layer","ogr")
   		
   	def load_work_layer(self):
   		fname = QFileDialog.getOpenFileName(self.okno,"Open File","C:",'*.shp')
   		self.work_drop_layer = iface.addVectorLayer(fname,"grid","ogr")
   		crs=QgsCoordinateReferenceSystem("epsg:4326")
   		self.work_drop_layer.setCrs(crs)
   		self.work_layer.setText(str(fname))
   		if self.work_drop_layer.wkbType()==QGis.WKBPolygon:
			result = "Temp\work_drop_layer_centroid.shp"
			processing.runalg('qgis:polygoncentroids', self.work_drop_layer, result)
			QgsMapLayerRegistry.instance().removeMapLayer(self.work_drop_layer.id())
			self.work_drop_layer = iface.addVectorLayer(result,"work_drop_layer","ogr")

   		
   	def select_localization_home(self):
   		canvas = iface.mapCanvas()
   		canvas.refresh()
   		iface.actionSelect().trigger()
   		self.okno.hide()
   		layer = iface.activeLayer()
   		layer.selectionChanged.connect(self.read_coordinates_home)
   		  		
	def read_coordinates_home(self,text_edit):
		layer = iface.activeLayer()
   	 	feature = layer.selectedFeatures()
   		geom = feature[0].geometry()
   		if geom.type() == QGis.Point:
   			point = geom.asPoint()
   			x = point.x()
   			y = point.y() 
   		  	self.home_coor.setText(str(point))
   		self.okno.show()
   		layer.selectionChanged.disconnect(self.read_coordinates_home)
   	
   	def select_localization_work(self):
   		canvas = iface.mapCanvas()
   		canvas.refresh()
   		iface.actionSelect().trigger()
   		self.okno.hide()
   		layer = iface.activeLayer()
   		layer.selectionChanged.connect(self.read_coordinates_work)
   		  		
	def read_coordinates_work(self,text_edit):
		layer = iface.activeLayer()
   	 	feature = layer.selectedFeatures()
   		geom = feature[0].geometry()
   		if geom.type() == QGis.Point:
   			point = geom.asPoint()
   			x = point.x()
   			y = point.y() 
   		  	self.work_coor.setText(str(point))
   		self.okno.show()
   	 	layer.selectionChanged.disconnect(self.read_coordinates_work)
   	 	
   	def points_to_denisty(self,layer,result_path,distance=False):
   		processing.runalg('qgis:countpointsinpolygon', self.polygon_layer, layer,"NUMPOINTS", result_path)
   		counter = iface.addVectorLayer(result_path,"counter","ogr")
   		
   		#Field calculator
   		expression_density = QgsExpression(""""NUMPOINTS"/$area""")
   			
   		counter.startEditing()
   		pr = counter.dataProvider()
   		pr.addAttributes([QgsField("Density", QVariant.Double), QgsField("Prob", QVariant.Double)])
   		counter.updateFields()
   		index = counter.fieldNameIndex("Density")
   		expression_density.prepare(counter.pendingFields())
   			
   		for feature in counter.getFeatures():
   			value = expression_density.evaluate(feature)
   			counter.changeAttributeValue(feature.id(),index,value)
   		
   		density_sum = 0
   		for feature in counter.getFeatures():
   			density_sum += feature['Density']
   			
   		index = counter.fieldNameIndex("Prob")
   		for feature in counter.getFeatures():
   			value = feature["Density"]/density_sum
   			feature["Prob"] = value
   			counter.changeAttributeValue(feature.id(),index,value)
   			counter.updateFeature(feature)
   		counter.commitChanges()
   		counter.updateFields()
   		
   		_writer = QgsVectorFileWriter.writeAsVectorFormat(counter,result_path,"utf-8",wgs,"ESRI Shapefile")
   			
   		prob_layer = iface.addVectorLayer(result_path,"prob_layer","ogr")
   		QgsMapLayerRegistry.instance().removeMapLayer(counter.id())
   	
   	def generate_from_positions(self):
		start = time.time()
   		layer = iface.activeLayer()
   		#Homefile
   		homefile = open("Temp\home_locations.csv",'r')
   		#Workfile
   		workfile = open("Temp\work_locations.csv",'r')
   		#Source
   		file = open(self.fname,'r')
   		cdrlist = []
   		file.next()
		for line in file:
	   		if line.split(';')[0] == self.cdr_list.selectedItems()[0].text(): #if id equals to selected user
	   			cdrlist.append(line.split(';'))
   		#New file writing
	   	file_write = open(self.fname[0:len(self.fname)-4]+'_id'+str(self.cdr_list.selectedItems()[0].text())+'_positions_'+
								os.path.basename(self.prob_file),'wb')
	   	self.deleteContent(file_write)
	   	with open(self.fname,'rb') as f:
	   			file_write.write(f.readline().replace(';',','))
   		for i in range(100):
	   		#Home Loc
	   		home_point = homefile.next().split(',')
		   	home_x = float(home_point[0][0::])
			home_y = float(home_point[1][0::])
	   		home = QgsPoint(home_x,home_y)
	   		#Work Loc
	   		work_point = workfile.next().split(',')
	   		work_x = float(work_point[0][0::])
	   		
	   		work_y = float(work_point[1][0::])
	   		work = QgsPoint(work_x,work_y)			
	   	 	#Assigning positions in time
		   	round_up = 60*(24.0/self.time_resolution)*60
	   		position_to_indexes = []
		   	for num in range(len(cdrlist)):
		   		day = int(cdrlist[num][14].split(' ')[0].split('/')[2])
	   	   		month = int(cdrlist[num][14].split(' ')[0].split('/')[1])
	   	   		year = int(cdrlist[num][14].split(' ')[0].split('/')[0])
		   		hour = int(cdrlist[num][14].split(' ')[1].split(':')[0]) 
		   		minute = int(cdrlist[num][14].split(' ')[1].split(':')[1])
	   	   		cdr_datetime = datetime.datetime(year,month,day,hour,minute)
	   	   		if self.checkBox.isChecked() and (cdr_datetime.isoweekday() == 6 or cdr_datetime.isoweekday() == 7) :
	   	   			position_to_indexes.append([num,self.randomSelectWeekend(self.roundTime(cdr_datetime,round_up)),
													self.roundTime(cdr_datetime,round_up)])
	   	   		else:
	   	   			position_to_indexes.append([num,self.randomSelect(self.roundTime(cdr_datetime,round_up)),
													self.roundTime(cdr_datetime,round_up)])
	   	   			
		   	#Positions to coordinates
		   	point_time = []
		   	geom_buffer = self.create_ellipse(home,work,self.spread_rate.value())
		   	mem_layer = QgsVectorLayer("Polygon","Buffer","memory")
		   	pr = mem_layer.dataProvider()
		   	pr.createSpatialIndex()
		   	buffer = QgsFeature(1)
		   	buffer.setGeometry(geom_buffer)
		   	pr.addFeatures([buffer])
			
		   	points_within = [feat.geometry().asPoint() for feat in layer.getFeatures() 
				if feat.geometry().intersects(geom_buffer)]
				
		   	for num in range(len(position_to_indexes)):
		   		if position_to_indexes[num][1] == 0:
		   			point_time.append(home)
		   		elif position_to_indexes[num][1] == 1:
		   			point_time.append(work)
		   		else:
		   			try:
		   				point_time.append(random.choice(points_within))
		   			except:
		   				continue
	   		
	   		for num in range(len(point_time)):
	   			point_time[num] = str(point_time[num]).split(',')
	   		 	point_time[num][0]=float(point_time[num][0].replace('(',''))
	   		 	point_time[num][1]=float(point_time[num][1].replace(')',''))
	   		 	for elem_num in range(len(cdrlist[num])):
	   		 		try:
	   		 	 		if cdrlist[num][elem_num].isdigit():
	   		 		  		cdrlist[num][elem_num] = float(cdrlist[num][elem_num])
	   		 		except:
	   		 			pass
	   			file_write.write(str([i]+cdrlist[num][1:len(cdrlist[0])-2]+
								point_time[num]).replace(']','')+'\n')

	   		iface.messageBar().clearWidgets()
	   		#QgsMapLayerRegistry.instance().removeMapLayer(centroid_layer.id())
	   	file.close()
   		file_write.close()
		end = time.time()
		QgsMessageLog.logMessage(str(end-start))
   	
   	def where2(self):
		start = time.time()
   		layer = iface.activeLayer()
   		#Homefile
   		homefile = open("\Temp\home_locations.csv",'r')
   		#Workfile
   		workfile = open("\Temp\work_locations.csv",'r')
   		#Source
   		file = open(self.fname,'r')
   		cdrlist = []
   		file.next()
		for line in file:
	   		if line.split(';')[0] == self.cdr_list.selectedItems()[0].text(): #if id equals to selected user
	   			cdrlist.append(line.split(';'))
   		#New file writing
	   	file_write = open(self.fname[0:len(self.fname)-4]+'_id'+str(self.cdr_list.selectedItems()[0].text())+'_where2.csv','wb')
	   	self.deleteContent(file_write)
	   	with open(self.fname,'rb') as f:
	   			file_write.write(f.readline().replace(';',','))
   		for i in range(100):
	   		#Home Loc
	   		home_point = homefile.next().split(',')
		   	home_x = float(home_point[0][0::])
			home_y = float(home_point[1][0::])
	   		home = QgsPoint(home_x,home_y)
	   		#Work Loc
	   		work_point = workfile.next().split(',')
	   		work_x = float(work_point[0][0::])
	   		work_y = float(work_point[1][0::])
	   		work = QgsPoint(work_x,work_y)			
	   	 	#Assigning positions in time
		   	round_up = 60*(24.0/self.time_resolution)*60
	   		position_to_indexes = []
	   		point_time = []
		   	for num in range(len(cdrlist)):
		   		day = int(cdrlist[num][14].split(' ')[0].split('/')[2])
	   	   		month = int(cdrlist[num][14].split(' ')[0].split('/')[1])
	   	   		year = int(cdrlist[num][14].split(' ')[0].split('/')[0])
		   		hour = int(cdrlist[num][14].split(' ')[1].split(':')[0]) 
		   		minute = int(cdrlist[num][14].split(' ')[1].split(':')[1])
	   	   		cdr_datetime = datetime.datetime(year,month,day,hour,minute)
	   	   		hourly = self.roundTime(cdr_datetime,3600).hour
	   	   		file_path = """\\Temp\\accen"""+str(hourly)+"""prob.csv"""
		   	   	probability = [0,0]
	   	   		with open(file_path,'rb') as prob:
	   	   			prob.next()
	   	   			for line in prob:
	   	   				line = line.split(',')
	   	   				coors = (round(float(line[::-1][3]),4),round(float(line[::-1][2]),4))
	   	   				if coors == (home_x,home_y):
	   	   					probability[0] = (float(line[::-1][4]))
	   	   				elif coors == (work_x,work_y):
	   	   					probability[1] = (float(line[::-1][4]))
	   	   		probability = self.normalize(probability)
	   	   		ind = np.random.choice([0,1],p=probability)
	   	   		if ind == 0:
	   	   			point_time.append(home)
	   	   		elif ind == 1:
	   	   			point_time.append(work)
	   		
	   		for num in range(len(point_time)):
	   			point_time[num] = str(point_time[num]).split(',')
	   		 	point_time[num][0]=float(point_time[num][0].replace('(',''))
	   		 	point_time[num][1]=float(point_time[num][1].replace(')',''))
	   		 	for elem_num in range(len(cdrlist[num])):
	   		 		try:
	   		 	 		if cdrlist[num][elem_num].isdigit():
	   		 		  		cdrlist[num][elem_num] = float(cdrlist[num][elem_num])
	   		 		except:
	   		 			pass
	   			file_write.write(str([i]+cdrlist[num][1:len(cdrlist[0])-2]+
								point_time[num]).replace(']','')+'\n')

	   		iface.messageBar().clearWidgets()
	   		#QgsMapLayerRegistry.instance().removeMapLayer(centroid_layer.id())
	   	file.close()
   		file_write.close()
		end = time.time()
		QgsMessageLog.logMessage(str(end-start))
   			
   	def generate(self): #Main
   		layer = iface.activeLayer()
   		#Home Loc
   		home_gen = self.home_coor.toPlainText()
   		home_point = (home_gen.split(','))
   		home_x = float(home_point[0][1:len(home_point[0])])
   		home_y = float(home_point[1][0:len(home_point[1])-1])
   		home = QgsPoint(home_x,home_y)
   		#Work Loc
   		work_gen = self.work_coor.toPlainText()
   		work_point = (work_gen.split(','))
   		work_x = float(work_point[0][1:len(work_point[0])])
   		work_y = float(work_point[1][0:len(work_point[1])-1])
   		work = QgsPoint(work_x,work_y)
   		#Open original file
   		file = open(self.fname,'r')
		cdrlist = []
		for line in file:
			if line.split(';')[0] == self.cdr_list.selectedItems()[0].text(): #if id equals to selected user
   				cdrlist.append(line.split(';'))
	   	#Assigning positions in time
	   	round_up = 60*(24.0/self.time_resolution)*60
	   	#QgsMessageLog.logMessage(str(round_up))
	   	position_to_indexes = []
	   	for num in range(len(cdrlist)):
	   		#QgsMessageLog.logMessage(str(cdrlist[num][14]))
	   		day = int(cdrlist[num][14].split(' ')[0].split('/')[2])
   	   		month = int(cdrlist[num][14].split(' ')[0].split('/')[1])
   	   		year = int(cdrlist[num][14].split(' ')[0].split('/')[0])
	   		hour = int(cdrlist[num][14].split(' ')[1].split(':')[0]) 
	   		minute = int(cdrlist[num][14].split(' ')[1].split(':')[1])
   	   		cdr_datetime = datetime.datetime(year,month,day,hour,minute)
   	   		if self.checkBox.isChecked() and (cdr_datetime.isoweekday() == 6 or cdr_datetime.isoweekday() == 7) :
   	   			position_to_indexes.append([num,self.randomSelectWeekend(self.roundTime(cdr_datetime,round_up))])
   	   		else:
   	   			position_to_indexes.append([num,self.randomSelect(self.roundTime(cdr_datetime,round_up))])
	   	#Positions to coordinates
	   	point_time = []
	   	geom_buffer = self.create_ellipse(home,work,self.spread_rate.value())
	   	mem_layer = QgsVectorLayer("Polygon","Buffer","memory")
	   	pr = mem_layer.dataProvider()
	   	pr.createSpatialIndex()
	   	buffer = QgsFeature(1)
	   	buffer.setGeometry(geom_buffer)
	   	pr.addFeatures([buffer])
	   	QgsMapLayerRegistry.instance().addMapLayer(mem_layer)
	   	points_within = [feat.geometry().asPoint() for feat in layer.getFeatures() 
			if feat.geometry().intersects(geom_buffer)]
	   	for num in range(len(position_to_indexes)):
	   		if position_to_indexes[num][1] == 0:
	   			point_time.append(home)
	   		elif position_to_indexes[num][1] == 1:
	   			point_time.append(work)
	   		else:
	   			point_time.append(random.choice(points_within))
	   			#QgsMessageLog.logMessage(str(points_within))
	   			#QgsMessageLog.logMessage(str(geom_home.asPoint()))
   		#New file writing
   		if self.checkBox.isChecked():
   			file_write = open(self.fname[0:len(self.fname)-4]+'_id'+str(self.cdr_list.selectedItems()[0].text())+'_positions_weekend_'+
							os.path.basename(self.prob_file),'wb')
   		else:
   			file_write = open(self.fname[0:len(self.fname)-4]+'_id'+str(self.cdr_list.selectedItems()[0].text())+'_positions_'+
							os.path.basename(self.prob_file),'wb')
   		self.deleteContent(file_write)
   		with open(self.fname,'rb') as f:
   			file_write.write(f.readline().replace(';',','))
   		for num in range(len(point_time)):
   			point_time[num] = str(point_time[num]).split(',')
   		 	point_time[num][0]=float(point_time[num][0].replace('(',''))
   		 	point_time[num][1]=float(point_time[num][1].replace(')',''))
   		 	for elem_num in range(len(cdrlist[num])):
   		 	 	if cdrlist[num][elem_num].isdigit():
   		 		  	cdrlist[num][elem_num] = float(cdrlist[num][elem_num])
   			file_write.write(str(cdrlist[num][0:len(cdrlist[0])-2]+
							point_time[num])[1:len(str(cdrlist[num][0:len(cdrlist[0])-2]+point_time[num]))-1]+'\n')
   		file_write.close()
   		file.close()
	   	
	def deleteContent(self,pfile):
		pfile.seek(0)
		pfile.truncate()
		
	def randomSelect(self,hour):
		time_slot = (hour.hour)*(self.time_denominator) + (hour.minute/((24.0/self.time_resolution)*60))
		home_rand = random.random() * float(self.home.item(time_slot,1).text())
   		work_rand = random.random() * float(self.work.item(time_slot,1).text())
   		third_rand = random.random() * float(self.third.item(time_slot,1).text())
   		prob_list = [home_rand,work_rand,third_rand]
   		return prob_list.index(max(prob_list))
    
	def randomSelectWeekend(self,hour):
		time_slot = (hour.hour)*(self.time_denominator) + (hour.minute/((24.0/self.time_resolution)*60))
		home_rand = random.random() * float(self.home_weekend.item(time_slot,1).text())
   		work_rand = random.random() * float(self.work_weekend.item(time_slot,1).text())
   		third_rand = random.random() * float(self.third_weekend.item(time_slot,1).text())
   		prob_list = [home_rand,work_rand,third_rand]
   		return prob_list.index(max(prob_list))
   	
   	def calculateDistance(self,point1,point2,meters=False):
   		if isinstance(point1,list):
   			x_coor = float(point1[0])
   			y_coor = float(point1[1])
   		 	point1 = QgsPoint(x_coor,y_coor)
   		if isinstance(point2,list):
   			x_coor = float(point2[0])
   			y_coor = float(point2[1])
   		 	point2 = QgsPoint(x_coor,y_coor)
   		distance_object = QgsDistanceArea()
   		if meters:
   		 	distance_object.setSourceCrs(wgs)
   		  	distance_object.setEllipsoid('WGS84')
   		   	distance_object.setEllipsoidalMode(True)
   		distance = distance_object.measureLine(point1,point2)
   		return distance
   	
   	def roundTime(self,dt=None, roundTo=3600):
   		if dt == None : dt = datetime.datetime.now()
   		seconds = (dt.replace(tzinfo=None) - dt.min).seconds
   		rounding = (seconds+roundTo/2) // roundTo * roundTo
   		return dt + timedelta(0,rounding-seconds,-dt.microsecond)
   	
   	def load_prob(self,form):
   		self.prob_file = QFileDialog.getOpenFileName(self.okno,"Open File","C:",'*.csv')
   		if QFileDialog.accepted:
   			file = open(self.prob_file,'r')
   			for line in file:
   				if line.split(';')[0] == 'third test':
   					break
   				elif line.split(';')[0] == 'home':
   				 	home_prob = {}
   				 	is_reading_home_prob = True
   				 	continue
   				elif line.split(';')[0] == 'work':
   					work_prob = {}
   					is_reading_home_prob = False
   					continue
   				if is_reading_home_prob:
   					home_prob[int(line.split(';')[0])] = float(line.split(';')[1])
   				else:
   					work_prob[int(line.split(';')[0])] = float(line.split(';')[1])
   		self.time_resolution = len(home_prob)
   		self.time_denominator = (self.time_resolution/24.0)
   		#TableWidget
		self.home.setRowCount(self.time_resolution)
		self.home.setColumnCount(2)
		self.home.horizontalHeader().setStretchLastSection(True)
		self.home.setHorizontalHeaderLabels(["Hour","Value"])
		for key, value in home_prob.iteritems():
			displayed_hour = float(float(key)/(self.time_denominator))
			self.home.setItem(key, 0, QTableWidgetItem('%.1f' % displayed_hour))
			self.home.setItem(key, 1, QTableWidgetItem('%.2f' % value))
		#TableWidget_2
		self.work.setRowCount(self.time_resolution)
		self.work.setColumnCount(2)
		self.work.horizontalHeader().setStretchLastSection(True)
		self.work.setHorizontalHeaderLabels(["Hour","Value"])
		for key, value in work_prob.iteritems():
			displayed_hour = float(float(key)/(self.time_denominator))
			self.work.setItem(key, 0, QTableWidgetItem('%.1f' % displayed_hour))
			self.work.setItem(key, 1, QTableWidgetItem('%.2f' % value))
		#TableWidget_3
		self.third.setRowCount(self.time_resolution)
		self.third.setColumnCount(2)
		self.third.horizontalHeader().setStretchLastSection(True)
		self.third.setHorizontalHeaderLabels(["Hour","Value"])
		third_prob = {}
		for hour in range(self.time_resolution):
			third_prob[hour] = 1 - (work_prob[hour]+home_prob[hour])
		for key, value in third_prob.iteritems():
			displayed_hour = float(float(key)/(self.time_denominator))
			self.third.setItem(key, 0, QTableWidgetItem('%.1f' % displayed_hour))
			self.third.setItem(key, 1, QTableWidgetItem('%.2f' % value))
		#Main window comboBox index
		self.time_agg.setCurrentIndex(math.floor(self.time_denominator)-(1*(self.time_resolution/48.0)))
			
   	def load_prob_weekend(self,form):
   		self.prob_file_weekend = QFileDialog.getOpenFileName(self.okno,"Open File","C:",'*.csv')
   		if QFileDialog.accepted:
   			file = open(self.prob_file_weekend,'r')
   			for line in file:
   				if line.split(';')[0] == 'third test':
   					break
   				elif line.split(';')[0] == 'home':
   				 	home_prob_weekend = {}
   				 	is_reading_home_prob = True
   				 	continue
   				elif line.split(';')[0] == 'work':
   					work_prob_weekend = {}
   					is_reading_home_prob = False
   					continue
   				if is_reading_home_prob:
   					home_prob_weekend[int(line.split(';')[0])] = float(line.split(';')[1])
   				else:
   					work_prob_weekend[int(line.split(';')[0])] = float(line.split(';')[1])
   		self.time_resolution = len(home_prob_weekend)
   		self.time_denominator = (self.time_resolution/24.0)
   		#TableWidget
		self.home_weekend.setRowCount(self.time_resolution)
		self.home_weekend.setColumnCount(2)
		self.home_weekend.horizontalHeader().setStretchLastSection(True)
		self.home_weekend.setHorizontalHeaderLabels(["Hour","Value"])
		for key, value in home_prob_weekend.iteritems():
			displayed_hour = float(float(key)/(self.time_denominator))
			self.home_weekend.setItem(key, 0, QTableWidgetItem('%.1f' % displayed_hour))
			self.home_weekend.setItem(key, 1, QTableWidgetItem('%.2f' % value))
		#TableWidget_2
		self.work_weekend.setRowCount(self.time_resolution)
		self.work_weekend.setColumnCount(2)
		self.work_weekend.horizontalHeader().setStretchLastSection(True)
		self.work_weekend.setHorizontalHeaderLabels(["Hour","Value"])
		for key, value in work_prob_weekend.iteritems():
			displayed_hour = float(float(key)/(self.time_denominator))
			self.work_weekend.setItem(key, 0, QTableWidgetItem('%.1f' % displayed_hour))
			self.work_weekend.setItem(key, 1, QTableWidgetItem('%.2f' % value))
		#TableWidget_3
		self.third_weekend.setRowCount(self.time_resolution)
		self.third_weekend.setColumnCount(2)
		self.third_weekend.horizontalHeader().setStretchLastSection(True)
		self.third_weekend.setHorizontalHeaderLabels(["Hour","Value"])
		third_prob_weekend = {}
		for hour in range(self.time_resolution):
			third_prob_weekend[hour] = 1 - (work_prob_weekend[hour]+home_prob_weekend[hour])
		for key, value in third_prob_weekend.iteritems():
			displayed_hour = float(float(key)/(self.time_denominator))
			self.third_weekend.setItem(key, 0, QTableWidgetItem('%.1f' % displayed_hour))
			self.third_weekend.setItem(key, 1, QTableWidgetItem('%.2f' % value))
		#Main window comboBox index
		self.time_agg.setCurrentIndex(math.floor(self.time_denominator)-(1*(self.time_resolution/48.0)))

	def timeAggChanged(self):
		#QgsMessageLog.logMessage(str(self.time_agg.currentIndex()))
		if self.time_agg.currentIndex() == 0:
			self.time_resolution = 24.0
			self.time_denominator = (self.time_resolution/24.0)
		elif self.time_agg.currentIndex() == 1:
			self.time_resolution = 48.0
			self.time_denominator = (self.time_resolution/24.0)
		elif self.time_agg.currentIndex() == 2:
			self.time_resolution = 96.0
			self.time_denominator = (self.time_resolution/24.0)
		self.home_weekend.setRowCount(self.time_resolution)
		self.work_weekend.setRowCount(self.time_resolution)
		self.third_weekend.setRowCount(self.time_resolution)
		self.home.setRowCount(self.time_resolution)
		self.work.setRowCount(self.time_resolution)
		self.third.setRowCount(self.time_resolution)
	
	def azimuth(self,home_point,work_point):
		azimuth = math.atan2(work_point.y()-home_point.y(),work_point.x()-home_point.x())
		return azimuth
	
	def create_ellipse(self,home_point,work_point,long_to_short=1):
		try:
   			home_point.geom()
   		except:
   			home_point = QgsPoint(float(home_point[0]),float(home_point[1]))
			work_point = QgsPoint(float(work_point[0]),float(work_point[1]))
   		a = self.calculateDistance(home_point,work_point)
   		#QgsMessageLog.logMessage(str(long_to_short))
   		b = a*float(long_to_short)
   		azi = self.azimuth(home_point,work_point)
   		pol = []
   		for t in range(0,201):
		   	x = home_point.x() + (a*math.cos(t*ro)*math.cos(azi)-b*math.sin(t*ro)*math.sin(azi))
			y = home_point.y() + (b*math.sin(t*ro)*math.cos(azi)+a*math.cos(t*ro)*math.sin(azi))
			pol.append(QgsPoint(x,y))
		activity_space = QgsGeometry.fromPolygon([pol])
		return activity_space
	
	def points_to_distribution(self):
		file = open("""C:""",'r')
		reader = csv.reader(file,delimiter=',',quotechar="'")
		head = reader.next()
		limiter = 0
		cust_index = '0'
		cdr_user_positions_work = []
		cdr_user_positions_home = []
		cdr_all_work = []
		cdr_all_home = []
		cdr_all_distance = []
		cdr_user_all = []
		spreads = []
		home_time_agg = {}
		work_time_agg = {}
		other_time_agg = {}
		for time in range(int(self.time_resolution)):
			key = time/self.time_denominator
			home_time_agg[key] = []
			work_time_agg[key] = []
			other_time_agg[key] = []
		
		for line in reader:    
		    try:
		        float(line[1])
		    except:
		    	QgsMessageLog.logMessage("Error 103")
		        continue
		    
		    try:
		        float(line[30])
		    except:
		    	QgsMessageLog.logMessage("Error 104")
		        continue
		    
		    #datetime
		    cust_index_old = cust_index
		    cust_index = line[0].replace('[','') #file has '[' before id

		    #QgsMessageLog.logMessage(str(cust_index))
		    if cust_index_old != cust_index:
		        #Home Work localizations per one user
		        work_place = self.most_common(cdr_user_positions_work)
		        home_place = self.most_common(cdr_user_positions_home)
		        cdr_all_work.append(work_place)
		        cdr_all_home.append(home_place)
		        long_axis = self.calculateDistance(work_place,home_place,
															meters=True)
		        cdr_all_distance.append(long_axis)
		        #Prob calculations
		        round_up = 60*(24.0/self.time_resolution)*60
		        per_time_agg = {}
		        for time in range(int(self.time_resolution)):
		        	per_time_agg[time/(self.time_resolution/24)] = [0,0,0]
		        for num in range(2):
		        	home_place[num] = float(home_place[num])
		        	work_place[num] = float(work_place[num])
		        for position in cdr_user_all:
		        	position[2] = self.roundTime(position[2],round_up)
		        	position[2] = position[2].hour+(position[2].minute/60.0)
		        	if home_place == position[:2]:
		        		per_time_agg[position[2]][0] += 1
		        	elif work_place == position[:2]:
		        		per_time_agg[position[2]][1] += 1
		        	else:
		        		per_time_agg[position[2]][2] += 1
		        for hours in per_time_agg:
		        	per_time_agg[hours] = self.normalize(per_time_agg[hours])
		        	home_time_agg[hours].append(per_time_agg[hours][0])	
		        	work_time_agg[hours].append(per_time_agg[hours][1])
		        	other_time_agg[hours].append(per_time_agg[hours][2])
		        
		        #Slow - requires refinement
		        x = np.transpose(np.array(cdr_user_all)[:,0])
		        y = np.transpose(np.array(cdr_user_all)[:,1])
		        all_points = []
		        for poix, poiy in zip(x,y):
		        	all_points.append(QgsPoint(poix,poiy))
		        spread = 0.01
		        all_points = set(all_points)
		        all_geometry = []
		        for element in all_points:
		        	all_geometry.append(QgsGeometry.fromPoint(element))
		        try:
			        while True:
			        	ellipse_geom = self.create_ellipse(home_place, work_place, spread)
			        	points_within = [feat for feat in all_geometry 
				if feat.intersects(ellipse_geom)]
			        	if len(points_within) == len(all_points):
			        		break
			        	else:
			        		spread += 0.01
			    
		        spreads.append(spread)
		        
		        #Clearing lists
		        cdr_user_positions_work = []
		        cdr_user_positions_home = []
		        cdr_user_all = []
		        cust_index_old = line[0]
		        continue
		    call_date = line[14].replace("'","").lstrip()
		    
		    year = int(call_date.split(' ')[0].split('/')[0])
		    month = int(call_date.split(' ')[0].split('/')[1])
		    day = int(call_date.split(' ')[0].split('/')[2])
		    hour = int(call_date.split(' ')[1].split(':')[0])
		    minute = int(call_date.split(' ')[1].split(':')[1])
		    second = int(call_date.split(' ')[1].split(':')[2])
		    call_datetime = datetime.datetime(year,month,day,hour,minute,second)
		    
		    line[30] = line[30].replace("'","").lstrip()
		    line[31] = line[31].replace("'","").lstrip()
		    
		    cdr_user_all.append([float(line[30]),float(line[31]),call_datetime])
			
		    #add to list
		    if call_datetime.time() > datetime.time(10) and \
		    call_datetime.time() < datetime.time(14): 
		        cdr_user_positions_work.append([line[30],line[31]])
		    elif call_datetime.time() > datetime.time(2) and \
		    call_datetime.time() < datetime.time(6):
		        cdr_user_positions_home.append([line[30],line[31]])
			
			
		    limiter += 1
		
		mean_spread = np.mean(np.array(spreads))
		QgsMessageLog.logMessage(str(mean_spread))
		#mean_probs_calc
		for hour in range(len(home_time_agg)):
			hour = hour/(self.time_denominator)
			home_time_agg[hour] = np.array(home_time_agg[hour]).mean()
			work_time_agg[hour] = np.array(work_time_agg[hour]).mean()
			other_time_agg[hour] = np.array(other_time_agg[hour]).mean()
			norm_list = self.normalize([home_time_agg[hour],work_time_agg[hour],other_time_agg[hour]])
			home_time_agg[hour] = norm_list[0]
			work_time_agg[hour] = norm_list[1]
			other_time_agg[hour] = norm_list[2]
		result_home = "Temp\home_points.shp"
		result_work = "Temp\work_points.shp"
		result_prob = "Temp\prob_dist.csv"
		self.write_prob(home_time_agg,work_time_agg,other_time_agg,result_prob) 
		self.set_of_point_to_layer(result_home,cdr_all_home,cdr_all_distance)
		self.set_of_point_to_layer(result_work, cdr_all_work)
		
		iface.addVectorLayer(result_home,"home","ogr")
		iface.addVectorLayer(result_work,"work","ogr")
		self.points_to_denisty(result_home, "Temp\prob_home.shp",distance=True)
		self.points_to_denisty(result_work, "Temp\prob_work.shp")
		
		iface.messageBar().clearWidgets()
		
	def set_of_point_to_layer(self,result,pointset,distance = None):
		"""pointset and distance has to be rowwise"""
		mem_layer = QgsVectorLayer("Point","mem_layer","memory")
		mem_layer.startEditing()
		pr = mem_layer.dataProvider()
		pr.createSpatialIndex()
		if distance:
			pr.addAttributes([QgsField("Distance", QVariant.Double)])
		else:
			pass
		mem_layer.updateFields()
	   	mem_layer_features = []
	   	if distance:
		   	for element in zip(pointset,distance):
		   		fet = QgsFeature()
		   		x_coor = float(element[0][0])
		   		y_coor = float(element[0][1])
		   		fet.setGeometry(QgsGeometry.fromPoint(QgsPoint(x_coor,y_coor)))
		   		fet.setAttributes([element[1]])
		   		mem_layer_features.append(fet)
		else:
			for element in pointset:
				fet = QgsFeature()
				x_coor = float(element[0])
				y_coor = float(element[1])
				fet.setGeometry(QgsGeometry.fromPoint(QgsPoint(x_coor,y_coor)))
				mem_layer_features.append(fet)
				mem_layer.updateFeature(fet)
   		mem_layer.commitChanges()
   		mem_layer.updateFields()
				
		pr.addFeatures(mem_layer_features)
   		crs=QgsCoordinateReferenceSystem("epsg:4326")
		QgsVectorFileWriter.writeAsVectorFormat(mem_layer, result ,"UTF-8", crs , "ESRI Shapefile")
		QgsMapLayerRegistry.instance().removeMapLayer(mem_layer.id())
		
	def density_from_point_layer(self,point_layer):
	   		#Field calculator
   			expression_density = QgsExpression(""""Works"/$area""")
   			
   			#PickupsDensity/Prob
   			census_wgsps.startEditing()
   			pr = census_wgsps.dataProvider().addAttributes([QgsField("DensityW", QVariant.Double), QgsField("ProbW", QVariant.Double)])
   			census_wgsps.updateFields()
   			index = census_wgsps.fieldNameIndex("DensityW")
   			expression_density.prepare(census_wgsps.pendingFields())
   			for feature in census_wgsps.getFeatures():
   				value = expression_density.evaluate(feature)
   				census_wgsps.changeAttributeValue(feature.id(),index,value)
   				
   			density_sum = 0
   			for feature in census_wgsps.getFeatures():
   				density_sum += feature['DensityW']

   			index = census_wgsps.fieldNameIndex("ProbW")
   			for feature in census_wgsps.getFeatures():
   				value = feature["DensityW"]/density_sum
   				feature["ProbW"] = value
   				census_wgsps.updateFeature(feature)
   			census_wgsps.commitChanges()
   			
   			_writer = QgsVectorFileWriter.writeAsVectorFormat(census_wgsps,"Temp\census_file.shp","utf-8",wgs,"ESRI Shapefile")
   			
   			census_prob = iface.addVectorLayer("Temp\census_file.shp","census_prob","ogr")
		
	def randomize_home_work(self):
		self.home_drop_layer.setCrs(wgs)
		self.work_drop_layer.setCrs(wgs)
		QgsVectorFileWriter.writeAsVectorFormat(self.home_drop_layer,"Temp\home_drop_wgsps.shp","utf-8",wgsps,"ESRI Shapefile")
		QgsVectorFileWriter.writeAsVectorFormat(self.work_drop_layer,"Temp\work_drop_wgsps.shp","utf-8",wgsps,"ESRI Shapefile")

		if iface.mapCanvas().mapRenderer().hasCrsTransformEnabled():
			self.iface.mapCanvas().mapRenderer().setDestinationCrs(wgsps)
		
		#Computation time profiler
   		#cProfile.runctx('self.find_home_work(10000,True)',globals(),locals(),"stats")
   		#stream = open('E:\stat10thousand.txt', 'w');
   		#stats = pstats.Stats('stats', stream=stream)
   		#stats.print_stats()
   		
   		self.find_home_work(4900,True)
   		
   		if iface.mapCanvas().mapRenderer().hasCrsTransformEnabled():
			self.iface.mapCanvas().mapRenderer().setDestinationCrs(wgs)
			
   		extent = self.home_drop_layer.extent()
   		iface.mapCanvas().setExtent(extent)
		
	def degree_buffer(self,distance,origin):
		new_distance = distance
		
		geom_buffer = origin.buffer(new_distance*1.1,-1)
		mem_layer = QgsVectorLayer("Polygon","Buffer","memory")
	   	pr = mem_layer.dataProvider()
	   	pr.createSpatialIndex()
	   	buffer = QgsFeature(1)
	   	buffer.setGeometry(geom_buffer)
	   	pr.addFeatures([buffer])
	   	mem_layer.setCrs(wgsps)
	   	QgsVectorFileWriter.writeAsVectorFormat(mem_layer,"Temp\\buffer1.shp","UTF-8", wgsps,"ESRI Shapefile")
	   	
	   	geom_buffer = origin.buffer(new_distance*0.9,-1)
	   	mem_layer2 = QgsVectorLayer("Polygon","Buffer","memory")
	   	pr2 = mem_layer2.dataProvider()
	   	pr2.createSpatialIndex()
	   	buffer = QgsFeature(1)
	   	buffer.setGeometry(geom_buffer)
	   	pr2.addFeatures([buffer])
	   	mem_layer2.setCrs(wgsps)
	   	QgsVectorFileWriter.writeAsVectorFormat(mem_layer2,"Temp\\buffer2.shp","utf-8", wgsps,"ESRI Shapefile")
	   	
	   	#buffer1 = QgsVectorLayer("Temp\\buffer1.shp","buffer1","ogr")
	   	buffer1 = iface.addVectorLayer("Temp\\buffer1.shp","buffer1","ogr")
	   	iface.messageBar().clearWidgets()
	   	buffer2 = iface.addVectorLayer("Temp\\buffer2.shp","buffer2","ogr")
	   	iface.messageBar().clearWidgets()
	   	#buffer2 = QgsVectorLayer("Temp\\buffer2.shp","buffer2","ogr")
	   	
	   	result = "Temp\\buffer_fin.shp"
		processing.runalg('qgis:difference', buffer1, buffer2, "Temp\\buffer_fin.shp",progress = None)
		#buffer_fin = iface.addVectorLayer(result,"buffer_fin","ogr")
		#feature = buffer_fin.getFeatures().next()
		#geom_buffer = feature.geometry()
		
		try:
			QgsMapLayerRegistry.instance().removeMapLayer(buffer1.id())
		except:
			QgsMessageLog.logMessage("Error 102")
		
		try:
			QgsMapLayerRegistry.instance().removeMapLayer(buffer2.id())
		except:
			QgsMessageLog.logMessage("Error 102")
		
		#QgsMapLayerRegistry.instance().removeMapLayer(buffer_fin.id())
		
		#return geom_buffer
		return None
		
	def find_home_work(self,iterations=1,write_csv_file=False):
		home_drop_wgsps = iface.addVectorLayer("Temp\home_drop_wgsps.shp","home_drop_distance","ogr")
		iface.messageBar().clearWidgets()
		work_drop_wgsps = iface.addVectorLayer("Temp\work_drop_wgsps.shp","work_drop_distance","ogr")
		iface.messageBar().clearWidgets()
		if write_csv_file==True:
			file_write_home = open("Temp\home_locations.csv",'wb')
   			file_write_work = open("Temp\work_locations.csv",'wb')
   		  	self.deleteContent(file_write_home)
   		  	self.deleteContent(file_write_work)
   		  	
		for iter in range(iterations):
			#Search for home
			randomize_id = []
			randomize_prob = []
			coordinate_dict = {}
			distance_dict = {}
			for feature in home_drop_wgsps.getFeatures():
				geom = feature.geometry()
	   			if geom.type() == QGis.Point:
	   			 	point = geom.asPoint()
	   			randomize_id.append(feature.id())
	   			randomize_prob.append(float(feature["Prob"]))
				coordinate_dict[feature.id()] = point
				distance_dict[feature.id()] = float(feature["pops_censu"])
			max_key = np.random.choice(randomize_id, p = randomize_prob)
			home_coordinates = coordinate_dict[max_key]
			distance = distance_dict[max_key]
			#Set home coordinates
			req = QgsFeatureRequest()
			req.setFilterFids([max_key])
			for feature in self.home_drop_layer.getFeatures(req):
				home_coordinates_wgs = feature.geometry().asPoint()
			self.home_coor2.setText(str(home_coordinates_wgs))
			self.home_coor.setText(str(home_coordinates_wgs))
			#Search for possible workplace
			#Transformation
			geom_home = QgsGeometry.fromPoint(home_coordinates)
			self.degree_buffer(distance, geom_home)
		   	buffer_fin = iface.addVectorLayer("Temp\\buffer_fin.shp","buffer_fin","ogr")
		   	iface.messageBar().clearWidgets()
		   	try:
		   		feature = buffer_fin.getFeatures().next()
				geom_buffer = feature.geometry()
				points_within = [feat for feat in work_drop_wgsps.getFeatures() if feat.geometry().intersects(geom_buffer)]
				QgsMapLayerRegistry.instance().removeMapLayer(buffer_fin.id())
			except:
				QgsMessageLog.logMessage("Error 101")
			

		   	#Normalize prob inside work
		   	randomize_prob = []
   			for feature in points_within:
   			 	randomize_prob.append(np.float64(feature["Prob"]))
   			
   			sum_randomize_prob = sum(randomize_prob)
   			for num in range(len(randomize_prob)):
   				randomize_prob[num] = np.float64(randomize_prob[num]/sum_randomize_prob)
   			
		   	#Search for work
		   	randomize_id = []
		   	for feature in points_within:
		   		geom = feature.geometry()
		   		if geom.type() == QGis.Point:
		   			point = geom.asPoint()
		   		randomize_id.append(feature.id())
		   	
		   	try:
				max_key = np.random.choice(randomize_id, p = randomize_prob)
			except:
				QgsMessageLog.logMessage("Probabilities do not sum to 1, skipped iteration")
				continue
			
			#Set work coordinates
			req = QgsFeatureRequest()
			req.setFilterFids([max_key])
			for feature in self.work_drop_layer.getFeatures(req):
				work_coordinates_wgs = feature.geometry().asPoint()
			self.work_coor2.setText(str(work_coordinates_wgs))
			self.work_coor.setText(str(work_coordinates_wgs))
			if write_csv_file==True:
				#New file writing
   			   	file_write_home.write(str(home_coordinates_wgs)[1:len(str(home_coordinates_wgs))-1]+'\n')
   			   	file_write_work.write(str(work_coordinates_wgs)[1:len(str(work_coordinates_wgs))-1]+'\n')
   			QgsMapLayerRegistry.instance().clearAllLayerCaches()
		QgsMapLayerRegistry.instance().removeMapLayer(work_drop_wgsps.id())
   		QgsMapLayerRegistry.instance().removeMapLayer(home_drop_wgsps.id())
   		file_write_home.close()
   		file_write_work.close()
   		
   	def load_census_file(self):
   		fname = QFileDialog.getOpenFileName(self.okno,"Open File","C:",'*.shp')
   		if QFileDialog.accepted:
	   		self.census_file = iface.addVectorLayer(fname,"census_file","ogr")
	   		QgsVectorFileWriter.writeAsVectorFormat(self.census_file,"Temp\census_file_wgsps.shp","utf-8",wgsps,"ESRI Shapefile")
	   		census_wgsps = iface.addVectorLayer("Temp\census_file_wgsps.shp","census_wgsps_distance","ogr")
	   		
	   		#Field calculator
   			expression_density = QgsExpression(""""Works"/$area""")
   			
   			#PickupsDensity/Prob
   			census_wgsps.startEditing()
   			pr = census_wgsps.dataProvider().addAttributes([QgsField("DensityW", QVariant.Double), QgsField("ProbW", QVariant.Double)])
   			census_wgsps.updateFields()
   			index = census_wgsps.fieldNameIndex("DensityW")
   			expression_density.prepare(census_wgsps.pendingFields())
   			for feature in census_wgsps.getFeatures():
   				value = expression_density.evaluate(feature)
   				census_wgsps.changeAttributeValue(feature.id(),index,value)
   				
   			density_sum = 0
   			for feature in census_wgsps.getFeatures():
   				density_sum += feature['DensityW']

   			index = census_wgsps.fieldNameIndex("ProbW")
   			for feature in census_wgsps.getFeatures():
   				value = feature["DensityW"]/density_sum
   				feature["ProbW"] = value
   				census_wgsps.updateFeature(feature)
   			census_wgsps.commitChanges()
   			
   			_writer = QgsVectorFileWriter.writeAsVectorFormat(census_wgsps,"Temp\census_file.shp","utf-8",wgs,"ESRI Shapefile")
   			
   			census_prob = iface.addVectorLayer("Temp\census_file.shp","census_prob","ogr")
   	
   	def most_common(self,L):
   		return max(itertools.groupby(sorted(L)), key = lambda(x, v):(len(list(v)),-L.index(x)))[0]
   	
   	def normalize(self,lst):
   		sums = sum(lst)
   		if sums == 0:
   			return [1.0,0.0,0.0]
   	 	else:
   		  	norm = [float(i)/sums for i in lst]
	 	   	return norm
	 	   
	#Statistical
	def statistical(self):
		file = open("""C:""",'r')
		reader = csv.reader(file,delimiter=',',quotechar="'")
		head = reader.next()
		limiter = 0
		
		#Dict prepare
		hour_data = {}
		for hour_r in range(24):
		    hour_data[hour_r] = []
		    	
		    	
		for line in reader:
		    #if limiter>100:
		        #break
		    #limiter += 1
		    
		    call_date = line[14].replace("'","").lstrip()
		    hour = int(call_date.split(' ')[1].split(':')[0])
		    
		    line[30] = line[30].replace("'","").lstrip()
		    line[31] = line[31].replace("'","").lstrip()
		    	    	
		    for hour_r in range(24):
		    	if hour == hour_r:
		    		hour_data[hour_r].append([float(line[30]),float(line[31])])
		
		QgsMessageLog.logMessage(str(hour_data))    		
		for hour_r in range(24):
			result_stat = "Temp\stat_hour" + str(hour_r) + ".shp"
			result_stat_prob = "Temp\stathourSCDR2\stat" + str(hour_r) + ".shp"
			self.set_of_point_to_layer(result_stat, hour_data[hour_r])
			stat = iface.addVectorLayer(result_stat,"stat","ogr")
			try:
				self.points_to_denisty(result_stat, result_stat_prob)
			except:
				QgsMessageLog.logMessage(str(hour_r)+"Is an empty layer")
			QgsMapLayerRegistry.instance().removeMapLayer(stat.id())
		
		file.close()
		iface.messageBar().clearWidgets()
	
	#Statistical
	def prob_per_time(self):
		file = open("""C:""",'r')
		reader = csv.reader(file,delimiter=',',quotechar="'")
		head = reader.next()
		limiter = 0
		
		#Dict prepare
		hour_data = {}
		for hour_r in range(int(self.time_resolution)):
		    hour_data[hour_r] = []
		    	
		    	
		for line in reader:
		    #if limiter>100:
		        #break
		    #limiter += 1
		    
		    call_date = line[14].replace("'","").lstrip()
		    hour = int(call_date.split(' ')[1].split(':')[0])
		    minut = int(call_date.split(' ')[1].split(':')[2])
		    
		    
		    line[30] = line[30].replace("'","").lstrip()
		    line[31] = line[31].replace("'","").lstrip()
		    denom = self.time_denominator
		    for hour_r in range(int(self.time_resolution)):
		    	if hour_r/denom == hour + (round((minut/60.)*denom))/denom:
		    		hour_data[hour_r].append([float(line[30]),float(line[31])])
		
		QgsMessageLog.logMessage(str(hour_data))    
	
		for hour_r in range(int(self.time_resolution)):
			result_stat = "Temp\prob_hour" + str(hour_r) + ".shp"
			result_stat_prob = "Temp\stathourwhere2\stat" + str(hour_r) + ".shp"
			self.set_of_point_to_layer(result_stat, hour_data[hour_r])
			stat = iface.addVectorLayer(result_stat,"stat","ogr")
			try:
				self.points_to_denisty(result_stat, result_stat_prob)
			except:
				QgsMessageLog.logMessage(str(hour_r)+"Is an empty layer")
			QgsMapLayerRegistry.instance().removeMapLayer(stat.id())
		
		file.close()
		iface.messageBar().clearWidgets()
	
	#Not used
	def other_select(self,temporary_location,time):
		QgsMessageLog.logMessage(str(time))
		hour_r = (self.roundTime(time, 3600)).hour #hour is temporary
		QgsMessageLog.logMessage(str(hour_r))
		
		path = """\Temp\prob_in_hour\prob_in_hour"""+str(int(hour_r))+""".shp"""
		QgsMessageLog.logMessage(path)
		prob_layer = iface.addVectorLayer(path,"prob_hour","ogr")
		points_within = iface.addVectorLayer(temporary_location,"points_within","ogr")
		probField='JOIN'
		pointField = 'JOIN'
		joinObject = QgsVectorJoinInfo()
		joinObject.joinLayerId = prob_layer.id()
		joinObject.joinFieldName = probField
		joinObject.targetFieldName = pointField
		points_within.addJoin(joinObject)
		
		#Normalize prob in layer
		randomize_prob = []
		for feature in points_within.getFeatures():
			randomize_prob.append(np.float64(feature["prob_hour_Prob"]))
			
		sum_randomize_prob = sum(randomize_prob)
		randomize_prob = randomize_prob/sum_randomize_prob
		
		randomize_id = []
		for feature in points_within.getFeatures():
			geom = feature.geometry()
			point = geom.asPoint()
			randomize_id.append(point)
		
		max_key = np.random.choice(len(randomize_id), p = randomize_prob)
		QgsMapLayerRegistry.instance().removeMapLayer(prob_layer.id())
		QgsMapLayerRegistry.instance().removeMapLayer(points_within.id())
		return randomize_id[max_key]

		
	def write_prob(self,home,work,other,result):
		with open(result,'wb') as prob_file:
			prob_file.write('home, \n')
			for num_row in range(len(home)):
				num_row = num_row/self.time_denominator
				prob_file.write(str(num_row*self.time_denominator)+','+str(home[num_row])+'\n')
			prob_file.write('work, \n')
			for num_row in range(len(work)):
				num_row = num_row/self.time_denominator
				prob_file.write(str(num_row*self.time_denominator)+','+str(work[num_row])+'\n')
			prob_file.write('third test, \n')
			for num_row in range(len(other)):
				num_row = num_row/self.time_denominator
				prob_file.write(str(num_row*self.time_denominator)+','+str(other[num_row])+'\n')
		return None
