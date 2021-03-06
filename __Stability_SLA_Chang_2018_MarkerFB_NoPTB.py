﻿# -*- coding: utf-8-sig -*-

######################################################################################################################
#
#		EXPLORING THE EFFECT OF STEP LENGTH ASYMMETRY ON THE REACTIVE CONTROL OF STABILITY
#
#		Lucas De Macedo Pinheiro ~ August, 2016
#		Chang Liu ~ Oct, 2016 Modified 
#				    Oct, 24 
#					Nov.10, 2016, fix the PTB latency
#                           detect right HS at t, send out pulse t=100ms, treadmill start acc at t=200ms, treadmill reach max speed at t=600ms, then treadmill dcc 
#                   Dec.3, save step length
#					Jan.20, add 60steps for step length adaption, and calculate the timing before PTB
#							**Need to find the mapping of timing to actual elapse time, HS to HS=1.08sec elapse time=0.25
#					Jun.10,2018 Figure out the multithreading issue using viz.director()
#					Jun.14,2018 A no PTB version code
#		~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#		Python code for the perturbations trial. It starts the treadmill according
#		to "speed_S" values. A number of "ptb_max" perturbations are applied with
#		"speed_P" velocities after a random number of steps between "step_range",
#		left or right belt is also randomly chosen with the "belt_vec" list. 
#		Participants receive visual	feedback based on the output of the baseline
#		code. The same COP method is used. The program closes and the treadmill
#		stops after all perturbations are applied.
#			Inputs: "speed_S", "accel_max", "step_range", "speed_P", "SLA", "belt_vec"
#
######################################################################################################################
#              
#
#
###############################################################################
from __future__ import division
import viz
import vizshape # 2D or 3D indicators
import vizact
import socket
import struct
import json
import time
import random
import numpy 
import heapq
from labjack import ljm
import time
import timeit
import sys
from datetime import datetime
from time import sleep
import vizmultiprocess #Vizard does not support multiprocess but it has its own version 'vizmultiprocess'
##########################################################################################################################################################

accel_max = 20000	# Perturbations acceleration [mm/s] // make sure to change max accel in Treadmill Panel Settings
ptb_total= 6
belt_vec = random.sample(['L','R']*ptb_total, ptb_total*2)	# 10 left + 10 right perturbations shuffled, # not count the last perturbation
step_range = (20,30)	# min & max num steps until next perturbation  min <= x < max 
speed = float(raw_input('input self-selected speed?'))
print int(speed*1000)
speed_S = (int(speed*1000),int(speed*1000)) # Standard speeds [ vLeft, Right ] [mm/s]
speed_P = (int(speed*1000/2),int(speed*1000/2))  # Perturbation speed
elapse_time=0.25

start_L=[]
start_R=[]
SLA = 0 # enter value of desired asymmetry. If positive, left leg takes longer step and right takes shorter step to maitain stride legnth constant
flagL = 1
flagR = 1
scoreText_L = True
scoreText_R = True

f0 = open('C:\Users\User\Documents\Chang\Belt_ptb.txt','w') # store the sequence of perturbations
json.dump(belt_vec,f0)
f0.close()
print belt_vec

LeftAnkle = 0
LeftGTO = 1
RightAnkle = 2
RightGTO = 3
stanceFlagLeft = 0
stanceFlagRight = 0

stepOffsetRight = [0]
stepOffsetLeft = [0]


stepLengthLeft = [0]
stepLengthRight = [0]

posL=[0]
posR=[0]

sd_Left_temp = []
sd_Right_temp = []

ankleHeightL = 0.125
ankleHeightR = 0.125

successL_count = 0
successR_count = 0
save_successL_count=[]
save_successR_count=[]

Text_3d = viz.addText3D('',parent=viz.SCREEN,scene = viz.MainScene,fontSize=140,pos=[0.1,.8,2.5])
Text_3d.color(viz.RED)
Text_3d_right = viz.addText3D('',parent=viz.SCREEN,scene = viz.MainScene,fontSize=140,pos=[0.8,.8,2.5])
Text_3d_right.color(viz.RED) 

##########################################################################################################################################################

