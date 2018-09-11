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

SL_Left = median_stepLengthLeft
SL_Right = median_stepLengthRight 
print "SL_Left",SL_Left
print "SL_Right",SL_Right