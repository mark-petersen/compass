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


class GoM5BaseMesh(QuasiUniformSphericalMeshStep):
    """
    A step for creating Gulf of Mexico (GoM) 5km  mesh
    """
    def setup(self):
        """
        Add some input files
        """

        inputs = ['coastline_CUSP.geojson',
                  'land_mask_Kamchatka.geojson',
                  'mask_western_Pacific.geojson',
                  'region_Atlantic_Southern_Oceans.geojson',
                  'region_Gulf_central_America.geojson',
                  'region_Gulf_of_Mexico.geojson',
                  'region_Mediterranean_Sea.geojson',
                  'region_txla_shelf.geojson',
                  'region_txla_inner.geojson'
                  ]
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

# pick your case:
        case = 'qu100'
        #case = 'atl60'
        #case = 'atl30'
        #case = 'gom14'
        #case = 'gom5'
        #case = 'gom3'

        if case == 'qu100':
            # Atlantic + southern ocean
            hr_atl_sou = 100.0
            hr_gom_cen = 100.0
            dlon = 1.0
        elif case == 'atl60':
            # Atlantic + southern ocean
            hr_atl_sou = 60.0
            hr_gom_cen = 60.0
            dlon = 0.1
        elif case == 'atl30':
            # Atlantic + southern ocean
            hr_atl_sou = 30.0
            hr_gom_cen = 30.0
            dlon = 0.1
        elif case == 'gom5':
            # Atlantic + southern ocean
            hr_atl_sou = 30.0
            hr_gom_cen = 14.0
            dlon = 0.05

        dlat = dlon
        earth_radius = constants['SHR_CONST_REARTH']
        #print('\nCreating cellWidth on a lat-lon grid of: {0:.2f} x {0:.2f} '
        #      'degrees'.format(dlon, dlat))
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

########################################################################
#
#  Define cell width for low resolution region
#
########################################################################
        # Expand from 1D to 2D. Pick one of these:
        lowRes = 100.0 # in km
        QU1D = lowRes*np.ones(lat.size)
        _, cellWidth = np.meshgrid(lon, QU1D)

        #_plot_cartopy(2, 'low res', cellWidth, '3Wbgy5')
        #plotFrame = 3

########################################################################
#
#  Define cell width for high resolution region
#
########################################################################