# Vizard window set up
viz.setMultiSample(4)   
viz.setOption('viz.glFinish',1)
viz.MainWindow.fov(100)
viz.go()
viz.addChild('ground_wood.osgb')

# load step length list from file ########change directory!!!
filename=raw_input('Please input the subject name to retrieve left/right step length file')+'.txt'
#test_no=raw_input('Please input the number of the test');
test_no = 1
temp_filepath='C:\\Users\\User\\Documents\\Chang\\LeftStepLength'+filename
temp_stepLengthLeft = open(temp_filepath,'r') # change directory
stepLengthLeft = json.load(temp_stepLengthLeft)
temp_stepLengthLeft.close()
temp_filepath='C:\\Users\\User\\Documents\\Chang\\RightStepLength'+filename
temp_stepLengthRight = open(temp_filepath,'r') # change directory
stepLengthRight = json.load(temp_stepLengthRight)
temp_stepLengthRight.close()

# calculate median
median_stepLengthLeft = numpy.median(stepLengthLeft)
f = open('C:\Users\User\Documents\Chang\LeftStepLength_median.txt','w')
json.dump(median_stepLengthLeft,f)
f.close()
median_stepLengthRight = numpy.median(stepLengthRight)
f1 = open('C:\Users\User\Documents\Chang\RightStepLength_median.txt','w')
json.dump(median_stepLengthRight,f1)
f1.close()
print "median_Left", median_stepLengthLeft
print "median_Right", median_stepLengthRight

# 100 values closest to the median
max_stepLengthLeft = heapq.nsmallest(100, stepLengthLeft, key=lambda x: abs(x-median_stepLengthLeft))	#100 values closest to the median
max_stepLengthLeft.sort(reverse = True)
f2 = open('C:\Users\User\Documents\Chang\LeftStepLength_100.txt','w')				
for item in max_stepLengthLeft:
	f2.write("%s\n" % item)
f2.close()
max_stepLengthRight = heapq.nsmallest(100, stepLengthRight, key=lambda x: abs(x-median_stepLengthRight))	#100 values closest to the median
max_stepLengthRight.sort(reverse = True)
f3 = open('C:\Users\User\Documents\Chang\RightStepLength_100.txt','w')				
for item in max_stepLengthRight:
	f3.write("%s\n" % item)
f3.close()

# calculate standard devation
sd_Left = 0
for number in range(len(max_stepLengthLeft)):
	sd_Left += ((max_stepLengthLeft[number] - median_stepLengthLeft)**2)/len(max_stepLengthLeft)
sd_Left = sd_Left**0.5
sd_Right = 0
for number in range(len(max_stepLengthRight)):
	sd_Right += ((max_stepLengthRight[number] - median_stepLengthRight)**2)/len(max_stepLengthRight)
sd_Right = sd_Right**0.5
print "sd_Left", sd_Left
print "sd_Right", sd_Right


################################################################################################################################


# Establish connection with Treadmill Control Panel
HOST = '127.0.0.1' #name of the target computer that runs the treadmill controller
PORT = 4000
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

# QTM initialization
QUALISYS_IP = '192.168.252.1'
qualisysOn = False

# Establish connection with LabJack
handle = ljm.openS("T7","USB", "ANY")
#Switch = ljm.openS("T7", "USB", "ANY")

## check if LabJack is communicating with the computer
name = "SERIAL_NUMBER"
result = ljm.eReadName(handle, name)

print("\neReadName result: ")
print("    %s = %f" % (name, result))
ljm.eWriteName(handle,"DAC0",0)
ljm.eWriteName(handle,"DAC1",0)


################################################################################################################################

def updateViewHQ(LeftAnkle, RightAnkle, LeftGTO, RightGTO):
	viz.MainView.setEuler(0,90,270)
	xyzCamera = qualisys.getMarker(LeftGTO).getPosition()
#	print xyzCamera
	xyzCamera1 = qualisys.getMarker(2).getPosition()
#	
	viz.MainView.setPosition(0,0.5,.4)
	viz.cam.setReset()
	vizact.onkeydown(' ',viz.cam.reset)
	
	positionL = qualisys.getMarker(LeftAnkle).getPosition()
