#!/usr/bin/env python
"""
This script plots results from MPAS-Ocean planar output.
"""
import numpy.ma as ma
import numpy as np
from netCDF4 import Dataset
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('Agg')

# varNames = ['velocityX', 'velocityY', 'layerThickness']
varNames = ['layerThickness']

nVars = len(varNames)
timeArray = [2,3,4]
nTime = len(timeArray)

fig = plt.gcf()
fig.set_size_inches(12.0, 10.0)

# dsMesh = Dataset('../base_mesh/planar_hex_mesh.nc','r')
# nx=dsMesh.getncattr('nx')
# ny=dsMesh.getncattr('ny')
# dsMesh.close()

print('read output')
ds = Dataset('output.nc', 'r')
#yMinkm = min(ds.variables['yCell']) / 1.0e3
#yMaxkm = max(ds.variables['yCell']) / 1.0e3

xtime = ds.variables['xtime']
# exact solution

print('compute exact solution')
# obtain dimensions and mesh variables
nCells = len(ds.dimensions['nCells'])
xCell = ds.variables['xCell'][:]
yCell = ds.variables['yCell'][:]
nEdges = len(ds.dimensions['nEdges'])
xEdge = ds.variables['xEdge']
yEdge = ds.variables['yEdge']
angleEdge = ds.variables['angleEdge']

Dc = 1.0e3  # 100km grid cell width
nx = 40
ny = nx

g = 9.80616
f0 = 1e-4
Lz = 1000.0
nVertLevels = 1
H = Lz

c = np.sqrt(g * H)  # = 100 m s^(-1), 
Lx = nx * Dc
Ly = np.sqrt(3.0) / 2.0 * ny * Dc
kx = 1 * 2 * np.pi / Lx
ky = 2 * 2 * np.pi / Ly
omega = np.sqrt(g * H * (kx ** 2 + ky ** 2) + f0 ** 2)

ssh = ds.variables['ssh'][:]
#layerThickness = ds.variables['layerThickness']
#normalVelocity = ds.variables['normalVelocity'][:]
daysSinceStartOfSim = ds.variables['daysSinceStartOfSim'][:]
timeSec = daysSinceStartOfSim * 86400.0
ds.close()

sshSol = np.zeros((nTime, nCells))
# sshDif = np.zeros((nTime,nCells))
# normalVelocitySol = np.zeros((nTime,nEdges,nVertLevels))
# normalVelocityDif = np.zeros((nTime,nEdges,nVertLevels))
for iRow in range(nTime):
    time = timeSec[timeArray[iRow]]

    for iCell in range(0, nCells):
        for k in range(0, nVertLevels):
            sshSol[iRow, iCell] = omega * np.cos(kx * xCell[iCell] + ky * yCell[iCell] - omega * time)
            # layerThickness[0, iCell, k] = Lz + ssh[0, iCell]

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
print('create plot')
titleTxt = [', initial', ', time 1', ', time 2']
colTxt = ['model', 'solution', 'model-sol']
nCol = 3
nRow = nTime
for iRow in range(nRow):
    iTime = timeArray[iRow]
    for iCol in range(nCol):
        if iCol == 0:
            var = np.squeeze(ssh[iTime, :])
        elif iCol == 1:
            var = np.squeeze(sshSol[iRow, :])
        else:
            var = np.squeeze(ssh[iTime, :] - sshSol[iRow, :])
        plt.subplot(nCol, nRow, iRow * nRow + iCol + 1)
        plt.scatter(xCell[:] / 1e3, yCell[:] / 1e3, s=5, c=var, marker='h')
        plt.clim(np.min(var), np.max(var))
        plt.title('ssh' + ' ' + colTxt[iCol] + ' t=' + str(round(daysSinceStartOfSim[iTime] *24*60,3)) + 'm')
        plt.jet()
        if iRow == nRow - 1:
            plt.xlabel('x, km')
        if iCol == 0:
            plt.ylabel('y, km')
        plt.colorbar()

        # print('plotting: '+varNames[iRow] + titleTxt[iCol])
        # print(' min: ',np.min(var[timeArray[iCol], :]), ' max: ',np.max(var[timeArray[iCol], :]))
        # print(var[timeArray[iCol], 1:50])
        # print('np.shape(var)',np.shape(var))
        # varSliced = np.transpose(var[timeArray[iCol], :, :])
        # varMasked = ma.masked_where(varSliced < -1.0e33, varSliced)
        # ax = plt.imshow(varMasked)  # ,extent=[yMinkm,yMaxkm,zMin,zMax])
        # plt.axis('off')

print('save plot')
plt.savefig('Compare_model_sol.png')
