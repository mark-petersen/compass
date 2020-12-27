import os

from mpas_tools.ocean import build_spherical_mesh

from compass.testcase import get_step_default
from compass.io import symlink, download
from compass import namelist, streams
from compass.model import partition, run_model
from compass.parallel import update_namelist_pio
from compass.ocean.tests.global_ocean.cull import cull_mesh
from compass.ocean.vertical import generate_grid, write_grid
from compass.ocean.plot import plot_vertical_grid, plot_initial_state
from compass.ocean.tests.global_ocean.mesh import build_cell_width_lat_lon


def collect(mesh_name, cores, min_cores=None, max_memory=1000,
            max_disk=1000, threads=1):
    """
    Get a dictionary of step properties

    Parameters
    ----------
    mesh_name : str
        The name of the mesh

    cores : int
        The number of cores to run on in init runs. If this many cores are
        available on the machine or batch job, the task will run on that
        number. If fewer are available (but no fewer than min_cores), the job
        will run on all available cores instead.

    min_cores : int, optional
        The minimum allowed cores.  If that number of cores are not available
        on the machine or in the batch job, the run will fail.  By default,
        ``min_cores = cores``

    max_memory : int, optional
        The maximum amount of memory (in MB) this step is allowed to use

    max_disk : int, optional
        The maximum amount of disk space  (in MB) this step is allowed to use

    threads : int, optional
        The number of threads to run with during init runs

    Returns
    -------
    step : dict
        A dictionary of properties of this step
    """
    step = get_step_default(__name__)
    step['mesh_name'] = mesh_name
    step['cores'] = cores
    step['max_memory'] = max_memory
    step['max_disk'] = max_disk
    if min_cores is None:
        min_cores = cores
    step['min_cores'] = min_cores
    step['threads'] = threads

    return step


def setup(step, config):
    """
    Set up the test case in the work directory, including downloading any
    dependencies

    Parameters
    ----------
    step : dict
        A dictionary of properties of this step from the ``collect()`` function

    config : configparser.ConfigParser
        Configuration options for this testcase, a combination of the defaults
        for the machine, core, configuration and testcase
    """
    mesh_name = step['mesh_name']
    step_dir = step['work_dir']

    # generate the namelist, replacing a few default options
    replacements = dict()

    replacements.update(namelist.parse_replacements(
        'compass.ocean.tests.global_ocean.init', 'namelist.init'))

    namelist.generate(config=config, replacements=replacements,
                      step_work_dir=step_dir, core='ocean', mode='init')

    # generate the streams file
    streams_data = streams.read('compass.ocean.tests.global_ocean.init',
                                'streams.init')

    streams.generate(config=config, tree=streams_data, step_work_dir=step_dir,
                     core='ocean', mode='init')

    initial_condition_database = config.get('paths',
                                            'initial_condition_database')

    inputs = []
    outputs = []

    filenames = {
        'temperature.nc': 'PTemp.Jan_p3.filled.mpas100levs.160127.nc',
        'salinity.nc':
            'Salt.Jan_p3.noBlackCaspian.filled.mpas100levs.160127.nc',
        'wind_stress.nc':
            'windStress.ncep_1958-2000avg.interp3600x2431.151106.nc',
        'topography.nc': 'ETOPO2v2c_f4_151106.nc',
        'swData.nc': 'chlorophyllA_monthly_averages_1deg.151201.nc'}

    for local_filename, remote_filename in filenames.items():
        # download an input file if it's not already in the initial condition
        # database
        filename = download(
            file_name=remote_filename,
            url='https://web.lcrc.anl.gov/public/e3sm/mpas_standalonedata/'
                'mpas-ocean/initial_condition_database',
            config=config, dest_path=initial_condition_database)

        inputs.append(filename)

        symlink(filename, os.path.join(step_dir, local_filename))

    # make a link to the ocean_model executable
    symlink(os.path.abspath(config.get('executables', 'model')),
            os.path.join(step_dir, 'ocean_model'))

    for file in ['initial_state.nc', 'culled_graph.info',
                 'init_mode_forcing_data.nc']:
        outputs.append(os.path.join(step_dir, file))

    step['inputs'] = inputs
    step['outputs'] = outputs


def run(step, test_suite, config, logger):
    """
    Run this step of the testcase

    Parameters
    ----------
    step : dict
        A dictionary of properties of this step from the ``collect()``
        function, with modifications from the ``setup()`` function.

    test_suite : dict
        A dictionary of properties of the test suite

    config : configparser.ConfigParser
        Configuration options for this testcase, a combination of the defaults
        for the machine, core and configuration

    logger : logging.Logger
        A logger for output from the step
    """
    cores = step['cores']
    threads = step['threads']
    step_dir = step['work_dir']
    mesh_name = step['mesh_name']

    # create the base mesh
    cellWidth, lon, lat = build_cell_width_lat_lon(mesh_name)
    build_spherical_mesh(cellWidth, lon, lat, out_filename='base_mesh.nc')

    cull_mesh(with_critical_passages=True)

    interfaces = generate_grid(config=config)
    write_grid(interfaces=interfaces, out_filename='vertical_grid.nc')
    plot_vertical_grid(grid_filename='vertical_grid.nc', config=config,
                       out_filename='vertical_grid.png')

    update_namelist_pio(config, cores, step_dir)
    partition(cores, logger, graph_file='culled_graph.info')

    run_model(config, core='ocean', core_count=cores, logger=logger,
              threads=threads)

    plot_initial_state(input_file_name='initial_state.nc',
                       output_file_name='initial_state.png')