#print positionL
	positionR = qualisys.getMarker(RightAnkle).getPosition()
	#print positionR
	analog = qualisys.getAnalog(0)
	#print analog
	ForcePlates = analog.getData()
	#print ForcePlates
	calibrationFz= 1000      # 3,3 value in Bertec calibation matrix
	GRFL = ForcePlates[3]*calibrationFz
	GRFR = ForcePlates[10]*calibrationFz
	#print "Left", GRFL
	#print "Right", GRFR
	
	positionL_Hip = qualisys.getMarker(LeftGTO).getPosition()
	positionR_Hip = qualisys.getMarker(RightGTO).getPosition()

	targetL = vizshape.addQuad(size=(SL_Left, .15,),axis=vizshape.AXIS_Y, cullFace=False,color=viz.GREEN,pos=(SL_Left/2,0.01,positionL[2]))
	targetL2 = vizshape.addQuad(size=(SL_Left*8, .15,),axis=vizshape.AXIS_Y, cullFace=False,color=viz.GREEN,pos=(-4*SL_Left,0.01,positionL[2]))
	targetL_bottom = vizshape.addQuad(size=(0.01, .25,),axis=vizshape.AXIS_Y, cullFace=False,color=viz.RED,pos=(SL_Left - 2*sd_Left,0.01,positionL[2]))
	targetL_top = vizshape.addQuad(size=(0.01, .25,),axis=vizshape.AXIS_Y, cullFace=False,color=viz.RED,pos=(SL_Left + 2*sd_Left,0.01,positionL[2] ))

	targetR = vizshape.addQuad(size=(SL_Right, .15,),axis=vizshape.AXIS_Y, cullFace=False,color=viz.BLUE,pos=( SL_Right/2 ,0.01,positionR[2]))
	targetR2 = vizshape.addQuad(size=(SL_Right*8, .15,),axis=vizshape.AXIS_Y, cullFace=False,color=viz.BLUE,pos=(-4*SL_Right,0.01,positionR[2]))
	targetR_bottom = vizshape.addQuad(size=(0.01, .25,),axis=vizshape.AXIS_Y, cullFace=False,color=viz.RED,pos=(SL_Right - 2*sd_Right,0.01,positionR[2]))
	targetR_top = vizshape.addQuad(size=(0.01, .25,),axis=vizshape.AXIS_Y, cullFace=False,color=viz.RED,pos=(SL_Right + 2*sd_Right,0.01,positionR[2] ))

def qualisysInit():
	qualisys = viz.add('qualisys.dle', 0, QUALISYS_IP)
	return qualisys

# function to generate data packet to send to Treadmill Control Panel
def serializepacket(speedL,speedR,accL,accR,theta):
	fmtpack = struct.Struct('>B 18h 27B')#should be 64 bits in length to work properly
	outpack = fmtpack.pack(0,speedR,speedL,0,0,accR,accL,0,0,theta,~speedR,~speedL,~0,~0,~accR,~accL,~0,~0,~theta,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)
	return(outpack)
	
def receivePacket(recvPack):
	unpack = (0,0)
	if len(bytes(recvPack[0])) == 32:
		unpack=struct.unpack('>B 5h 21B',bytes(recvPack[0])) #must be 32bytes and only need the first item from the tuple	
	elif len(bytes(recvPack[0])) == 64:
		unpack=struct.unpack('>B 18h 27B',bytes(recvPack[0]))
	return(unpack)

def qtm_receive():
	analog = qualisys.getAnalog(0)
	ForcePlates = analog.getData()	# [Zero, Fx1, Fy1, ..., My2, Mz2]
	
	# calibration factors // QTM options > Force Data > Calibration 
	Fcal = (500,500,1000,800,400,400)	# Fx,Fy,Fz,Mx,My,Mz // Calibration Matrix
	
	# Force Plates Vector to return
	FP = [0,0,0,0,0,0,0,0,0,0,0,0]	# FxL,FyL,GRFL,MxL,MyL,MzL,  FxR,FyR,GRFR,MxR,MyR,MzR
	
	# left force plate
	FP[0] = ForcePlates[1]*Fcal[0]	# FxL
	FP[1] = ForcePlates[2]*Fcal[1]	# FyL
	FP[2] = ForcePlates[3]*Fcal[2]	# FzL
	FP[3] = ForcePlates[4]*Fcal[3]	# MxL
	FP[4] = ForcePlates[5]*Fcal[4]	# MyL
	FP[5] = ForcePlates[6]*Fcal[5]	# MzL
	# right force plate
	FP[6] = ForcePlates[8]*Fcal[0]	# FxR
	FP[7] = ForcePlates[9]*Fcal[1]	# FyR
	FP[8] = ForcePlates[10]*Fcal[2]	# FzR
	FP[9] = ForcePlates[11]*Fcal[3]	# MxR
	FP[10] = ForcePlates[12]*Fcal[4]# MyR
	FP[11] = ForcePlates[13]*Fcal[5]# MzR
	
	return FP

