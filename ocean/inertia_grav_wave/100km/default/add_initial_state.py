#!/usr/bin/env python
'''
This script creates an initial condition file for MPAS-Ocean.
'''
import os
import shutil
import numpy as np
import netCDF4 as nc
from netCDF4 import Dataset
#import xarray as xr

Ly = 10000.0e3
Lz = 1000.0
nVertLevels = 1

def main():
    # {{{

    shutil.copy2('base_mesh.nc', 'initial_state.nc')
    ds = Dataset('initial_state.nc', 'a', format='NETCDF3_64BIT_OFFSET')
    #ds = xr.open_dataset('initial_state.nc')
    
    print('vertical_init(ds)')
    vertical_init(ds)
    print('velocity_init(ds)')
    velocity_init(ds)
    print('tracer_init(ds)')
    tracer_init(ds)
    print('coriolis_init(ds)')
    coriolis_init(ds)
    print('others_init(ds)')
    others_init(ds)

    ds.close()
# }}}

def vertical_init(ds):
    thicknessAllLayers = Lz #100.0  # [m] for evenly spaced layers
    minLayers = 3
# {{{
    # create new variables # {{{
    ds.createDimension('nVertLevels', nVertLevels)
    refLayerThickness = ds.createVariable(
        'refLayerThickness', np.float64, ('nVertLevels',))
    maxLevelCell = ds.createVariable('maxLevelCell', np.int32, ('nCells',))
    refBottomDepth = ds.createVariable(
        'refBottomDepth', np.float64, ('nVertLevels',))
    refZMid = ds.createVariable('refZMid', np.float64, ('nVertLevels',))
    bottomDepth = ds.createVariable('bottomDepth', np.float64, ('nCells',))
    bottomDepthObserved = ds.createVariable(
        'bottomDepthObserved', np.float64, ('nCells',))
    restingThickness = ds.createVariable(
        'restingThickness', np.float64, ('nCells', 'nVertLevels',))
    vertCoordMovementWeights = ds.createVariable(
        'vertCoordMovementWeights', np.float64, ('nVertLevels',))
    # }}}

    # obtain dimensions and mesh variables # {{{
    nCells = len(ds.dimensions['nCells'])
    xCell = ds.variables['xCell']
    yCell = ds.variables['yCell']
    # }}}

    # evenly spaced vertical grid
    refLayerThickness[:] = thicknessAllLayers

    # Create other variables from refLayerThickness
    refBottomDepth[0] = refLayerThickness[0]
    refZMid[0] = -0.5 * refLayerThickness[0]
    for k in range(1, nVertLevels):
        refBottomDepth[k] = refBottomDepth[k - 1] + refLayerThickness[k]
        refZMid[k] = -refBottomDepth[k - 1] - 0.5 * refLayerThickness[k]
    vertCoordMovementWeights[:] = 1.0

    # flat bottom, no bathymetry
    #maxLevelCell[:] = nVertLevels
    #bottomDepth[:] = refBottomDepth[nVertLevels-1]
    #bottomDepthObserved[:] = refBottomDepth[nVertLevels-1]
    # for k in range(nVertLevels):
    #    layerThickness[0,:,k] = refLayerThickness[k]
    #    restingThickness[:,k] = refLayerThickness[k]

    # Define bottom depth: parabola
    for iCell in range(0, nCells):
        x = xCell[iCell]
        y = yCell[iCell]
        bottomDepthObserved[iCell] = Lz

    # full cells, not partial
    # initialize to very bottom:
    maxLevelCell[:] = nVertLevels
    bottomDepth[:] = refBottomDepth[nVertLevels - 1]
    for k in range(nVertLevels):
        #layerThickness[0, :, k] = refLayerThickness[k]
        restingThickness[:, k] = refLayerThickness[k]
    for iCell in range(0, nCells):
        x = xCell[iCell]
        y = yCell[iCell]
        for k in range(nVertLevels):
            if bottomDepthObserved[iCell] < refBottomDepth[k]:
                maxLevelCell[iCell] = 1 #max(k, minLayers)
                bottomDepth[iCell] = refBottomDepth[maxLevelCell[iCell] - 1]
                break
# }}}

def tracer_init(ds):
# {{{

    # create new variables # {{{
    tracer1 = ds.createVariable(
        'tracer1', np.float64, ('Time', 'nCells', 'nVertLevels',))
    tracer2 = ds.createVariable(
        'tracer2', np.float64, ('Time', 'nCells', 'nVertLevels',))
    tracer3 = ds.createVariable(
        'tracer3', np.float64, ('Time', 'nCells', 'nVertLevels',))
    temperature = ds.createVariable(
        'temperature', np.float64, ('Time', 'nCells', 'nVertLevels',))
    salinity = ds.createVariable(
        'salinity', np.float64, ('Time', 'nCells', 'nVertLevels',))
    layerThickness = ds.variables['layerThickness']
    # }}}

    # obtain dimensions and mesh variables # {{{
    nVertLevels = len(ds.dimensions['nVertLevels'])
    nCells = len(ds.dimensions['nCells'])
    xCell = ds.variables['xCell']
    yCell = ds.variables['yCell']
    refZMid = ds.variables['refZMid']
    refBottomDepth = ds.variables['refBottomDepth']
    # }}}
    for iCell in range(0, nCells):
        x = xCell[iCell]
        y = yCell[iCell]
        for k in range(0, nVertLevels):
            z = refZMid[k]

            temperature[0, iCell, k] = 10.0
            salinity[0, iCell, k] = 35.0
            tracer1[0, iCell, k] = 1.0
            tracer2[0, iCell, k] = 1.0
            tracer3[0, iCell, k] = 1.0

