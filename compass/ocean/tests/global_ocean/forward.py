import os
from importlib.resources import contents

from compass.ocean.tests.global_ocean.configure import configure_global_ocean
from compass.ocean.tests.global_ocean.metadata import \
    add_mesh_and_init_metadata
from compass.model import run_model
from compass.testcase import TestCase
from compass.step import Step


class ForwardStep(Step):
    """
    A step for performing forward MPAS-Ocean runs as part of global ocean test
    cases.

    Attributes
    ----------
    mesh : compass.ocean.tests.global_ocean.mesh.Mesh
        The test case that produces the mesh for this run

    init : compass.ocean.tests.global_ocean.init.Init
        The test case that produces the initial condition for this run

    time_integrator : {'split_explicit', 'RK4'}
        The time integrator to use for the forward run
    """
    def __init__(self, test_case, mesh, init, time_integrator, name='forward',
                 subdir=None, cores=None, min_cores=None, threads=None):
        """
        Create a new step

        Parameters
        ----------
        test_case : compass.TestCase
            The test case this step belongs to

        mesh : compass.ocean.tests.global_ocean.mesh.Mesh
            The test case that produces the mesh for this run

        init : compass.ocean.tests.global_ocean.init.Init
            The test case that produces the initial condition for this run

        time_integrator : {'split_explicit', 'RK4'}
            The time integrator to use for the forward run

        name : str, optional
            the name of the step

        subdir : str, optional
            the subdirectory for the step.  The default is ``name``

        cores : int, optional
            the number of cores the step would ideally use.  If fewer cores
            are available on the system, the step will run on all available
            cores as long as this is not below ``min_cores``

        min_cores : int, optional
            the number of cores the step requires.  If the system has fewer
            than this number of cores, the step will fail

        threads : int, optional
            the number of threads the step will use
        """
        self.mesh = mesh
        self.init = init
        self.time_integrator = time_integrator
        if min_cores is None:
            min_cores = cores
        super().__init__(test_case=test_case, name=name, subdir=subdir,
                         cores=cores, min_cores=min_cores, threads=threads)

        self.add_namelist_file(
            'compass.ocean.tests.global_ocean', 'namelist.forward')
        self.add_streams_file(
            'compass.ocean.tests.global_ocean', 'streams.forward')

        if mesh.with_ice_shelf_cavities:
            self.add_namelist_file(
                'compass.ocean.tests.global_ocean', 'namelist.wisc')

        if init.with_bgc:
            self.add_namelist_file(
                'compass.ocean.tests.global_ocean', 'namelist.bgc')
            self.add_streams_file(
                'compass.ocean.tests.global_ocean', 'streams.bgc')

        mesh_package = mesh.mesh_step.package
        mesh_package_contents = list(contents(mesh_package))
        mesh_namelists = ['namelist.forward',
                          'namelist.{}'.format(time_integrator.lower())]
        for mesh_namelist in mesh_namelists:
            if mesh_namelist in mesh_package_contents:
                self.add_namelist_file(mesh_package, mesh_namelist)

        mesh_streams = ['streams.forward',
                        'streams.{}'.format(time_integrator.lower())]
        for mesh_stream in mesh_streams:
            if mesh_stream in mesh_package_contents:
                self.add_streams_file(mesh_package, mesh_stream)

        mesh_path = mesh.mesh_step.path

        if mesh.with_ice_shelf_cavities:
            initial_state_target = '{}/ssh_adjustment/adjusted_init.nc'.format(
                init.path)
        else:
            initial_state_target = '{}/initial_state/initial_state.nc'.format(
                init.path)
        self.add_input_file(filename='init.nc',
                            work_dir_target=initial_state_target)
        self.add_input_file(
            filename='forcing_data.nc',
            work_dir_target='{}/initial_state/init_mode_forcing_data.nc'
                            ''.format(init.path))
        self.add_input_file(
            filename='graph.info',
            work_dir_target='{}/culled_graph.info'.format(mesh_path))
        self.add_input_file(
            filename='particles.nc',
            work_dir_target='{}/initial_state/particles.nc'
                            ''.format(init.path))

        self.add_model_as_input()

        self.add_output_file(filename='output.nc')

    def setup(self):
        """
        Set up the test case in the work directory, including downloading any
        dependencies
        """
        if self.cores is None:
            self.cores = self.config.getint(
                'global_ocean', 'forward_cores')
        if self.min_cores is None:
            self.min_cores = self.config.getint(
                'global_ocean', 'forward_min_cores')
        if self.threads is None:
            self.threads = self.config.getint(
                'global_ocean', 'forward_threads')

    def run(self):
        """
        Run this step of the testcase
        """
        run_model(self)
        add_mesh_and_init_metadata(self.outputs, self.config,
                                   init_filename='init.nc')


class ForwardTestCase(TestCase):
    """
    A parent class for test cases for forward runs with global MPAS-Ocean mesh

    Attributes
    ----------
    mesh : compass.ocean.tests.global_ocean.mesh.Mesh
        The test case that produces the mesh for this run

    init : compass.ocean.tests.global_ocean.init.Init
        The test case that produces the initial condition for this run

    time_integrator : {'split_explicit', 'RK4'}
        The time integrator to use for the forward run
    """

    def __init__(self, test_group, mesh, init, time_integrator, name):
        """
        Create test case

        Parameters
        ----------
        test_group : compass.ocean.tests.global_ocean.GlobalOcean
            The global ocean test group that this test case belongs to

        mesh : compass.ocean.tests.global_ocean.mesh.Mesh
            The test case that produces the mesh for this run

        init : compass.ocean.tests.global_ocean.init.Init
            The test case that produces the initial condition for this run

        time_integrator : {'split_explicit', 'RK4'}
            The time integrator to use for the forward run

        name : str
            the name of the test case
        """
        self.mesh = mesh
        self.init = init
        self.time_integrator = time_integrator
        subdir = get_forward_subdir(init.init_subdir, time_integrator, name)
        super().__init__(test_group=test_group, name=name, subdir=subdir)

    def configure(self):
        """
        Modify the configuration options for this test case
        """
        configure_global_ocean(test_case=self, mesh=self.mesh, init=self.init)

    def run(self):
        """
        Run each step of the testcase
        """
        config = self.config
        # get the these properties from the config options
        for step_name in self.steps_to_run:
            step = self.steps[step_name]
            # get the these properties from the config options
            step.cores = config.getint('global_ocean', 'forward_cores')
            step.min_cores = config.getint('global_ocean', 'forward_min_cores')
            step.threads = config.getint('global_ocean', 'forward_threads')

        # run the steps
        super().run()


def get_forward_subdir(init_subdir, time_integrator, name):
    """
    Get the subdirectory for a test case that is based on a forward run with
    a time integrator
    """
    if time_integrator == 'split_explicit':
        # this is the default so we won't make a subdir for the time
        # integrator
        subdir = os.path.join(init_subdir, name)
    elif time_integrator == 'RK4':
        subdir = os.path.join(init_subdir, time_integrator, name)
    else:
        raise ValueError('Unexpected time integrator {}'.format(
            time_integrator))

    return subdir