# updated here; communicate with LabJack to send an impulse

def labjack_impulse():
	#ou would typically use LJM_eWriteNames() or LJM_eNames()
	#Pulse the valve
	ljm.eWriteName(handle,"FIO1",1)
	time.sleep(0.01)
	ljm.eWriteName(handle,"FIO1",0)
	print "send pulse"
################################################################################################################################
def AnkleTracking(flagL,flagR,LeftAnkle, RightAnkle, LeftGTO, RightGTO,ankleHeightL,ankleHeightR,successL_count,successR_count): 
	global start_L, start_R,scoreText_L,scoreText_R  
	
	# Show steps
	
	
#	Text_3d.message('{}'.format(numsteps))
#	fadeOut4 = vizact.fadeTo(0,time=0.5)
#	Text_3d.addAction(fadeOut4)	


	positionL = qualisys.getMarker(LeftAnkle).getPosition()
	
	#print positionL
	positionR = qualisys.getMarker(RightAnkle).getPosition()
	#print positionR
	analog = qualisys.getAnalog(0)
	#print analog
	ForcePlates = analog.getData()
	#print ForcePlates
	calibrationFz= 1000      # 3,3 value in Bertec calibation matrix
	GRFL = ForcePlates[3]*calibrationFz
	GRFR = ForcePlates[10]*calibrationFz
	#print "Left", GRFL
	#print "Right", GRFR
	positionL_Hip = qualisys.getMarker(LeftGTO).getPosition()
	positionR_Hip = qualisys.getMarker(RightGTO).getPosition()
	temp_stepLengthLeft  = positionL [0] - positionR [0]
	temp_stepLengthRight  = positionR [0] - positionL [0]
	# LEFT LEG
	
	if  ( 50<GRFL<2000):  # --> leg is in stance phase, hide ankle location
		markerposL=positionL[0]-positionR[0]
		
		markerL = vizshape.addQuad(size=(0.05, 0.05),axis=-vizshape.AXIS_Y, cullFace=True, cornerRadius=0.05,pos=(markerposL,positionL[1],positionL[2]))
		ankleHeightL = positionL[1]
		fadeOut = vizact.fadeTo(0,time=0.00)           
		markerL.addAction(fadeOut)
		if (flagL == 1):
			if (temp_stepLengthLeft > 0):
				flagL = 0
				
		if (abs(markerposL -  median_stepLengthLeft)  <  8*sd_Left + 0.01) & (scoreText_L == True):
#			if (positionL[1] < ankleHeightL and
#				abs (positionL[2] - positionL_Hip[2] ) < 0.05):
#							
					successL_score = int(round(10 - 10*abs(1 - ( markerposL/SL_Left ))))
#					save_successL_count.append(successL_score)
					
#					print total_successR_count
#					f = open('C:\Users\User\Documents\Natalia\QTM\save_successL_count.txt','w')
#					json.dump(save_successL_count,f)
#					f.close()
					print successL_score
					Text_3d.message('{}'.format(successL_score))
#					fadeOut = vizact.fadeTo(0,time=0.2) 
					scoreText_L = False
					#####################################################
					###### ADJUST BASED ON TM SPEED, FOR SPEED>0.5 USE ~.5
					##### FOR SPEED < 0.5 USE ~.7 #######################
					#####################################################