#        if case == 'qu100':
#            cellWidth = lowRes
#
#            ax = plt.subplot(6, 2, 1)
#            ax.grid(True)
#            plt.title('Grid cell size [km] versus latitude')
#            plt.legend(loc="upper left")
#
#            plt.savefig('mesh_construction.png', dpi=600)
#
#            return cellWidth, lon, lat
#
#        if case == 'atl60':
#            # Atlantic + southern ocean
#            hr_atl_sou = 60.0
#            fileName = 'region_Atlantic_Southern_Oceans'
#            transitionOffset = 0.0 * km
#            transitionWidth = 1000.0 * km
#            fc = read_feature_collection('{}.geojson'.format(fileName))
#            signedDistance = signed_distance_from_geojson(fc, lon, lat,
#                                                          earth_radius,
#                                                          max_length=0.25)
#            maskSmooth = 0.5 * (1 + np.tanh((transitionOffset - signedDistance) /
#                                      (transitionWidth / 2.)))
#            maskSharp = 0.5 * (1 + np.sign(-signedDistance))
#            fc = read_feature_collection('mask_western_Pacific.geojson')
#            signedDistancePac = signed_distance_from_geojson(fc, lon, lat,
#                                                          earth_radius,
#                                                          max_length=0.25)
#            maskPacific = 0.5 * (1 + np.sign(-signedDistancePac))
#            mask = maskSharp * maskPacific + maskSmooth * (1 - maskPacific)
#            cellWidth = hr_atl_sou * mask + cellWidth * (1 - mask)
#
#            _plot_cartopy(plotFrame, fileName + ' mask', mask, 'Blues')
#            _plot_cartopy(plotFrame + 1, 'cellWidth ', cellWidth, '3Wbgy5')
#            plotFrame += 2
#
#            fileName = 'region_Mediterranean_Sea'
#            transitionWidth = 50*km
#            transitionOffset = 0.0
#            fc = read_feature_collection('{}.geojson'.format(fileName))
#            signedDistance = signed_distance_from_geojson(fc, lon, lat,
#                                                          earth_radius,
#                                                          max_length=0.25)
#            mask = 0.5 * (1 + np.tanh((transitionOffset - signedDistance) /
#                                      (transitionWidth / 2.)))
#            cellWidth = hr_atl_sou * mask + cellWidth * (1 - mask)
#
#            _plot_cartopy(plotFrame, fileName + ' mask', mask, 'Blues')
#            _plot_cartopy(plotFrame + 1, 'cellWidth ', cellWidth, '3Wbgy5')
#            plotFrame += 2
#
#            ax = plt.subplot(6, 2, 1)
#            ax.grid(True)
#            plt.title('Grid cell size [km] versus latitude')
#            plt.legend(loc="upper left")
#
#            plt.savefig('mesh_construction.png', dpi=600)
#
#            return cellWidth, lon, lat
#
#        if case == 'atl30':
        # Atlantic + southern ocean
        fileName = 'region_Atlantic_Southern_Oceans'
        transitionOffset = 0.0 * km
        transitionWidth = 1000.0 * km
        fc = read_feature_collection('{}.geojson'.format(fileName))
        signedDistance = signed_distance_from_geojson(fc, lon, lat,
                                                      earth_radius,
                                                      max_length=0.25)
        maskSmooth = 0.5 * (1 + np.tanh((transitionOffset - signedDistance) /
                                  (transitionWidth / 2.)))
        maskSharp = 0.5 * (1 + np.sign(-signedDistance))
        fc = read_feature_collection('mask_western_Pacific.geojson')
        signedDistancePac = signed_distance_from_geojson(fc, lon, lat,
                                                      earth_radius,
                                                      max_length=0.25)
        maskPacific = 0.5 * (1 + np.sign(-signedDistancePac))
        mask = maskSharp * maskPacific + maskSmooth * (1 - maskPacific)
        cellWidth = hr_atl_sou * mask + cellWidth * (1 - mask)

#        _plot_cartopy(plotFrame, fileName + ' mask', mask, 'Blues')
#        _plot_cartopy(plotFrame + 1, 'cellWidth ', cellWidth, '3Wbgy5')
#        plotFrame += 2

        fileName = 'region_Mediterranean_Sea'
        transitionWidth = 50*km
        transitionOffset = 0.0
        fc = read_feature_collection('{}.geojson'.format(fileName))
        signedDistance = signed_distance_from_geojson(fc, lon, lat,
                                                      earth_radius,
                                                      max_length=0.25)
        mask = 0.5 * (1 + np.tanh((transitionOffset - signedDistance) /
                                  (transitionWidth / 2.)))
        cellWidth = hr_atl_sou * mask + cellWidth * (1 - mask)

#        _plot_cartopy(plotFrame, fileName + ' mask', mask, 'Blues')
#        _plot_cartopy(plotFrame + 1, 'cellWidth ', cellWidth, '3Wbgy5')
#        plotFrame += 2
#
#        ax = plt.subplot(6, 2, 1)
#        ax.grid(True)
#        plt.title('Grid cell size [km] versus latitude')
#        plt.legend(loc="upper left")
#
#        plt.savefig('mesh_construction.png', dpi=600)


