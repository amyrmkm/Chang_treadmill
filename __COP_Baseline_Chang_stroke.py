# -*- coding: utf-8-sig -*-

######################################################################################################################
#
#		EXPLORING THE EFFECT OF STEP LENGTH ASYMMETRY ON THE REACTIVE CONTROL OF STABILITY
#
#		Lucas De Macedo Pinheiro ~ August, 2016, Created
# 		Chang Liu ~ Oct 20, 2016 Modified
#                         ~ Oct 21, Modified filepath to allow for input user name
#                                   Reset camera position
#						  ~ Jun.6, 2018, Modified this code for PTB_stroke study
#		~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#		Python code for the baseline trial. It starts the treadmill according
#		to "speed_S" values and saves all the step lengths for left and right 
#		leg on .txt files , based on center of 
#		pressure (COP) coordinates calculated from the force plates data. It 
#		runs for approximately 5 min, as the variable "repeats" controls. The 
#		user has to close the window and stop the treadmill manually.
#			Inputs: "speed_S"
#
######################################################################################################################

import viz
import vizshape
import vizact
import socket
import struct
import time
import math
import json
import os
################################################################################################################################

 
filename=raw_input('input test subject name?')+'.txt'
speed = int(raw_input('input self-selected speed?'))
speed_S = (speed,speed) # Standard speeds [ vLeft, Right ] [mm/s]
################################################################################################################################

#vizshape.addAxes()
viz.setMultiSample(4)   
viz.setOption('viz.glFinish',1)
viz.MainWindow.fov(100)
viz.go()
viz.addChild('ground_gray.osgb')

QUALISYS_IP = '192.168.252.1'
qualisysOn = False

# Establish connection with Treadmill Control Panel
HOST = '127.0.0.1' #name of the target computer that runs the treadmill controller
PORT = 4000
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

#swing phase flags
flagL = 0
flagR = 0

stepLengthLeft = []
stepLengthRight = []
COP_L = [0,0]
COP_R = [0,0]

def updateViewHQ():
	viz.MainView.setEuler(0,90,270)
	viz.MainView.setPosition(0.15,0.65,0.5)	#[y,z,x]
	viz.cam.setReset()
	vizact.onkeydown(' ',viz.cam.reset)

# function to generate data packet to send to Treadmill Control Panel
def serializepacket(speedL,speedR,accL,accR,theta):
	fmtpack = struct.Struct('>B 18h 27B')#should be 64 bits in length to work properly
	outpack = fmtpack.pack(0,speedR,speedL,0,0,accR,accL,0,0,theta,~speedR,~speedL,~0,~0,~accR,~accL,~0,~0,~theta,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)
	return(outpack)
	

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