#					time.sleep(.15)
								

	elif (GRFL < 50): # --> leg is in swing phase, track ankle location
		markerposL=positionL[0]-positionR[0]
		markerL = vizshape.addQuad(size=(0.05, 0.05),axis=-vizshape.AXIS_Y, cullFace=False, cornerRadius=0.05,pos=(markerposL,positionL[1],positionL[2])) 
		fadeOut = vizact.fadeTo(0,time=0.00)           
		markerL.addAction(fadeOut)
		temp_stepLengthLeft  = positionL [0] - positionR [0]
		flagL = 1
		scoreText_L = True
	# RIGHT LEG
	
	if ( 50<GRFR<2000 ):  # --> leg is in stance phase, hide ankle location
		markerposR=positionR[0]-positionL[0]
		markerR = vizshape.addQuad(size=(0.05, 0.05),axis=-vizshape.AXIS_Y, cullFace=True, cornerRadius=0.05,pos=(markerposR,positionR[1],positionR[2]))
		ankleHeightR = positionR[1]
		fadeOut = vizact.fadeTo(0,time=0.00)           
		markerR.addAction(fadeOut)
		
		if (flagR == 1):
			if (temp_stepLengthRight > 0):
				flagR = 0
				start_R.append(time.clock())
				
		if (abs(median_stepLengthRight -  markerposR)  <  8*sd_Right + 0.01) & (scoreText_R == True):
#			if (positionR[1] < ankleHeightR and
#				abs (positionR[2] - positionR_Hip[2] ) < 0.05):
#							
					successR_score = int(round(10 - 10*abs(1 - ( markerposR/SL_Right ))))
					save_successR_count.append(successR_score)
					
#					print total_successR_count
#					f = open('C:\Users\User\Documents\Natalia\QTM\save_successR_count.txt','w')
#					json.dump(save_successR_count,f)
#					f.close()
					
					Text_3d_right.message('{}'.format(successR_score))
#					
					
					#####################################################
					###### ADJUST BASED ON TM SPEED, FOR SPEED>0.5 USE ~.5
					##### FOR SPEED < 0.5 USE ~.7 #######################
					#####################################################
					scoreText_R= False


	elif (GRFR < 50): # --> leg is in swing phase, track ankle location
		markerposR=positionR[0]-positionL[0]
		markerR = vizshape.addQuad(size=(0.05, 0.05),axis=-vizshape.AXIS_Y, cullFace=False, cornerRadius=0.05,pos=(markerposR,positionR[1],positionR[2])) 
		fadeOut = vizact.fadeTo(0,time=0.00)           
		markerR.addAction(fadeOut)
		flagR = 1
		scoreText_R= True
###############################################################		

# Map veloctity to voltage
def velocityToVoltage(velocityL,velocityR):
	maxVelocity=3000; #in mm/s
	minVelocity=0; #in mm/s
	maxVoltage=5; #in volts
	minVoltage=0;
	outputVoltageL=maxVoltage/maxVelocity*velocityL
	outputVoltageR=(maxVoltage-minVoltage)/(maxVelocity-minVelocity)*velocityR
#	print outputVoltageL, outputVoltageR
	ljm.eWriteName(handle, "DAC0", outputVoltageL)
	ljm.eWriteName(handle,"DAC1",outputVoltageR) ### fix
#	return (outputVoltageL, outputVoltageR)

def acquireVelocity():
	data=s.recvfrom(1024)
	unpackStruct=receivePacket(data)
#	print(unpackStruct)
	speedL=unpackStruct[2]
	speedR=unpackStruct[1]
	velocityToVoltage(speedL,speedR)
#	print "speedR=",speedR
#	print "speedL=",speedL

	
def labjack_impulse_L():
	ljm.eWriteName(handle, "DAC0", 2)
	time.sleep(0.01)
	ljm.eWriteName(handle, "DAC0", 1)
	
def labjack_impulse_R():
	ljm.eWriteName(handle, "DAC1", 2)
	time.sleep(0.01)
	ljm.eWriteName(handle, "DAC1", 1)
	
######################################################################################################################
#
#		EQUATIONS FOR COP FROM ANALOG DATA
#
#		Xcop = -XOffset + (-h*Fx - My)/Fz
#		Ycop = -YOffset + (-h*Fy + Mx)/Fz
#		h, XOFfset and YOffset are found in QTM Plate Calibration Config
#		** COP in Plate Coordinates **
#
######################################################################################################################