#        if case == 'gom14':
#            # Atlantic + southern ocean
#            hr_atl_sou = 30.0
#            fileName = 'region_Atlantic_Southern_Oceans'
#            transitionOffset = 0.0 * km
#            transitionWidth = 1000.0 * km
#            fc = read_feature_collection('{}.geojson'.format(fileName))
#            signedDistance = signed_distance_from_geojson(fc, lon, lat,
#                                                          earth_radius,
#                                                          max_length=0.25)
#            maskSmooth = 0.5 * (1 + np.tanh((transitionOffset - signedDistance) /
#                                      (transitionWidth / 2.)))
#            maskSharp = 0.5 * (1 + np.sign(-signedDistance))
#            fc = read_feature_collection('mask_western_Pacific.geojson')
#            signedDistancePac = signed_distance_from_geojson(fc, lon, lat,
#                                                          earth_radius,
#                                                          max_length=0.25)
#            maskPacific = 0.5 * (1 + np.sign(-signedDistancePac))
#            mask = maskSharp * maskPacific + maskSmooth * (1 - maskPacific)
#            cellWidth = hr_atl_sou * mask + cellWidth * (1 - mask)
#
#            _plot_cartopy(plotFrame, fileName + ' mask', mask, 'Blues')
#            _plot_cartopy(plotFrame + 1, 'cellWidth ', cellWidth, '3Wbgy5')
#            plotFrame += 2
#
#            fileName = 'region_Mediterranean_Sea'
#            transitionWidth = 50*km
#            transitionOffset = 0.0
#            fc = read_feature_collection('{}.geojson'.format(fileName))
#            signedDistance = signed_distance_from_geojson(fc, lon, lat,
#                                                          earth_radius,
#                                                          max_length=0.25)
#            mask = 0.5 * (1 + np.tanh((transitionOffset - signedDistance) /
#                                      (transitionWidth / 2.)))
#            cellWidth = hr_atl_sou * mask + cellWidth * (1 - mask)
#
#            _plot_cartopy(plotFrame, fileName + ' mask', mask, 'Blues')
#            _plot_cartopy(plotFrame + 1, 'cellWidth ', cellWidth, '3Wbgy5')
#            plotFrame += 2
#
#            hr_gom_cen = 14.0
            fileName = 'region_Gulf_central_America'
            transitionOffset = 1000 * km
            transitionWidth = 1000.0 * km
            fc = read_feature_collection('{}.geojson'.format(fileName))
            signedDistance = signed_distance_from_geojson(fc, lon, lat,
                                                          earth_radius,
                                                          max_length=0.25)
            maskSmooth = 0.5 * (1 + np.tanh((transitionOffset - signedDistance) /
                                      (transitionWidth / 2.)))
            maskSharp = 0.5 * (1 + np.sign(-signedDistance))
            mask = maskSharp * maskPacific + maskSmooth * (1 - maskPacific)
            cellWidth = hr_gom_cen * mask + cellWidth * (1 - mask)

            _plot_cartopy(plotFrame, fileName + ' mask', mask, 'Blues')
            _plot_cartopy(plotFrame + 1, 'cellWidth ', cellWidth, '3Wbgy5')
            plotFrame += 2

            ax = plt.subplot(6, 2, 1)
            ax.grid(True)
            plt.title('Grid cell size [km] versus latitude')
            plt.legend(loc="upper left")

            plt.savefig('mesh_construction.png', dpi=600)

            return cellWidth, lon, lat

