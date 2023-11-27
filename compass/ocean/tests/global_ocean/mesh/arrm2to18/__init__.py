import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import mpas_tools.mesh.creation.mesh_definition_tools as mdt
import numpy as np
from geometric_features import read_feature_collection
from mpas_tools.cime.constants import constants
from mpas_tools.mesh.creation.signed_distance import (
    mask_from_geojson,
    signed_distance_from_geojson,
)
from mpas_tools.viz.colormaps import register_sci_viz_colormaps

from compass.mesh import QuasiUniformSphericalMeshStep


class ARRM2to18BaseMesh(QuasiUniformSphericalMeshStep):
    """
    A step for creating ARRM2to18 mesh
    """
    def setup(self):
        """
        Add some input files
        """

        inputs = ['coastline_CUSP.geojson',
                  'region_CUSP_north.geojson',
                  'region_Kuroshio_north.geojson',
                  'land_mask_Kamchatka.geojson',
                  'land_mask_Mexico.geojson',
                  'namelist.split_explicit',
                  'region_Arctic_Ocean.geojson',
                  'region_Bering_Sea.geojson',
                  'region_Mediterranean_Sea.geojson',
                  'region_Kuroshio.geojson',
                  'region_Gulf_of_Mexico.geojson',
                  'region_Gulf_Stream_extension.geojson']
        for filename in inputs:
            self.add_input_file(filename=filename,
                                package=self.__module__)

        super().setup()

    def build_cell_width_lat_lon(self):
        """
        Create cell width array for this mesh on a regular latitude-longitude
        grid

        Returns
        -------
        cellWidth : numpy.array
            m x n array of cell width in km

        lon : numpy.array
            longitude in degrees (length n and between -180 and 180)

        lat : numpy.array
            longitude in degrees (length m and between -90 and 90)
        """

# use 1 degree to go faster
        dlon = 1.0
        #dlon = 0.1
        dlat = dlon
        earth_radius = constants['SHR_CONST_REARTH']
        print('\nCreating cellWidth on a lat-lon grid of: {0:.2f} x {0:.2f} '
              'degrees'.format(dlon, dlat))
        print('This can be set higher for faster test generation\n')
        nlon = int(360. / dlon) + 1
        nlat = int(180. / dlat) + 1
        lon = np.linspace(-180., 180., nlon)
        lat = np.linspace(-90., 90., nlat)
        km = 1.0e3

        print('plotting ...')
        plt.switch_backend('Agg')
        fig = plt.figure()
        plt.clf()
        fig.set_size_inches(10.0, 14.0)
        register_sci_viz_colormaps()

        # global settings for regionally-refined mesh
        highRes = 3.0  # [km]
        lowRes = 18.0  # [km]
        midRes =  6.0  # [km]
        RRShighRes = 10.0
        #transitionOffsetGlobal = 200.0 * km
        transitionOffsetGlobal = 0.0 * km
        transitionWidthGlobal = 2000.0 * km

        # create background tanh for high-res region
        latMid = 45.0
        latTransitionWidth = 5.0
        # create 1D array as a function of latitude
        midToHighResTanh = 0.5 + 0.5*np.tanh( (lat - latMid) / latTransitionWidth )
        # Expand from 1D to 2D
        _, midToHighResMask = np.meshgrid(lon, midToHighResTanh)

        #highRes = 2.0  # [km]
        #lowRes = 18.0  # [km]
        #RRShighRes = 6.0
        #EC60to30Narrow = mdt.EC_CellWidthVsLat(lat, latPosEq=8.0,
        #                                       latWidthEq=3.0)

        QU = lowRes*np.ones(lat.size)
        RRS6to18 = mdt.RRS_CellWidthVsLat(lat, lowRes, RRShighRes)
        RRS1to18 = mdt.RRS_CellWidthVsLat(lat, lowRes, highRes)
        # Expand from 1D to 2D
        _, cellWidthLowRes = np.meshgrid(lon, QU)