#def StepLength(COP_L, COP_R, width=0.05, length=0.05):
#	global flagL, flagR, SL_Left, SL_Right, sd_Left, sd_Right, successL_count, successR_count, start_L, start_R
#	
#	
#	# offset factors // QTM options > Force Data > Calibration 
#	Xoff = 0.2795	# X offset (for right force plate, invert to be -0.2795)
#	Yoff = 0.889
#	h = 0	# Zoff = h
#	
#	FPtemp = qtm_receive()	# force plate data
#	
#	# left force plate
#	COP_L = [0,0]
#	FxL = FPtemp[0]
#	FyL = FPtemp[1]
#	GRFL = FPtemp[2]
#	MxL = FPtemp[3]
#	MyL = FPtemp[4]
#	# right force plate
#	COP_R = [0,0]
#	FxR = FPtemp[6]
#	FyR = FPtemp[7]
#	GRFR = FPtemp[8]
#	MxR = FPtemp[9]
#	MyR = FPtemp[10]
#	
#	
#	# LEFT LEG
#	if ( 80<GRFL<2000 ):  # stance phase...	
#		if (flagL == 1):	# swing phase flag
#			flagL = 0	# not swing phase anymore
#			
#			start_L.append(time.clock()) #want to time btw heel strike
##			print start_L
#			
#			# COP calculation // constants added to change coordinate system from Plate to LAB 
#			# [+Xlab, +Ylab] = [+Yplate + 0.8162, +Xplate + 0.7798]
#			COP_L = [ (-Yoff + (((-h*FyL)+MxL)/GRFL) + 0.8162) , (Xoff + (((-h*FxL)-MyL)/GRFL) + 0.7798) ]
#			COP_R = [ (-Yoff + (((-h*FyR)+MxR)/GRFR) + 0.8154) ,(-Xoff + (((-h*FxR)-MyR)/GRFR) + 0.2124) ]	
#			
#			SL_L = COP_L[0]-COP_R[0]	#left step length
#			markerL = vizshape.addQuad(size=(length, width),axis= -vizshape.AXIS_Y,cullFace=False,cornerRadius=0.05,pos=[SL_L,0.02,0.7])
#			fadeOut = vizact.fadeTo(0,time=0.7)           
#			markerL.addAction(fadeOut)
#			
#			stepLengthLeft.append(SL_L)	# step length list
#			#stepLengthLeft.sort(reverse = True)	# greatest first
##			print "stepLengthLeft", stepLengthLeft
##			should not overlap with the previous trial
##			filepath='C:\\Users\\User\\Documents\\Chang\\LeftStepLength'+test_no+filename
##			f = open(filepath,'w')
##			json.dump(stepLengthLeft,f)
##			f.close()
#			#print "COP_L x", COP_L[0], "COP_R x", COP_R[0]
#			#print "left step length", SL_L
#			
#			if abs(SL_L-SL_Left) <= (2*sd_Left + 0.01):	# success message
#				successL =  viz.addText('Success!', parent=viz.SCREEN, scene = viz.MainScene, color=viz.GREEN, fontSize=80, pos=[0.2,0.05,0])
#				fadeOut4 = vizact.fadeTo(0,time=0.5)
#				successL.addAction(fadeOut4)
#				
#				successL_count += 1
##				f = open('C:\Users\User\Documents\Chang\save_successL_count.txt','w')
##				json.dump(successL_count,f)
##				f.close()
#				
#				print "successL_count", successL_count				
##				time.sleep(0.15)
#				
#	elif ( GRFL<=80 ):	# swing phase...
#		flagL = 1
#
#
#	# RIGHT LEG
#	if ( 80<GRFR<2000 ):  # stance phase...
#		if (flagR == 1):	# swing phase flag
#			flagR = 0	# not swing phase anymore
#			start_R.append(time.clock())
##			print "startR",start_R
#			
#			# COP calculation // constants added to change coordinate system from Plate to LAB 
#			# [+Xlab, +Ylab] = [+Yplate + 0.8154, +Xplate + 0.2124]
#			COP_R = [ (-Yoff + (((-h*FyR)+MxR)/GRFR) + 0.8154) ,(-Xoff + (((-h*FxR)-MyR)/GRFR) + 0.2124) ]	
#			COP_L = [ (-Yoff + (((-h*FyL)+MxL)/GRFL) + 0.8162) , (Xoff + (((-h*FxL)-MyL)/GRFL) + 0.7798) ]
#			
#			SL_R = COP_R[0]-COP_L[0]	#right step length
#			markerR = vizshape.addQuad(size=(length, width),axis= -vizshape.AXIS_Y,cullFace=False,cornerRadius=0.05,pos=[SL_R,0.02,0.3])
#			fadeOut = vizact.fadeTo(0,time=0.7)           
#			markerR.addAction(fadeOut)
#			
#			stepLengthRight.append(SL_R)	# step length list
#			#stepLengthRight.sort(reverse = True)	# greatest first
##			print "stepLengthRight", stepLengthRight
##			filepath2='C:\\Users\\User\\Documents\\Chang\\RightStepLength'+test_no+filename
##			f1 = open(filepath2,'w')
##			json.dump(stepLengthRight,f1)
##			f1.close()
#			#print "COP_R x", COP_R[0], "COP_L x", COP_L[0]
#			#print "right step length", SL_R
#			
#			if abs(SL_R-SL_Right) <= (2*sd_Right + 0.01):	# success message
#				successR =  viz.addText('Success!', parent=viz.SCREEN, scene = viz.MainScene, color=viz.BLUE, fontSize=80, pos=[0.55,0.05,0])
#				fadeOut5 = vizact.fadeTo(0,time=0.5)
#				successR.addAction(fadeOut5)
#				
#				successR_count += 1
##				f = open('C:\Users\User\Documents\Chang\save_successR_count.txt','w')
##				json.dump(successR_count,f)
##				f.close()
#				print "successR_count", successR_count				
##				time.sleep(0.15)
#				
#	elif ( GRFR<=80 ):	# swing phase...
#		flagR = 1
			

	
#########################################################################################################################


