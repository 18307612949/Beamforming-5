#*************************
#   Nec2hdf5.py
#
#   This reads a NEC output file that has used the PT
#card to print currents at the feed of antenna elements
#in an array, one PT card per element.  The currents are
#stored in an HDF5 file for easy use in MATLAB, Python or C
#
#   TO DO:
#       Add Polarization
#       See if it can all be done in one pass?
#           splitting it up takes slightly more time
#           easier to follow though...
#*************************

import h5py 
import numpy as np
import re

f = open("Test.out","r") 

#Normalize so that at each frequency max is magnitude 1
Normalize = True

#***************************
#   Create HDF5 file
#***************************
f5 = h5py.File("testnec.h5","w")

#*****************
#   Get Parameters
#*****************
#  Frequencies 
#  Azimuths
#  Elevations
#  Number of array elements
#
#  Does not currently
#  use polarization
#
#*****************
freq = set()
azm = set()
elev = set()
Elem = set()


ii = 1
for line in f:
    #*************************
    #   Find Frequency in MHz
    #*************************
    if("FREQUENCY" in line): 
        #Parse the number from NEC
        freq_i = re.findall('[\d.]+',f.readline())
        freq_i = round(float(freq_i[0]) * 10**(float(freq_i[1])),4)
        freq.add(freq_i) 
    
    if("THETA" in line):
        f.readline() #Skip line
        
        #Parse out useful data
        for data in f:
            if(not data.strip() or "DATA" in data):
                break
            dataArray = re.findall('[+-]?\d+(?:\.\d+)?',data) 
            elev.add(float(dataArray[0]))
            azm.add(float(dataArray[1]))
            Elem.add(int(dataArray[5]))

#Reset to top of file
f.seek(0)

freq = sorted(list(freq))
elev = sorted(list(elev))
azm = sorted(list(azm))
Elem = sorted(list(Elem))


#******************************
#   Create HDF5 File Structure
#
#   /Freq/Elev/Elem Mag[Azm]
#                   Phase[Azm]
#******************************
f5.create_group("Frequency (MHz)")
f5.create_dataset("listFreq", data = np.asarray(freq))
f5.create_dataset("listElev", data = np.asarray(elev))
f5.create_dataset("listAzm", data = np.asarray(azm))
for ff in freq:
    gFreq = f5.create_group(str(ff))
    gFreq.create_group("Elevation (degrees)")
    for th in elev:
        gElev = gFreq.create_group(str(th))
        gElev.create_group("Elements") 
        for ii in Elem:
            gElem = gElev.create_group(str(ii))

#**************************
#   Put Mag/Phase data into
#   the HDF5 file
#**************************
mag = np.zeros((len(elev),len(azm)))
phase = np.zeros((len(elev),len(azm)))

freqIdx = 0
elemIdx = 0
for line in f:
    
    if(freqIdx >= len(freq)):
        freqIdx = 0
        elemIdx = elemIdx + 1

    #Parse nearly identital to before
    if("THETA" in line):
        f.readline()

        #Need to iterate over [Elev,Azm]
        ii = 0
        jj = 0
        for data in f:      
            #Find end of data
            if(not data.strip() or "DATA" in data):
                break
            #Regex out numbers 
            dataArray = re.findall('[+-]?\d+(?:\.\d+)?',data)
            
            #make mag[elev,azm] array
            mag[jj,ii] = float(dataArray[2]) * 10**(float(dataArray[3]))
            phase[jj,ii] = float(dataArray[4])
            if(jj < len(elev)-1):
                jj = jj + 1
            else:
                jj = 0 
                ii = ii + 1  
        
        #Place array in the dataset
        for th in range(len(elev)):
            gElem = f5[str(freq[freqIdx])][str(elev[th])][str(Elem[elemIdx])]
            gElem.create_dataset("Magnitude",data = mag[th,:])
            gElem.create_dataset("Phase", data = phase[th,:])
        freqIdx = freqIdx + 1
        
f.close()


