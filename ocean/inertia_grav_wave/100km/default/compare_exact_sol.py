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

#varNames = ['velocityX', 'velocityY', 'layerThickness']
varNames = ['layerThickness']

nVars = len(varNames)
timeArray = [0, 12, 24]
nTimes = len(timeArray)

fig = plt.gcf()
fig.set_size_inches(12.0, 10.0)

#dsMesh = Dataset('../base_mesh/planar_hex_mesh.nc','r')
# nx=dsMesh.getncattr('nx')
# ny=dsMesh.getncattr('ny')
# dsMesh.close()

ds = Dataset('output.nc', 'r')
yMinkm = min(ds.variables['yCell']) / 1.0e3
yMaxkm = max(ds.variables['yCell']) / 1.0e3

xtime = ds.variables['xtime']
# exact solution

# obtain dimensions and mesh variables
nCells = len(ds.dimensions['nCells'])
xCell = ds.variables['xCell']
yCell = ds.variables['yCell']
nEdges = len(ds.dimensions['nEdges'])
xEdge = ds.variables['xEdge']
yEdge = ds.variables['yEdge']
angleEdge = ds.variables['angleEdge']

Dc = 1.0e3 # 100km grid cell width
nx = 40
ny = nx

g = 10.0
f0 = 1e-4
Lz = 1000.0
nVertLevels = 1
H = Lz 

c = np.sqrt(g*H) #= 100 m s^(-1), 
Lx = nx*Dc
Ly = np.sqrt(3.0)/2.0 *ny*Dc
kx = 1*2*np.pi/Lx 
ky = 2*2*np.pi/Ly
omega = np.sqrt(g*H*(kx**2 + ky**2) + f0**2)

normalVelocity = ds.variables('normalVelocity')
ssh = ds.variables('ssh')
layerThickness = ds.variables('layerThickness')
daysSinceStartOfSim = ds.variables('daysSinceStartOfSim')
timeSec = daysSinceStartOfSim*86400.0

sshSol = np.zeros((nTime,nCells))
#sshDif = np.zeros((nTime,nCells))
#normalVelocitySol = np.zeros((nTime,nEdges,nVertLevels))
#normalVelocityDif = np.zeros((nTime,nEdges,nVertLevels))
for iTime in range(nTime):
    time = timeSec[timeArray[iTime]]

    for iCell in range(0, nCells):
        for k in range(0, nVertLevels):
            sshSol[0, iCell] = omega*np.cos(kx*xCell[iCell] + ky*yCell[iCell] - omega*time)
            #layerThickness[0, iCell, k] = Lz + ssh[0, iCell]

#    coef = omega*g/(omega**2 - f0**2)
#    for iEdge in range(0, nEdges):
#        x = xEdge[iEdge]
#        y = yEdge[iEdge]
#        cos1 = omega*np.cos(kx*x + ky*y - omega*time)
#        sin1 = f0*np.sin(kx*x + ky*y - omega*time)
#        for k in range(0, nVertLevels):
#            uEdgeTmp = coef*(kx*cos1 - ky*sin1)
#            vEdgeTmp = coef*(ky*cos1 + kx*sin1)
#            normalVelocitySol[0, iEdge, k]  = uEdgeTmp * np.cos(angleEdge[iEdge]) + vEdgeTmp * np.sin(angleEdge[iEdge])

# title at top:
# MPAS-O Test: Southern Ocean basin, 3000km x 4800m, cells:  40km x 100m
# Only Redi diffusion is on. All other tendencies are off. Nonlinear EOS.
# slope: 0.01

titleTxt = [', initial', ', time 1', ', time 2']
colTxt = ['model','solution','model-sol']
for iRow in range(nTimes):
    for iCol in range(3):
        if iCol == 0:
            var = np.squeeze(ssh[timeArray[iTime],:,0])
        elif iCol == 1:
            var = np.squeeze(sshSol[iTime,:,0])
        elif iCol == 2:
            var = np.squeeze(ssh[timeArray[iTime],:,0] - sshSol[iTime,:,0])
        iCol = 1
        plt.subplot(nVars, nTimes, iRow * nTimes + iCol + 1)
        plt.scatter(xCell[:]/1e3,yCell[:]/1e3,s=5,c=var[timeArray[iCol], :],marker='h')
        plt.clim(min(var[timeArray[iCol], :]),np.max(var[timeArray[iCol], :]))
        plt.title(varNames[iRow] + ' '+colTxt[iCol]+' t='+str(daysSinceStartOfSim/24)+'h']
        plt.jet()
        if iRow == nVars - 1:
            plt.xlabel('x, km')
        if iCol == 0:
            plt.ylabel('y, km')
        plt.colorbar()

        #print('plotting: '+varNames[iRow] + titleTxt[iCol])
        #print(' min: ',np.min(var[timeArray[iCol], :]), ' max: ',np.max(var[timeArray[iCol], :]))
        #print(var[timeArray[iCol], 1:50])
        #print('np.shape(var)',np.shape(var))
        #varSliced = np.transpose(var[timeArray[iCol], :, :])
        #varMasked = ma.masked_where(varSliced < -1.0e33, varSliced)
        #ax = plt.imshow(varMasked)  # ,extent=[yMinkm,yMaxkm,zMin,zMax])
        #plt.axis('off')

ds.close()
plt.savefig('Output.png')