# }}}

def velocity_init(ds):
    # {{{
    # obtain dimensions and mesh variables # {{{
    nCells = len(ds.dimensions['nCells'])
    xCell = ds.variables['xCell']
    yCell = ds.variables['yCell']
    nEdges = len(ds.dimensions['nEdges'])
    xEdge = ds.variables['xEdge']
    yEdge = ds.variables['yEdge']
    angleEdge = ds.variables['angleEdge']
    # }}}
    Dc = 1.0e3 # 100km grid cell width
    nx = 40
    ny = nx

    g = 9.80616
    f0 = 1e-4
    H = Lz # 1000.0 

    c = np.sqrt(g*H) #= 100 m s^(-1), 
    Lx = nx*Dc
    Ly = np.sqrt(3.0)/2.0 *ny*Dc
    kx = 1*2*np.pi/Lx 
    ky = 2*2*np.pi/Ly
    omega = np.sqrt(g*H*(kx**2 + ky**2) + f0**2)

    uEdge = ds.createVariable(
        'uEdge', np.float64, ('Time', 'nEdges', 'nVertLevels',))
    vEdge = ds.createVariable(
        'vEdge', np.float64, ('Time', 'nEdges', 'nVertLevels',))
    normalVelocity = ds.createVariable(
        'normalVelocity', np.float64, ('Time', 'nEdges', 'nVertLevels',))
    normalVelocity[:] = 0.0
    ssh = ds.createVariable(
        'ssh', np.float64, ('Time', 'nCells', ))
    layerThickness = ds.createVariable(
        'layerThickness', np.float64, ('Time', 'nCells', 'nVertLevels',))

    print('velocity_init(ds) cell loop')
    time = 0.0
    for iCell in range(0, nCells):
        x = xCell[iCell]
        y = yCell[iCell]
        for k in range(0, nVertLevels):
            ssh[0, iCell] = omega*np.cos(kx*x + ky*y - omega*time)
            layerThickness[0, iCell, k] = Lz + ssh[0, iCell]

    print('velocity_init(ds) edge loop')

    coef = omega*g/(omega**2 - f0**2)
    for iEdge in range(0, nEdges):
        x = xEdge[iEdge]
        y = yEdge[iEdge]
        cos1 = omega*np.cos(kx*x + ky*y - omega*time)
        sin1 = f0*np.sin(kx*x + ky*y - omega*time)
        for k in range(0, nVertLevels):
            uEdge[0, iEdge, k] = coef*(kx*cos1 - ky*sin1)
            vEdge[0, iEdge, k] = coef*(ky*cos1 + kx*sin1)
            normalVelocity[0, iEdge, k]  = uEdge[0,iEdge,k] * np.cos(angleEdge[iEdge]) + vEdge[0,iEdge,k] * np.sin(angleEdge[iEdge])

    import matplotlib as mpl
    import matplotlib.pyplot as plt
    mpl.rcParams['figure.figsize'] = (6,16) # Large figures
    mpl.rcParams['image.cmap'] = 'Spectral'

    ax=plt.subplot(3,1,1)
    plt.scatter(xCell[:]/1.0e3, yCell[:]/1.0e3, c=ssh[0,:], s=120, marker='h')
    plt.title('ssh')
    plt.colorbar()

    ax=plt.subplot(3,1,2)
    plt.scatter(xEdge[:]/1.0e3, yEdge[:]/1.0e3, c=uEdge[0,:], s=80, marker='d')
    plt.title('u on edge')
    plt.colorbar()

    ax=plt.subplot(3,1,3)
    plt.scatter(xEdge[:]/1.0e3, yEdge[:]/1.0e3, c=vEdge[0,:], s=60, marker='d')
    plt.title('v on edge')
    plt.colorbar()

    plt.savefig('igw_ic.png')

#ax.set_xlim(40,44.5)
    #plt.xlabel('time [days]')
    #plt.ylabel('depth [m]')
    #plt.title('AMOC streamfunction [Sv] 26.5N MPAS-O 01b baseline')
    #plt.colorbar(ticks=np.linspace(-cmax,cmax,9))

# }}}

def coriolis_init(ds):
    # {{{
    print('b4 fAll')
    fAll = 1.0e-4
    print('fEdge')
    fEdge = ds.createVariable('fEdge', np.float64, ('nEdges',))
    fEdge[:] = fAll
    print('fVertex')
    fVertex = ds.createVariable('fVertex', np.float64, ('nVertices',))
    fVertex[:] = fAll
    print('fCell')
    fCell = ds.createVariable('fCell', np.float64, ('nCells',))
    fCell[:] = fAll
# }}}

def others_init(ds):
    # {{{
    surfaceStress = ds.createVariable(
        'surfaceStress', np.float64, ('Time', 'nEdges',))
    surfaceStress[:] = 0.0
    atmosphericPressure = ds.createVariable(
        'atmosphericPressure', np.float64, ('Time', 'nCells',))
    atmosphericPressure[:] = 0.0
    boundaryLayerDepth = ds.createVariable(
        'boundaryLayerDepth', np.float64, ('Time', 'nCells',))
    boundaryLayerDepth[:] = 0.0
# }}}

if __name__ == '__main__':
    # If called as a primary module, run main
    main()

# vim: foldmethod=marker ai ts=4 sts=4 et sw=4 ft=python
