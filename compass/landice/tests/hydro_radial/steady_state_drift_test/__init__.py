from compass.testcase import add_step, run_steps
from compass.landice.tests.hydro_radial import setup_mesh, run_model, visualize


def collect(testcase):
    """
    Update the dictionary of test case properties and add steps

    Parameters
    ----------
    testcase : dict
        A dictionary of properties of this test case, which can be updated
    """
    testcase['description'] = 'hydro-radial steady-state drift test'

    add_step(testcase, setup_mesh, initial_condition='exact')

    add_step(testcase, run_model, cores=4, threads=1)

    add_step(testcase, visualize, input_dir='run_model')


# no configure function is needed


def run(testcase, test_suite, config, logger):
    """
    Run each step of the test case

    Parameters
    ----------
    testcase : dict
        A dictionary of properties of this test case from the ``collect()``
        function

    test_suite : dict
        A dictionary of properties of the test suite

    config : configparser.ConfigParser
        Configuration options for this test case, a combination of the defaults
        for the machine, core and configuration

    logger : logging.Logger
        A logger for output from the test case
    """
    run_steps(testcase, test_suite, config, logger)