temp = raw_input('Is QTM recording?<y/n>')
if temp == 'y':
    qualisys = qualisysInit()
    qualisysOn = True

trial = raw_input('Input "a" for baseline SLA; Input "b" for symmetry SLA')
if qualisysOn:
	# visual display variables
	# add option to bring the short leg longer for symmetric walking
	if trial == 'a':
		alpha = (median_stepLengthLeft + median_stepLengthRight)*SLA/2	# alpha in SLA formula
		SL_Left = median_stepLengthLeft + alpha
		SL_Right = median_stepLengthRight - alpha
	elif trial =='b':
		if median_stepLengthLeft >= median_stepLengthRight:
			SL_Left =  median_stepLengthLeft
			SL_Right = median_stepLengthLeft
		else:
			SL_Right = median_stepLengthRight
			SL_Left = median_stepLengthRight
	
	# Initial condition
	updateViewHQ(LeftAnkle, RightAnkle, LeftGTO, RightGTO)
#	time.sleep(7)
	
#	time.sleep(10)	# delay [sec]
	
	# perturbations variables
	stp = 80 # 80steps initial instead of random.randint(step_range[0], step_range[1])
	
	Lstp_flag = 0	# identify swing phase
	Rstp_flag = 0
	stp_counter = 0
	belt = belt_vec[0]	# initialization
	ptb_max = len(belt_vec)	# max number of perturbations
	ptb = 1	# current perturbation
	
	
#	out = serializepacket(speed_S[0],speed_S[1],200,200,0)
#	s.sendall(out)
	vizact.ontimer2(0,viz.FOREVER,AnkleTracking,flagL,flagR,LeftAnkle, RightAnkle, LeftGTO, RightGTO,ankleHeightL,ankleHeightR,successL_count,successR_count)
	vizact.ontimer2(0,viz.FOREVER,acquireVelocity)
		
	
	
######################################################################################################################
#
#		?  IMPROVEMENTS  ?
#
#		Use bars/lines instead of the black dots for feedback
#		Create a countdown screen before treadmill starts/stops
#		Change the success to percentage
#		Add a success condition to apply perturbations, if success<threshold no perturbation
#		Better integrate "check_steps" and "StepLength" functions (steps counter, "check_steps" as interruption)
#
######################################################################################################################


