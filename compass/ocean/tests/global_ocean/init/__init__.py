from compass.testcase import run_steps, get_testcase_default
from compass.ocean.tests.global_ocean.init import initial_state
from compass.ocean.tests import global_ocean
from compass.validate import compare_variables
from compass.config import add_config


def collect(mesh_name):
    """
    Get a dictionary of testcase properties

    Parameters
    ----------
    mesh_name : str
        The name of the mesh

    Returns
    -------
    testcase : dict
        A dict of properties of this test case, including its steps
    """
    description = 'Global Ocean {} - Init Test'.format(mesh_name)
    module = __name__

    name = module.split('.')[-1]
    subdir = '{}/{}'.format(mesh_name, name)
    steps = dict()
    step = initial_state.collect(mesh_name, cores=4, min_cores=2,
                                 max_memory=1000, max_disk=1000, threads=1)
    steps[step['name']] = step

    testcase = get_testcase_default(module, description, steps, subdir=subdir)
    testcase['mesh_name'] = mesh_name

    return testcase


def configure(testcase, config):
    """
    Modify the configuration options for this testcase.

    Parameters
    ----------
    testcase : dict
        A dictionary of properties of this testcase from the ``collect()``
        function

    config : configparser.ConfigParser
        Configuration options for this testcase, a combination of the defaults
        for the machine, core and configuration
    """
    global_ocean.configure(testcase, config)
    mesh_name = testcase['mesh_name']
    add_config(config, 'compass.ocean.tests.global_ocean.mesh',
               '{}.cfg'.format(mesh_name.lower()), exception=True)


def run(testcase, test_suite, config, logger):
    """
    Run each step of the testcase

    Parameters
    ----------
    testcase : dict
        A dictionary of properties of this testcase from the ``collect()``
        function

    test_suite : dict
        A dictionary of properties of the test suite

    config : configparser.ConfigParser
        Configuration options for this testcase, a combination of the defaults
        for the machine, core and configuration

    logger : logging.Logger
        A logger for output from the testcase
    """
    work_dir = testcase['work_dir']
    steps = ['initial_state']
    run_steps(testcase, test_suite, config, steps, logger)
    variables = ['temperature', 'salinity', 'layerThickness']
    compare_variables(variables, config, work_dir,
                      filename1='initial_state/initial_state.nc')