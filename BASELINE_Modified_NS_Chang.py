import viz
import vizshape
import vizact
import socket
import struct
import time
import math
import json
import os

# inputs before the program starts
filename=raw_input('input test subject name?')+'.txt'
#speed = float(raw_input('input self-selected speed?'))
##print int(speed*1000)
#speed_S = (int(speed*1000),int(speed*1000)) # Standard speeds [ vLeft, Right ] [mm/s]

#############################
#vizshape.addAxes()
viz.setMultiSample(4)   
viz.setOption('viz.glFinish',1)
viz.MainWindow.fov(60)
viz.go()

viz.addChild('ground_gray.osgb')
QUALISYS_IP = '192.168.252.1'
qualisysOn = False
flagL = 1
flagR = 1

# Establish connection with Treadmill Control Panel
#HOST = '127.0.0.1' #name of the target computer that runs the treadmill controller
#PORT = 4000
#s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#s.connect((HOST, PORT))



# Make sure marker indices are correct in QTM. Order in QTM should be LAnkle, L_GTO, RAnkle, R_GTO


#Active Markers Aim Model

LeftAnkle = 0
LeftGTO = 1
RightAnkle = 2
RightGTO = 3

stepLengthLeft = [0]
stepLengthRight = [0]
sd_Left_temp = []
sd_Right_temp = []

def updateViewHQ (n = RightGTO): # n:index righ shoulder marker to set camera location
       viz.MainView.setEuler(0,90,270)
       positionCamera = qualisys.getMarker(n).getPosition()
       viz.MainView.setPosition(positionCamera[0],1,positionCamera[2])

def StepLength(flagL,flagR,stepLengthLeft,stepLengthRight,L = LeftAnkle, R = RightAnkle, width = 0.05, length = 0.05): # R: index in QTM for ankle marker right, L = index in QTM for ankle marker left
	positionL = qualisys.getMarker(L).getPosition()
	positionR = qualisys.getMarker(R).getPosition()
	analog = qualisys.getAnalog(0)
	ForcePlates = analog.getData()
	calibrationFz= 1000      # 3,3 value in Bertec calibation matrix
	GRFL = ForcePlates[3]*calibrationFz
	GRFR = ForcePlates[10]*calibrationFz
	temp_stepLengthLeft  = positionL [0] - positionR [0]
	temp_stepLengthRight  = positionR [0] - positionL [0]
	
	# LEFT LEG
	if (GRFL>30):  # --> leg is in stance phase, hide ankle location
		markerL = vizshape.addQuad(size = (length, width),axis = -vizshape.AXIS_Y, cullFace=True, cornerRadius=0.05,pos=positionL)
		if (flagL == 1):
			if (temp_stepLengthLeft > 0):
				stepLengthLeft.append(temp_stepLengthLeft)
				flagL = 0
				stepLengthLeft.sort(reverse = True)
#				print stepLengthLeft
#				max_stepLengthLeft = stepLengthLeft[:100]
				filepath='C:\\Users\\User\\Documents\\Chang\\LeftStepLength'+filename
				f = open(filepath,'w')
				json.dump(stepLengthLeft,f)
				f.close()
#				f_test = open('C:\Users\User\Documents\Natalia\QTM\LeftStepLengthtest.txt','w')				
#				for item in max_stepLengthLeft:
#					f_test.write("%s\n" % item)
#				mean_stepLengthLeft = float(sum(max_stepLengthLeft)) / len(max_stepLengthLeft)	
#				sd_Left = float(((sum(sd_Left_temp))/len(max_stepLengthLeft))**0.5)
#				f1 = open('C:\Users\User\Documents\Natalia\QTM\Left_MeanStepLength.txt','w')
#				json.dump(mean_stepLengthLeft,f1)
#				f1.close()
	else: # --> leg is in swing phase, track ankle location
			markerL = vizshape.addQuad(size=(length, width), axis =-vizshape.AXIS_Y, cullFace=False, cornerRadius=0.05,pos=positionL) 
			fadeOut = vizact.fadeTo(0,time=.05)           
			markerL.addAction(fadeOut)
			temp_stepLengthLeft  = positionL [0] - positionR [0]
			flagL = 1
			
	# RIGHT LEG
	if (GRFR>30):  # --> Right is in stance phase, hide ankle location
		markerR = vizshape.addQuad(size = (length, width),axis = -vizshape.AXIS_Y, cullFace=True, cornerRadius=0.05,pos=positionR)
		if (flagR == 1):
			if (temp_stepLengthRight > 0):
				stepLengthRight.append(temp_stepLengthRight)
				flagR = 0
				stepLengthRight.sort(reverse = True)
				max_stepLengthRight = stepLengthRight[:100]
				print stepLengthRight
				filepath2='C:\\Users\\User\\Documents\\Chang\\RightStepLength'+filename
				f1 = open(filepath2,'w')
				json.dump(stepLengthRight,f1)
				f1.close()
#				f_testR = open('C:\Users\User\Documents\Natalia\QTM\RightStepLengthtest.txt','w')				
#				for item in max_stepLengthRight:
#					f_testR.write("%s\n" % item)
#				mean_stepLengthRight = float(sum(max_stepLengthRight)) / len(max_stepLengthRight)
#				f3 = open('C:\Users\User\Documents\Natalia\QTM\Right_MeanStepLength.txt','w')
#				json.dump(mean_stepLengthRight,f3)
#				f3.close()


	else: # --> leg is in swing phase, track ankle location
			markerR = vizshape.addQuad(size=(length, width), axis =-vizshape.AXIS_Y, cullFace=False, cornerRadius=0.05,pos=positionR) 
			fadeOut = vizact.fadeTo(0,time=.05)           
			markerR.addAction(fadeOut)
			temp_stepLengthRight  = positionR [0] - positionL [0]
			flagR = 1

def serializepacket(speedL,speedR,accL,accR,theta):
	fmtpack = struct.Struct('>B 18h 27B')#should be 64 bits in length to work properly
	outpack = fmtpack.pack(0,speedR,speedL,0,0,accR,accL,0,0,theta,~speedR,~speedL,~0,~0,~accR,~accL,~0,~0,~theta,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)
	return(outpack)
	


######################################################################################################################################
        
def qualisysInit():
    qualisys = viz.add('qualisys.dle', 0, QUALISYS_IP)
    markerList = qualisys.getMarkerList()
    print markerList
    return qualisys


temp = raw_input('Initiate Quialisys?<y/n>')
if temp == 'y':
    qualisys=qualisysInit()
    qualisysOn=True
if qualisysOn:
	# Initial condition
	updateViewHQ()
#	time.sleep(10)
#	out = serializepacket(speed_S[0],speed_S[1],100,100,0)
#	s.sendall(out)
#	time.sleep(2)	# delay [sec]
	
	repeats = 20000
	vizact.ontimer2(0,repeats,updateViewHQ)
	vizact.ontimer2(0,repeats,StepLength,flagL,flagR,stepLengthLeft,stepLengthRight,L = LeftAnkle, R = RightAnkle, width = 0.05, length = 0.05)

	