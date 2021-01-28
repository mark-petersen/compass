import os
import numpy

from mpas_tools.logging import check_call

from compass.namelist import update
from compass.io import add_input_file


def add_model_as_input(step, config):
    """
    make a link to the model executable and add it to the inputs

    Parameters
    ----------
    step : dict
        A dictionary of properties of this step

    config : configparser.ConfigParser
        Configuration options for the test case
    """
    model = config.get('executables', 'model')
    model_basename = os.path.basename(model)
    add_input_file(step, filename=model_basename,
                   target=os.path.abspath(model))


def run_model(step, config, logger, update_pio=True, partition_graph=True,
              graph_file='graph.info', namelist=None, streams=None):
    """
    Run the model after determining the number of cores

    Parameters
    ----------
    step : dict
        A dictionary of properties of this step

    config : configparser.ConfigParser
        Configuration options for the test case

    logger : logging.Logger
        A logger for output from the step that is calling this function

    update_pio : bool, optional
        Whether to modify the namelist so the number of PIO tasks and the
        stride between them is consistent with the number of nodes and cores
        (one PIO task per node).

    partition_graph : bool, optional
        Whether to partition the domain for the requested number of cores.  If
        so, the partitioning executable is taken from the ``partition`` option
        of the ``[executables]`` config section.

    graph_file : str, optional
        The name of the graph file to partition

    namelist : str, optional
        The name of the namelist file, default is ``namelist.<core>``

    streams : str, optional
        The name of the streams file, default is ``streams.<core>``
    """
    core = step['core']
    cores = step['cores']
    threads = step['threads']
    step_dir = step['work_dir']

    if update_pio:
        update_namelist_pio(config, cores, step_dir)

    if partition_graph:
        partition(cores, config, logger, graph_file=graph_file)

    os.environ['OMP_NUM_THREADS'] = '{}'.format(threads)

    if namelist is None:
        namelist = 'namelist.{}'.format(core)

    if streams is None:
        streams = 'streams.{}'.format(core)

    parallel_executable = config.get('parallel', 'parallel_executable')
    model = config.get('executables', 'model')
    model_basename = os.path.basename(model)

    args = [parallel_executable,
            '-n', '{}'.format(cores),
            './{}'.format(model_basename),
            '-n', namelist,
            '-s', streams]

    check_call(args, logger)


def partition(cores, config, logger, graph_file='graph.info'):
    """
    Partition the domain for the requested number of cores

    Parameters
    ----------
    cores : int
        The number of cores that the model should be run on

    config : configparser.ConfigParser
        Configuration options for the test case, used to get the partitioning
        executable

    logger : logging.Logger
        A logger for output from the step that is calling this function

    graph_file : str, optional
        The name of the graph file to partition

    """
    executable = config.get('parallel', 'partition_executable')
    args = [executable, graph_file, '{}'.format(cores)]
    check_call(args, logger)


def update_namelist_pio(config, cores, step_dir):
    """
    Modify the namelist so the number of PIO tasks and the stride between them
    is consistent with the number of nodes and cores (one PIO task per node).

    Parameters
    ----------
     config : configparser.ConfigParser
        Configuration options for this test case

    cores : int
        The number of cores

    step_dir : str
        The work directory for this step of the test case
    """

    cores_per_node = config.getint('parallel', 'cores_per_node')

    # update PIO tasks based on the machine settings and the available number
    # or cores
    pio_num_iotasks = int(numpy.ceil(cores/cores_per_node))
    pio_stride = cores//pio_num_iotasks
    if pio_stride > cores_per_node:
        raise ValueError('Not enough nodes for the number of cores.  cores: '
                         '{}, cores per node: {}'.format(cores,
                                                         cores_per_node))

    replacements = {'config_pio_num_iotasks': '{}'.format(pio_num_iotasks),
                    'config_pio_stride': '{}'.format(pio_stride)}

    update(replacements=replacements, step_work_dir=step_dir, core='ocean')
