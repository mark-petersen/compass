from compass.testcase import run_steps, get_testcase_default
from compass.ocean.tests.baroclinic_channel import initial_state, forward
from compass.ocean.tests import baroclinic_channel
from compass.validate import compare_variables


def collect(resolution):
    """
    Get a dictionary of testcase properties

    Parameters
    ----------
    resolution : {'10km'}
        The resolution of the mesh

    Returns
    -------
    testcase : dict
        A dict of properties of this test case, including its steps
    """
    description = 'baroclinic channel {} restart test'.format(resolution)
    module = __name__

    name = module.split('.')[-1]
    subdir = '{}/{}'.format(resolution, name)
    steps = dict()
    step = initial_state.collect(resolution)
    steps[step['name']] = step

    step = forward.collect(resolution, cores=4, threads=1,
                           testcase_module=module,
                           namelist_file='namelist.full',
                           streams_file='streams.full')
    step['name'] = 'full_run'
    step['subdir'] = step['name']
    steps[step['name']] = step

    step = forward.collect(resolution, cores=4, threads=1,
                           testcase_module=module,
                           namelist_file='namelist.restart',
                           streams_file='streams.restart')
    step['name'] = 'restart_run'
    step['subdir'] = step['name']
    steps[step['name']] = step

    testcase = get_testcase_default(module, description, steps, subdir=subdir)
    testcase['resolution'] = resolution

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
    baroclinic_channel.configure(testcase, config)


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
    steps = ['initial_state', 'full_run', 'restart_run']
    run_steps(testcase, test_suite, config, steps, logger)
    variables = ['temperature', 'salinity', 'layerThickness', 'normalVelocity']
    compare_variables(variables, config, work_dir=testcase['work_dir'],
                      filename1='full_run/output.nc',
                      filename2='restart_run/output.nc')