# start the high res mask as zeros, and add ones for the high res region
        latMid = 47.0
        latTransitionWidth = 5.0
        # create 1D array as a function of latitude
        highResTanh = 0.5 + 0.5*np.tanh( (lat - latMid) / latTransitionWidth )
        ###_, highResMask = np.meshgrid(lon, highResTanh)
        _, highResMask = np.meshgrid(lon, np.zeros(lat.size))
        _, onesMask = np.meshgrid(lon, np.ones(lat.size))
        plotFrame = 1

        fileName = 'region_CUSP_north'
        transitionWidth = 800 * km
        transitionOffset = 400.0 * km
        print('trying to read' + '{}.geojson'.format(fileName) )
        fc = read_feature_collection('{}.geojson'.format(fileName))
        signedDistance = signed_distance_from_geojson(fc, lon, lat,
                                                      earth_radius,
                                                      max_length=0.25)
        mask = 0.5 * (1 + np.tanh((transitionOffset - signedDistance) /
                                  (transitionWidth / 2.)))
        midToHighResMask = np.maximum(midToHighResMask, mask)

        fileName = 'region_Kuroshio_north'
        transitionWidth = 800 * km
        transitionOffset = 400 * km
        print('trying to read' + '{}.geojson'.format(fileName) )
        fc = read_feature_collection('{}.geojson'.format(fileName))
        signedDistance = signed_distance_from_geojson(fc, lon, lat,
                                                      earth_radius,
                                                      max_length=0.25)
        mask = 0.5 * (1 + np.tanh((transitionOffset - signedDistance) /
                                  (transitionWidth / 2.)))
        midToHighResMask = np.maximum(midToHighResMask, mask)
        cellWidthHighRes = highRes*midToHighResMask + midRes*(1-midToHighResMask)

        fileNames = [
                  'region_Arctic_Ocean',
                  'region_Bering_Sea',
                  'region_Kuroshio',
                  'region_Gulf_Stream_extension']
        transitionOffset = transitionOffsetGlobal
        transitionWidth = transitionWidthGlobal
        signedDistance = 1.0e12*onesMask 
        for fileName in fileNames:
            fc = read_feature_collection('{}.geojson'.format(fileName))
            signedDistanceSingle = signed_distance_from_geojson(fc, lon, lat,
                                                          earth_radius,
                                                          max_length=0.25)
            signedDistance = np.minimum(signedDistance, signedDistanceSingle)
        mask = 0.5 * (1 + np.tanh((transitionOffset - signedDistance) /
                                  (transitionWidth / 2.)))
        highResMask = np.minimum( np.maximum(signedDistance, -transitionWidth), transitionWidth)
        ###highResMask = np.maximum(highResMask, mask)
            #_plot_cartopy(plotFrame, fileName + ' mask', mask, 'Blues')
            #_plot_cartopy(plotFrame + 1, 'highResMask', highResMask, '3Wbgy5')
            #plotFrame += 2

        fileName = 'coastline_CUSP'
        transitionWidth = transitionWidthGlobal
        transitionOffset = 1200.0 * km
        fc = read_feature_collection('{}.geojson'.format(fileName))
        signedDistance = signed_distance_from_geojson(fc, lon, lat,
                                                      earth_radius,
                                                      max_length=0.25)
        mask = 0.5 * (1 + np.tanh((transitionOffset - signedDistance) /
                                  (transitionWidth / 2.)))
        ###highResMask = np.maximum(highResMask, mask)

        ###cellWidth = cellWidthHighRes * highResMask + cellWidthLowRes * (1 - highResMask)
        cellWidth = highResMask

        fileName = 'region_Mediterranean_Sea'
        transitionWidth = 0.000001
        transitionOffset = 0.0
        MediterraneanRes = 6.0
        fc = read_feature_collection('{}.geojson'.format(fileName))
        signedDistance = signed_distance_from_geojson(fc, lon, lat,
                                                      earth_radius,
                                                      max_length=0.25)
        mask = 0.5 * (1 + np.tanh((transitionOffset - signedDistance) /
                                  (transitionWidth / 2.)))
        ###cellWidth = MediterraneanRes * mask + cellWidth * (1 - mask)
        _plot_cartopy(plotFrame, fileName + ' mask', mask, 'Blues')
        _plot_cartopy(plotFrame + 1, 'cellWidth ', cellWidth, '3Wbgy5')
        plotFrame += 2


        #ax = plt.subplot(6, 2, 1)
        #ax.plot(lat, RRS6to18, label='original RRS')
        #ax.plot(lat, QU, label='original QU')
# mrp del soon        ax.plot(lat, EC60to30Narrow, label='narrow EC60to30')
        #ax.grid(True)
        plt.title('Grid cell size [km] versus latitude')
        plt.legend(loc="upper left")

        plt.savefig('mesh_construction.png', dpi=300)

        return cellWidth, lon, lat


def _plot_cartopy(nPlot, varName, var, map_name):
    ax = plt.subplot(6, 2, nPlot, projection=ccrs.PlateCarree())
    ax.set_global()

    im = ax.imshow(var,
                   origin='lower',
                   transform=ccrs.PlateCarree(),
                   extent=[-180, 180, -90, 90], cmap=map_name,
                   zorder=0)
    ax.add_feature(cfeature.LAND, edgecolor='black', zorder=1)
    gl = ax.gridlines(
        crs=ccrs.PlateCarree(),
        draw_labels=True,
        linewidth=1,
        color='gray',
        alpha=0.5,
        linestyle='-', zorder=2)
    ax.coastlines()
    gl.top_labels = False
    gl.bottom_labels = False
    gl.right_labels = False
    gl.left_labels = False
    plt.colorbar(im, shrink=.9)
    plt.title(varName)