#        if case == 'gom5':
#            # Atlantic + southern ocean
#            hr_atl_sou = 30.0
#            fileName = 'region_Atlantic_Southern_Oceans'
#            transitionOffset = 0.0 * km
#            transitionWidth = 1000.0 * km
#            fc = read_feature_collection('{}.geojson'.format(fileName))
#            signedDistance = signed_distance_from_geojson(fc, lon, lat,
#                                                          earth_radius,
#                                                          max_length=0.25)
#            maskSmooth = 0.5 * (1 + np.tanh((transitionOffset - signedDistance) /
#                                      (transitionWidth / 2.)))
#            maskSharp = 0.5 * (1 + np.sign(-signedDistance))
#            fc = read_feature_collection('mask_western_Pacific.geojson')
#            signedDistancePac = signed_distance_from_geojson(fc, lon, lat,
#                                                          earth_radius,
#                                                          max_length=0.25)
#            maskPacific = 0.5 * (1 + np.sign(-signedDistancePac))
#            mask = maskSharp * maskPacific + maskSmooth * (1 - maskPacific)
#            cellWidth = hr_atl_sou * mask + cellWidth * (1 - mask)
#
#            _plot_cartopy(plotFrame, fileName + ' mask', mask, 'Blues')
#            _plot_cartopy(plotFrame + 1, 'cellWidth ', cellWidth, '3Wbgy5')
#            plotFrame += 2
#
#            fileName = 'region_Mediterranean_Sea'
#            transitionWidth = 50*km
#            transitionOffset = 0.0
#            fc = read_feature_collection('{}.geojson'.format(fileName))
#            signedDistance = signed_distance_from_geojson(fc, lon, lat,
#                                                          earth_radius,
#                                                          max_length=0.25)
#            mask = 0.5 * (1 + np.tanh((transitionOffset - signedDistance) /
#                                      (transitionWidth / 2.)))
#            cellWidth = hr_atl_sou * mask + cellWidth * (1 - mask)
#
#            _plot_cartopy(plotFrame, fileName + ' mask', mask, 'Blues')
#            _plot_cartopy(plotFrame + 1, 'cellWidth ', cellWidth, '3Wbgy5')
#            plotFrame += 2
#
#            hr_gom_cen = 14.0
#            fileName = 'region_Gulf_central_America'
#            transitionOffset = 1000 * km
#            transitionWidth = 1000.0 * km
#            fc = read_feature_collection('{}.geojson'.format(fileName))
#            signedDistance = signed_distance_from_geojson(fc, lon, lat,
#                                                          earth_radius,
#                                                          max_length=0.25)
#            maskSmooth = 0.5 * (1 + np.tanh((transitionOffset - signedDistance) /
#                                      (transitionWidth / 2.)))
#            maskSharp = 0.5 * (1 + np.sign(-signedDistance))
#            mask = maskSharp * maskPacific + maskSmooth * (1 - maskPacific)
#            cellWidth = hr_gom_cen * mask + cellWidth * (1 - mask)
#
#            _plot_cartopy(plotFrame, fileName + ' mask', mask, 'Blues')
#            _plot_cartopy(plotFrame + 1, 'cellWidth ', cellWidth, '3Wbgy5')
#            plotFrame += 2
#
        if case == 'gom5'||case == 'gom3':
            highRes_txla = 5.0
            fileName = 'region_txla_shelf'
            transitionOffset = 200 * km
            transitionWidth = 500 * km
            fc = read_feature_collection('{}.geojson'.format(fileName))
            signedDistance = signed_distance_from_geojson(fc, lon, lat,
                                                          earth_radius,
                                                          max_length=0.25)

            mask = 0.5 * (1 + np.tanh((transitionOffset - signedDistance) /
                                      (transitionWidth / 2.)))
            cellWidth = highRes_txla * mask + cellWidth * (1 - mask)

#            _plot_cartopy(plotFrame, fileName + ' mask', mask, 'Blues')
#            _plot_cartopy(plotFrame + 1, 'cellWidth ', cellWidth, '3Wbgy5')
#            plotFrame += 2
#
#            ax = plt.subplot(6, 2, 1)
#            ax.grid(True)
#            plt.title('Grid cell size [km] versus latitude')
#            plt.legend(loc="upper left")
#
#            plt.savefig('mesh_construction.png', dpi=600)
#
#            return cellWidth, lon, lat

