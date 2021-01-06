from compass.ocean.tests.global_ocean import mesh, init, performance_test, \
    restart_test, decomp_test, threads_test, analysis_test, daily_output_test
from compass.config import add_config
from compass.ocean.tests.global_ocean.mesh.mesh import get_mesh_package
from compass.ocean.tests.global_ocean.init import add_descriptions_to_config


def collect():
    """
    Get a list of testcases in this configuration

    Returns
    -------
    testcases : list
        A list of tests within this configuration
    """
    testcases = list()

    # we do a lot of tests for QU240/QU240wISC
    for mesh_name, with_ice_shelf_cavities in [('QU240', False),
                                               ('QUwISC240', True)]:
        testcases.append(mesh.collect(mesh_name, with_ice_shelf_cavities))

        for initial_condition in ['PHC', 'EN4_1900']:
            for with_bgc in [False, True]:
                testcases.append(init.collect(
                    mesh_name, with_ice_shelf_cavities, initial_condition,
                    with_bgc))
                for test in [performance_test, restart_test, decomp_test,
                             threads_test, analysis_test, daily_output_test]:
                    for time_integrator in ['split_explicit', 'RK4']:
                        testcases.append(test.collect(
                            mesh_name, with_ice_shelf_cavities,
                            initial_condition, with_bgc, time_integrator))

    # for other meshes, we do fewer tests
    for mesh_name, with_ice_shelf_cavities in [('EC30to60', False),
                                               ('ECwISC30to60', True)]:
        testcases.append(mesh.collect(mesh_name, with_ice_shelf_cavities))

        for initial_condition in ['PHC', 'EN4_1900']:
            with_bgc = False
            time_integrator = 'split_explicit'
            testcases.append(init.collect(
                mesh_name, with_ice_shelf_cavities, initial_condition,
                with_bgc))
            for test in [performance_test]:
                testcases.append(test.collect(
                    mesh_name, with_ice_shelf_cavities,
                    initial_condition, with_bgc, time_integrator))

    return testcases


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
    mesh_name = testcase['mesh_name']
    package, prefix = get_mesh_package(mesh_name)
    add_config(config, package, '{}.cfg'.format(prefix), exception=True)

    name = testcase['name']
    add_config(config, 'compass.ocean.tests.global_ocean.{}'.format(name),
               '{}.cfg'.format(name), exception=False)

    add_descriptions_to_config(testcase, config)
