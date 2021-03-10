from compass.landice.tests import dome, enthalpy_benchmark, eismint2, \
    greenland, hydro_radial


def collect():
    """
    Get a list of testcases in this configuration

    Returns
    -------
    testcases : list
        A dictionary of configurations within this core

    """
    testcases = list()
    for configuration in [dome, enthalpy_benchmark, eismint2, greenland,
                          hydro_radial]:
        testcases.extend(configuration.collect())

    return testcases