#            if case == 'gom3':
#                # Atlantic + southern ocean
#                hr_atl_sou = 30.0
#                fileName = 'region_Atlantic_Southern_Oceans'
#                transitionOffset = 0.0 * km
#                transitionWidth = 1000.0 * km
#                fc = read_feature_collection('{}.geojson'.format(fileName))
#                signedDistance = signed_distance_from_geojson(fc, lon, lat,
#                                                              earth_radius,
#                                                              max_length=0.25)
#                maskSmooth = 0.5 * (1 + np.tanh((transitionOffset - signedDistance) /
#                                          (transitionWidth / 2.)))
#                maskSharp = 0.5 * (1 + np.sign(-signedDistance))
#                fc = read_feature_collection('mask_western_Pacific.geojson')
#                signedDistancePac = signed_distance_from_geojson(fc, lon, lat,
#                                                              earth_radius,
#                                                              max_length=0.25)
#                maskPacific = 0.5 * (1 + np.sign(-signedDistancePac))
#                mask = maskSharp * maskPacific + maskSmooth * (1 - maskPacific)
#                cellWidth = hr_atl_sou * mask + cellWidth * (1 - mask)
#
#                _plot_cartopy(plotFrame, fileName + ' mask', mask, 'Blues')
#                _plot_cartopy(plotFrame + 1, 'cellWidth ', cellWidth, '3Wbgy5')
#                plotFrame += 2
#
#                fileName = 'region_Mediterranean_Sea'
#                transitionWidth = 50*km
#                transitionOffset = 0.0
#                fc = read_feature_collection('{}.geojson'.format(fileName))
#                signedDistance = signed_distance_from_geojson(fc, lon, lat,
#                                                              earth_radius,
#                                                              max_length=0.25)
#                mask = 0.5 * (1 + np.tanh((transitionOffset - signedDistance) /
#                                          (transitionWidth / 2.)))
#                cellWidth = hr_atl_sou * mask + cellWidth * (1 - mask)
#
#                _plot_cartopy(plotFrame, fileName + ' mask', mask, 'Blues')
#                _plot_cartopy(plotFrame + 1, 'cellWidth ', cellWidth, '3Wbgy5')
#                plotFrame += 2
#
#                hr_gom_cen = 14.0
#                fileName = 'region_Gulf_central_America'
#                transitionOffset = 1000 * km
#                transitionWidth = 1000.0 * km
#                fc = read_feature_collection('{}.geojson'.format(fileName))
#                signedDistance = signed_distance_from_geojson(fc, lon, lat,
#                                                              earth_radius,
#                                                              max_length=0.25)
#                maskSmooth = 0.5 * (1 + np.tanh((transitionOffset - signedDistance) /
#                                          (transitionWidth / 2.)))
#                maskSharp = 0.5 * (1 + np.sign(-signedDistance))
#                mask = maskSharp * maskPacific + maskSmooth * (1 - maskPacific)
#                cellWidth = hr_gom_cen * mask + cellWidth * (1 - mask)
#
#                _plot_cartopy(plotFrame, fileName + ' mask', mask, 'Blues')
#                _plot_cartopy(plotFrame + 1, 'cellWidth ', cellWidth, '3Wbgy5')
#                plotFrame += 2
#
#                highRes_txla = 5.0
#                fileName = 'region_txla_shelf'
#                transitionOffset = 200 * km
#                transitionWidth = 500 * km
#                fc = read_feature_collection('{}.geojson'.format(fileName))
#                signedDistance = signed_distance_from_geojson(fc, lon, lat,
#                                                              earth_radius,
#                                                              max_length=0.25)
#
#                mask = 0.5 * (1 + np.tanh((transitionOffset - signedDistance) /
#                                          (transitionWidth / 2.)))
#                cellWidth = highRes_txla * mask + cellWidth * (1 - mask)
#
#                _plot_cartopy(plotFrame, fileName + ' mask', mask, 'Blues')
#                _plot_cartopy(plotFrame + 1, 'cellWidth ', cellWidth, '3Wbgy5')
#                plotFrame += 2

            if case == 'gom3':
                highRes_txla_inner = 3.0
                fileName = 'region_txla_inner'
                transitionOffset = 80 * km
                transitionWidth = 100 * km
                fc = read_feature_collection('{}.geojson'.format(fileName))
                signedDistance = signed_distance_from_geojson(fc, lon, lat,
                                                              earth_radius,
                                                              max_length=0.25)

                mask = 0.5 * (1 + np.tanh((transitionOffset - signedDistance) /
                                          (transitionWidth / 2.)))
                cellWidth = highRes_txla_inner * mask + cellWidth * (1 - mask)

#                _plot_cartopy(plotFrame, fileName + ' mask', mask, 'Blues')
#                _plot_cartopy(plotFrame + 1, 'cellWidth ', cellWidth, '3Wbgy5')
#                plotFrame += 2
#
#                ax = plt.subplot(6, 2, 1)
#                ax.grid(True)
#                plt.title('Grid cell size [km] versus latitude')
#                plt.legend(loc="upper left")
#
#                plt.savefig('mesh_construction.png', dpi=600)

        return cellWidth, lon, lat

def _plot_cartopy(nPlot, varName, var, map_name):
    ax = plt.subplot(6, 2, nPlot, projection=ccrs.PlateCarree())
   # ax.set_global()

    im = ax.imshow(var,
                   origin='lower',
                   transform=ccrs.PlateCarree(),
                   cmap=map_name,
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
    ax.set_extent([-120,60,-70,70], ccrs.PlateCarree())
    gl.top_labels = False
    gl.bottom_labels = False
    gl.right_labels = False
    gl.left_labels = False
    plt.colorbar(im, shrink=.9)
    plt.title(varName)

