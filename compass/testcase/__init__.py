import os
import sys
import stat
from jinja2 import Template
from importlib import resources

from compass import logging
from compass.parallel import get_available_cores_and_nodes


def get_step_default(module):
    """
    Set up a default dictionary describing the step in the given module.  The
    dictionary contains the full name of the python module for the step, the
    name of the step (the name of the python file without the ``.py``
    extension), the subdirectory for the step (the same as the ``name``),
    the names of the ``setup()`` and ``run()`` functions within the module,
    and empty lists of ``inputs`` and ``outputs``, to be filled with the
    files required to run the step or produced by the step, respectively.

    Parameters
    ----------
    module : str
        The full name of the python module for the step, usually supplied from
        ``__name__``

    Returns
    -------
    step : dict
        A dictionary with the default information about the step, most of which
        can be modified as appropriate

    """
    name = module.split('.')[-1]
    step = {'module': module,
            'name': name,
            'subdir': name,
            'setup': 'setup',
            'run': 'run',
            'inputs': [],
            'outputs': []}
    return step


def get_testcase_default(module, description, steps, subdir=None):
    """
    Set up a default dictionary describing the testcase in the given module.
    The dictionary contains the full name of the python module for the testcase,
    the name of the testcase (the final part of the full module name), the
    subdirectory for the testcase (the same as the ``name`` if not supplied),
    the names of the ``configure()`` and ``run()`` functions within the module,
    and empty lists of ``inputs`` and ``outputs``, the ``core`` and
    ``configuration`` of the testcase (the parsed from the full module name),
    the description of the testcase provided, and the dictionary of steps.

    Parameters
    ----------
    module : str
        The full name of the python module for the testcase, usually supplied
        from ``__name__``

    description : str
        A description of the testcase

    steps : dict
        A dictionary of steps within the testcase, with the names of each step
        as keys and a dictionary of information on the step as values.  Each
        step's dictionary must contain, at a minimum, the information added by
        :py:func:`compass.testcase.get_default()`

    subdir : str, optional
        The subdirectory for the testcase, which defaults to the name of the
        testcase (parsed from the module name).  If a testcase supports
        various parameter values, such as various resolutions, it may be
        useful to supply a subdirectory so that the location of each variant of
        the testcase is placed in a unique working directory

    Returns
    -------
    testcase : dict
        A dictionary with the default information about the testcase, most of
        which can be modified as appropriate
    """
    name = module.split('.')[-1]
    core = module.split('.')[1]
    configuration = module.split('.')[3]
    if subdir is None:
        subdir = name
    path = os.path.join(core, configuration, subdir)
    for step in steps.values():
        step['testcase'] = name
    if hasattr(sys.modules[module], 'configure'):
        configure = 'configure'
    else:
        configure = None
    testcase = {'module': module,
                'name': name,
                'path': path,
                'core': core,
                'configuration': configuration,
                'subdir': subdir,
                'description': description,
                'steps': steps,
                'configure': configure,
                'run': 'run'}
    return testcase


def run_steps(testcase, test_suite, config, steps, logger):
    """
    Run the requested steps of a testcase

    Parameters
    ----------
    testcase : dict
        The dictionary describing the testcase with info from
        :py:func:`compass.testcase.get_default()` and any additional information
        added when collecting and setting up the testcase.

    test_suite : dict
        A dictionary of properties of the test suite

    config : configparser.ConfigParser
        Configuration options for this testcase

    steps : list
        A list of the names of the steps from ``testcase['steps']`` to run

    logger : logging.Logger
        A logger for output from the testcase
    """
    cwd = os.getcwd()
    for step_name in steps:
        step = testcase['steps'][step_name]

        if 'cores' in step:
            available_cores, _ = get_available_cores_and_nodes(config)
            step['cores'] = min(step['cores'], available_cores)
        else:
            logger.warn('Core count not specified for step {}. Default is 1 '
                        'core.'.format(step_name))
            step['cores'] = 1
        if 'min_cores' in step:
            if step['cores'] < step['min_cores']:
                raise ValueError(
                    'Available cores for {} is below the minimum of {}'
                    ''.format(step['cores'], step['min_cores']))

        logger.info(' * Running {}'.format(step_name))

        if 'log_filename' in testcase:
            step_logger = logger
            handler = None
            old_stdout = None
            old_stderr = None
        else:
            log_filename = '{}/{}.log'.format(cwd, step_name)
            test_name = step['path'].replace('/', '_')
            step_logger, handler, old_stdout, old_stderr = logging.start(
                test_name=test_name, log_filename=log_filename)
            step['log_filename'] = log_filename

        run = getattr(sys.modules[step['module']], step['run'])
        os.chdir(step['work_dir'])

        try:
            run(step, test_suite, config, step_logger)
        except BaseException:
            logger.info('     Failed')
            raise

        if 'log_filename' not in testcase:
            logging.stop(step_logger, handler, old_stdout, old_stderr)

        logger.info('     Complete')

    os.chdir(cwd)


def generate_run(step, template_name):
    """
    Generate a ``run.py`` script for the given testcase or step.

    Parameters
    ----------
    step : dict
        The dictionary of information about the step, used to fill in the
        script template

    template_name : str
        The name of the template file to use to create the run script
    """
    step_dir = step['work_dir']

    template = Template(resources.read_text('compass.testcase', template_name))
    script = template.render(step=step)

    run_filename = os.path.join(step_dir, 'run.py')
    with open(run_filename, 'w') as handle:
        handle.write(script)

    # make sure it has execute permission
    st = os.stat(run_filename)
    os.chmod(run_filename, st.st_mode | stat.S_IEXEC)
