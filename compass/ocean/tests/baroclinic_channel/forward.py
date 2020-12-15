import os
import numpy

from compass.testcase import get_step_default
from compass.io import symlink
from compass import namelist, streams
from compass.model import partition, run_model


def collect(resolution, cores, min_cores=None, max_memory=1000,
            max_disk=1000, threads=1, testcase_module=None,
            namelist_file=None, streams_file=None, nu=None):
    """
    Get a dictionary of step properties

    Parameters
    ----------
    resolution : {'1km', '4km', '10km'}
        The name of the resolution to run at

    cores : int
        The number of cores to run on in forward runs. If this many cores are
        available on the machine or batch job, the task will run on that number.
        If fewer are available (but no fewer than min_cores), the job will
        run on all available cores instead.

    min_cores : int, optional
        The minimum allowed cores.  If that number of cores are not available on
        the machine or in the batch job, the run will fail.  By default,
        ``min_cores = cores``

    max_memory : int, optional
        The maximum amount of memory (in MB) this step is allowed to use

    max_disk : int, optional
        The maximum amount of disk space  (in MB) this step is allowed to use

    threads : int, optional
        The number of threads to run with during forward runs

    testcase_module : str, optional
        The module for the testcase

    namelist_file : str, optional
        The name of a namelist file in the testcase package directory

    streams_file : str, optional
        The name of a streams file in the testcase package directory

    nu : float, optional
        The viscosity for this step

    Returns
    -------
    step : dict
        A dictionary of properties of this step
    """
    step = get_step_default(__name__)
    step['resolution'] = resolution
    step['cores'] = cores
    step['max_memory'] = max_memory
    step['max_disk'] = max_disk
    if min_cores is None:
        min_cores = cores
    step['min_cores'] = min_cores
    step['threads'] = threads
    if testcase_module is not None:
        step['testcase_module'] = testcase_module
    else:
        if namelist_file is not None or streams_file is not None:
            raise ValueError('You must supply a testcase module for the '
                             'namelist and/or streams file')
    if namelist_file is not None:
        step['namelist'] = namelist_file
    if streams_file is not None:
        step['streams'] = streams_file

    if nu is not None:
        step['nu'] = nu

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
    resolution = step['resolution']
    step_dir = step['work_dir']

    # generate the namelist, replacing a few default options
    replacements = dict()

    for namelist_file in ['namelist.forward',
                          'namelist.{}.forward'.format(resolution)]:
        replacements.update(namelist.parse_replacements(
            'compass.ocean.tests.baroclinic_channel', namelist_file))

    if 'testcase_module' in step:
        testcase_module = step['testcase_module']
    else:
        testcase_module = None

    # see if there's one for the testcase itself
    if 'namelist' in step:
        replacements.update(namelist.parse_replacements(
            testcase_module, step['namelist']))

    if 'nu' in step:
        # update the viscosity to the requested value
        replacements.update({'config_mom_del2': '{}'.format(step['nu'])})

    namelist.generate(config=config, replacements=replacements,
                      step_work_dir=step_dir, core='ocean', mode='forward')

    # generate the streams file
    streams_data = streams.read('compass.ocean.tests.baroclinic_channel',
                                'streams.forward')

    # see if there's one for the testcase itself
    if 'streams' in step:
        streams_data = streams.read(testcase_module, step['streams'],
                                    tree=streams_data)

    streams.generate(config=config, tree=streams_data, step_work_dir=step_dir,
                     core='ocean', mode='forward')

    # make a link to the ocean_model executable
    symlink(os.path.abspath(config.get('executables', 'model')),
            os.path.join(step_dir, 'ocean_model'))

    inputs = []
    outputs = []

    links = {'../initial_state/ocean.nc': 'init.nc',
             '../initial_state/culled_graph.info': 'graph.info'}
    for target, link in links.items():
        symlink(target, os.path.join(step_dir, link))
        inputs.append(os.path.abspath(os.path.join(step_dir, target)))

    for file in ['output.nc']:
        outputs.append(os.path.join(step_dir, file))

    step['inputs'] = inputs
    step['outputs'] = outputs


def run(step, test_suite, config, logger):
    """
    Run this step of the testcase

    Parameters
    ----------
    step : dict
        A dictionary of properties of this step from the ``collect()`` function,
        with modifications from the ``setup()`` function.

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
    _update_namelist_pio(config, cores, step_dir)
    partition(cores, logger)
    run_model(config, core='ocean', core_count=cores, logger=logger,
              threads=threads)


def _update_namelist_pio(config, cores, step_dir):
    """
    Determine an appropriate number of cores for MPAS-Ocean to run with, based
    on the resolution and the available node and core counts.

    Modify the namelist so the number of PIO tasks and the stride between them
    is consistent with the number of nodes and cores (one PIO task per node).

    Parameters
    ----------
     config : configparser.ConfigParser
        Configuration options for this testcase

    cores : int
        The number of cores

    step_dir : str
        The work directory for this step of the testcase

    Returns
    -------
    core_count : int
        The number of cores to use in this step of the testcase
    """

    cores_per_node = config.getint('parallel', 'cores_per_node')

    # update PIO tasks based on the machine settings and the available number
    # or cores
    pio_num_iotasks = int(numpy.ceil(cores/cores_per_node))
    pio_stride = min(cores_per_node, cores)

    replacements = {'config_pio_num_iotasks': '{}'.format(pio_num_iotasks),
                    'config_pio_stride': '{}'.format(pio_stride)}

    namelist.update(replacements=replacements, step_work_dir=step_dir,
                    core='ocean')