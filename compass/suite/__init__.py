import argparse
import sys
import os
from importlib import resources
import pickle
import configparser
import stat
from jinja2 import Template

from compass.setup import setup_cases
from compass.io import symlink
from compass import logging


def setup_suite(core, suite_name, config_file=None, machine=None, work_dir=None,
                baseline_dir=None):

    if config_file is None and machine is None:
        raise ValueError('At least one of config_file and machine is needed.')

    text = resources.read_text('compass.{}.suites'.format(core),
                               '{}.txt'.format(suite_name))
    tests = [test.strip() for test in text.split('\n') if len(test.strip()) > 0]

    if work_dir is None:
        work_dir = os.getcwd()
    work_dir = os.path.abspath(work_dir)

    testcases = setup_cases(tests, config_file=config_file, machine=machine,
                            work_dir=work_dir, baseline_dir=baseline_dir)

    # if compass/__init__.py exists, we're using a local version of the compass
    # package and we'll want to link to that in the tests and steps
    compass_path = os.path.join(os.getcwd(), 'compass')
    if os.path.exists(os.path.join(compass_path, '__init__.py')):
        symlink(compass_path, os.path.join(work_dir, 'compass'))

    test_suite = {'name': suite_name,
                  'testcases': testcases,
                  'work_dir': work_dir}

    # pickle the test or step dictionary for use at runtime
    pickle_file = os.path.join(test_suite['work_dir'],
                               '{}.pickle'.format(suite_name))
    with open(pickle_file, 'wb') as handle:
        pickle.dump(test_suite, handle, protocol=pickle.HIGHEST_PROTOCOL)

    template = Template(resources.read_text('compass.suite', 'suite.template'))
    script = template.render(suite_name=suite_name)

    run_filename = os.path.join(work_dir, '{}.py'.format(suite_name))
    with open(run_filename, 'w') as handle:
        handle.write(script)

    # make sure it has execute permission
    st = os.stat(run_filename)
    os.chmod(run_filename, st.st_mode | stat.S_IEXEC)


def clean_suite(core, test_suite, config_file=None, machine=None, work_dir=None,
                baseline_dir=None):
    pass


def run_suite(suite_name):
    with open('{}.pickle'.format(suite_name), 'rb') as handle:
        test_suite = pickle.load(handle)

    # start logging to stdout/stderr
    logger, handler, old_stdout, old_stderr = logging.start(
        test_name=suite_name, log_filename=None)

    os.environ['PYTHONUNBUFFERED'] = '1'

    try:
        os.makedirs('case_outputs')
    except OSError:
        pass

    success = True
    cwd = os.getcwd()
    for test_name in test_suite['testcases']:
        testcase = test_suite['testcases'][test_name]

        logger.info(' * Running {}'.format(test_name))
        logger.info('           {}'.format(testcase['description']))

        test_name = testcase['path'].replace('/', '_')
        log_filename = '{}/case_outputs/{}.log'.format(cwd, test_name)
        test_logger, test_handler, test_old_stdout, test_old_stderr = \
            logging.start(test_name=test_name, log_filename=log_filename)
        testcase['log_filename'] = log_filename

        os.chdir(testcase['work_dir'])

        config = configparser.ConfigParser(
            interpolation=configparser.ExtendedInterpolation())
        config.read(testcase['config'])

        run = getattr(sys.modules[testcase['module']], testcase['run'])
        try:
            run(testcase, test_suite, config, test_logger)
            logger.info('    PASS')
        except BaseException:
            test_logger.exception('Exception raised')
            logger.error('   FAIL    For more information, see:')
            logger.error('           case_outputs/{}.log'.format(test_name))

        logging.stop(test_logger, test_handler, test_old_stdout,
                     test_old_stderr)

        logger.info('')

    os.chdir(cwd)

    logging.stop(logger, handler, old_stdout, old_stderr)

    if not success:
        raise ValueError('One or more tests failed, see above.')


def main():
    parser = argparse.ArgumentParser(
        description='Set up a regression test suite')
    parser.add_argument("-c", "--core", dest="core",
                        help="The core for the test suite",
                        metavar="CORE", required=True)
    parser.add_argument("-t", "--test_suite", dest="test_suite",
                        help="Path to file containing a test suite to setup",
                        metavar="FILE", required=True)
    parser.add_argument("-f", "--config_file", dest="config_file",
                        help="Configuration file for test case setup",
                        metavar="FILE")
    parser.add_argument("-s", "--setup", dest="setup",
                        help="Option to determine if regression suite should "
                             "be setup or not.", action="store_true")
    parser.add_argument("--clean", dest="clean",
                        help="Option to determine if regression suite should "
                             "be cleaned or not.", action="store_true")
    parser.add_argument("-v", "--verbose", dest="verbose",
                        help="Use verbose output from setup_testcase.py",
                        action="store_true")
    parser.add_argument("-m", "--machine", dest="machine",
                        help="The name of the machine for loading machine-"
                             "related config options", metavar="MACH")
    parser.add_argument("-b", "--baseline_dir", dest="baseline_dir",
                        help="Location of baseslines that can be compared to",
                        metavar="PATH")
    parser.add_argument("-w", "--work_dir", dest="work_dir",
                        help="If set, script will setup the test suite in "
                        "work_dir rather in this script's location.",
                        metavar="PATH")
    args = parser.parse_args(sys.argv[2:])

    if not args.clean and not args.setup:
        raise ValueError('One of -s/--setup or -c/--cleanup must be specified')

    if args.clean:
        clean_suite(core=args.core, test_suite=args.test_suite,
                    config_file=args.config_file, machine=args.machine,
                    work_dir=args.work_dir, baseline_dir=args.baseline_dir)

    if args.setup:
        setup_suite(core=args.core, suite_name=args.test_suite,
                    config_file=args.config_file, machine=args.machine,
                    work_dir=args.work_dir, baseline_dir=args.baseline_dir)