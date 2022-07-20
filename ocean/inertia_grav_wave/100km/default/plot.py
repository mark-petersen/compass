#!/usr/bin/env python
'''
This script plots results from MPAS-Ocean planar output.
'''
import numpy.ma as ma
import numpy as np
from netCDF4 import Dataset
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

varNames = ['velocityX', 'velocityY', 'layerThickness']
nRow = len(varNames)
iTime = [0, 12, 24]
nCol = len(iTime)

fig = plt.gcf()
fig.set_size_inches(12.0, 10.0)

#ncfileMesh = Dataset('../base_mesh/planar_hex_mesh.nc','r')
# nx=ncfileMesh.getncattr('nx')
# ny=ncfileMesh.getncattr('ny')
# ncfileMesh.close()

ncfile = Dataset('output.nc', 'r')
ncfileIC = Dataset('../initial_state/initial_state.nc', 'r')
yMinkm = min(ncfile.variables['yCell']) / 1.0e3
yMaxkm = max(ncfile.variables['yCell']) / 1.0e3

xtime = ncfile.variables['xtime']
xCell = ncfile.variables['xCell']
yCell = ncfile.variables['yCell']

# title at top:
# MPAS-O Test: Southern Ocean basin, 3000km x 4800m, cells:  40km x 100m
# Only Redi diffusion is on. All other tendencies are off. Nonlinear EOS.
# slope: 0.01

titleTxt = [', initial', ', time 1', ', time 2']
for iRow in range(nRow):
    var = np.squeeze(ncfile.variables[varNames[iRow]])
    for iCol in range(nCol):
        #print('plotting: '+varNames[iRow] + titleTxt[iCol])
        #print(' min: ',np.min(var[iTime[iCol], :]), ' max: ',np.max(var[iTime[iCol], :]))
        #print(var[iTime[iCol], 1:50])
        plt.subplot(nRow, nCol, iRow * nCol + iCol + 1)
        #print('np.shape(var)',np.shape(var))
        plt.scatter(xCell[:]/1e3,yCell[:]/1e3,s=5,c=var[iTime[iCol], :],marker='h')
        plt.clim(min(var[iTime[iCol], :]),np.max(var[iTime[iCol], :]))
        #varSliced = np.transpose(var[iTime[iCol], :, :])
        #varMasked = ma.masked_where(varSliced < -1.0e33, varSliced)
        #ax = plt.imshow(varMasked)  # ,extent=[yMinkm,yMaxkm,zMin,zMax])
        #plt.axis('off')
        plt.title(varNames[iRow] + titleTxt[iCol])
        plt.jet()
        if iRow == nRow - 1:
            plt.xlabel('x, km')
        if iCol == 0:
            plt.ylabel('y, km')
        plt.colorbar()

ncfile.close()
ncfileIC.close()
plt.savefig('Output.png')
