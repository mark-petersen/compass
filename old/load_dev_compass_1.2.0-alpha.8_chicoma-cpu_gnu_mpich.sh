export COMPASS_BRANCH="/usr/projects/climate/dschlichting/repos/compass/gom"
export COMPASS_VERSION="1.2.0-alpha.8"

version_file="${COMPASS_BRANCH}/compass/version.py"
code_version=$(cat $version_file)
if [[ "$code_version" != *"$COMPASS_VERSION"* ]]; then

echo "This load script is for a different version of compass:"
echo "__version__ = '$COMPASS_VERSION'"
echo ""
echo "Your code is version:"
echo "$code_version"
echo ""
echo "You need to run ./conda/configure_compass_env.py to update your conda "
echo "environment and load script."

else
# the right compass version

echo Loading conda environment
source /usr/projects/climate/dschlichting/miconda3/etc/profile.d/conda.sh
source /usr/projects/climate/dschlichting/miconda3/etc/profile.d/mamba.sh
mamba activate dev_compass_1.2.0
echo Done.
echo

if [[ -z "${NO_COMPASS_REINSTALL}" && -f "./setup.py" && \
-d "compass" ]]; then
# safe to assume we're in the compass repo
# update the compass installation to point here
mkdir -p conda/logs
echo Reinstalling compass package in edit mode...
python -m pip install -e . &> conda/logs/install_compass.log
echo Done.
echo
fi

echo Loading Spack environment...
source /usr/projects/e3sm/compass/chicoma-cpu/spack/dev_compass_1_2_0_gnu_mpich/share/spack/setup-env.sh
spack env activate dev_compass_1_2_0_gnu_mpich
export http_proxy=http://proxyout.lanl.gov:8080/
export https_proxy=http://proxyout.lanl.gov:8080/
export ftp_proxy=http://proxyout.lanl.gov:8080
export HTTP_PROXY=http://proxyout.lanl.gov:8080
export HTTPS_PROXY=http://proxyout.lanl.gov:8080
export FTP_PROXY=http://proxyout.lanl.gov:8080

source /usr/share/lmod/8.3.1/init/sh

module rm PrgEnv-gnu
module rm PrgEnv-nvidia
module rm PrgEnv-cray
module rm PrgEnv-aocc
module rm craype-accel-nvidia80
module rm craype-accel-host

module load PrgEnv-gnu/8.4.0
module load gcc/12.2.0
module load craype-accel-host

module load cray-libsci

module load craype
module load libfabric/1.15.2.0
module load cray-mpich/8.1.26

module rm cray-hdf5-parallel
module rm cray-netcdf-hdf5parallel
module rm cray-parallel-netcdf
module load cray-hdf5-parallel/1.12.2.3
module load cray-netcdf-hdf5parallel/4.9.0.3
module load cray-parallel-netcdf/1.12.3.3

export MPICH_ENV_DISPLAY=1
export MPICH_VERSION_DISPLAY=1
## purposefully omitting OMP variables that cause trouble in ESMF
# export OMP_STACKSIZE=128M
# export OMP_PROC_BIND=spread
# export OMP_PLACES=threads
export HDF5_USE_FILE_LOCKING=FALSE
export PERL5LIB=/usr/projects/climate/SHARED_CLIMATE/software/chicoma-cpu/perl5-only-switch/lib/perl5
export PNETCDF_HINTS="romio_ds_write=disable;romio_ds_read=disable;romio_cb_write=enable;romio_cb_read=enable"
export FI_CXI_RX_MATCH_MODE=software
export MPICH_COLL_SYNC=MPI_Bcast

export LD_LIBRARY_PATH=$CRAY_LD_LIBRARY_PATH:$LD_LIBRARY_PATH
echo Done.
echo

export MPAS_EXTERNAL_LIBS=""
export NETCDF=${CRAY_NETCDF_HDF5PARALLEL_PREFIX}
export NETCDFF=${CRAY_NETCDF_HDF5PARALLEL_PREFIX}
export PNETCDF=${CRAY_PARALLEL_NETCDF_PREFIX}
export PIO=/usr/projects/e3sm/compass/chicoma-cpu/spack/dev_compass_1_2_0_gnu_mpich/var/spack/environments/dev_compass_1_2_0_gnu_mpich/.spack-env/view

export USE_PIO2=true
export OPENMP=true
export HDF5_USE_FILE_LOCKING=FALSE
export LOAD_COMPASS_ENV=/usr/projects/climate/dschlichting/repos/compass/gom/load_dev_compass_1.2.0-alpha.8_chicoma-cpu_gnu_mpich.sh
export COMPASS_MACHINE=chicoma-cpu

# the right compass version
fi