def StepLength(filename, stepLengthLeft,stepLengthRight,COP_L, COP_R, width=0.05, length=0.05):
	global flagL, flagR
	analog = qualisys.getAnalog(0)
	#print "analog", analog
	ForcePlates = analog.getData()	# [Zero, Fx1, Fy1, ..., My2, Mz2]
	#print "ForcePlates", ForcePlates
	
	# calibration/offset factors // QTM options > Force Data > Calibration 
	Fcal = (500,500,1000,800,400,400)	# Fx,Fy,Fz,Mx,My,Mz // Calibration Matrix
	Xoff = 0.2795	# X offset (for right force plate, invert to be -0.2795)
	Yoff = 0.889
	h = 0	# Zoff = h
	
	# left force plate
	COP_L = [0,0]
	FxL = ForcePlates[1]*Fcal[0]
	FyL = ForcePlates[2]*Fcal[1]
	GRFL = ForcePlates[3]*Fcal[2]
	MxL = ForcePlates[4]*Fcal[3]
	MyL = ForcePlates[5]*Fcal[4]
	# right force plate
	COP_R = [0,0]
	FxR = ForcePlates[8]*Fcal[0]
	FyR = ForcePlates[9]*Fcal[1]
	GRFR = ForcePlates[10]*Fcal[2]
	MxR = ForcePlates[11]*Fcal[3]
	MyR = ForcePlates[12]*Fcal[4]
	
	# LEFT LEG
	if ( 200<GRFL<2000 ):  # stance phase...# Does it need to change	
		if (flagL == 1):	# swing phase flag
			flagL = 0	# not swing phase anymore

			# COP calculation // constants added to change coordinate system from Plate to LAB 
			# [+Xlab, +Ylab] = [+Yplate + 0.8162, +Xplate + 0.7798]
			COP_L = [ (-Yoff + (((-h*FyL)+MxL)/GRFL) + 0.8162) , (Xoff + (((-h*FxL)-MyL)/GRFL) + 0.7798) ]
			COP_R = [ (-Yoff + (((-h*FyR)+MxR)/GRFR) + 0.8154) ,(-Xoff + (((-h*FxR)-MyR)/GRFR) + 0.2124) ]	
			
			SL_L = COP_L[0]-COP_R[0]	#left step length
			markerL = vizshape.addQuad(size=(length, width),axis= -vizshape.AXIS_Y,cullFace=False,cornerRadius=0.05,pos=[SL_L,0.15,0.7])
			fadeOut = vizact.fadeTo(0,time=0.7)           
			markerL.addAction(fadeOut)
			
			#print "COP_L x", COP_L[0], "COP_R x", COP_R[0]
			print "step length", SL_L

			stepLengthLeft.append(SL_L)	# step length list
			#stepLengthLeft.sort(reverse = True)	# greatest first
			#print "stepLengthLeft", stepLengthLeft
			#should not overlap with the previous trial
			filepath='C:\\Users\\User\\Documents\\Chang\\LeftStepLength'+filename
			f = open(filepath,'w')
			json.dump(stepLengthLeft,f)
			f.close()
		
	elif ( GRFL<=100 ):	# swing phase...
		flagL = 1


	# RIGHT LEG
	if ( 200<GRFR<2000 ):  # stance phase...
		if (flagR == 1):	# swing phase flag
			flagR = 0	# not swing phase anymore

			# COP calculation // constants added to change coordinate system from Plate to LAB 
			# [+Xlab, +Ylab] = [+Yplate + 0.8154, +Xplate + 0.2124]
			COP_R = [ (-Yoff + (((-h*FyR)+MxR)/GRFR) + 0.8154) ,(-Xoff + (((-h*FxR)-MyR)/GRFR) + 0.2124) ]	
			COP_L = [ (-Yoff + (((-h*FyL)+MxL)/GRFL) + 0.8162) , (Xoff + (((-h*FxL)-MyL)/GRFL) + 0.7798) ]
			
			SL_R = COP_R[0]-COP_L[0]	#right step length
			markerR = vizshape.addQuad(size=(length, width),axis= -vizshape.AXIS_Y,cullFace=False,cornerRadius=0.05,pos=[SL_R,0.15,0.3])
			fadeOut = vizact.fadeTo(0,time=0.7)           
			markerR.addAction(fadeOut)
			
			#print "COP_R x", COP_R[0], "COP_L x", COP_L[0]
			print "step length", SL_R
			
			stepLengthRight.append(SL_R)	# step length list
			#stepLengthRight.sort(reverse = True)	# greatest first
			print "stepLengthRight", stepLengthRight
			filepath2='C:\\Users\\User\\Documents\\Chang\\RightStepLength'+filename
			f1 = open(filepath2,'w')
			json.dump(stepLengthRight,f1)
			f1.close()
				
	elif ( GRFR<=100 ):	# swing phase...
		flagR = 1
			
#########################################################################################################################

def qualisysInit():
	qualisys = viz.add('qualisys.dle', 0, QUALISYS_IP)
	return qualisys
	

temp = raw_input('Is QTM recording?<y/n>')
if temp == 'y':
    qualisys = qualisysInit()
    qualisysOn = True

if qualisysOn:
	
	# Initial condition
	updateViewHQ()
#	time.sleep(10)
	out = serializepacket(speed_S[0],speed_S[1],100,100,0)
	s.sendall(out)
#	time.sleep(2)	# delay [sec]
	
	repeats = 20000
	vizact.ontimer2(0, repeats, StepLength, filename, stepLengthLeft, stepLengthRight, COP_L, COP_R, width=0.05, length=0.05,)
	

######################################################################################################################
#
#		IMPROVEMENTS ?
#
#		Possibly control QTM acquisition with the lab jack
#		Make it stop the treadmill when it's over (use time variable instead of "repeats")
#		Optimize file output
#
######################################################################################################################

