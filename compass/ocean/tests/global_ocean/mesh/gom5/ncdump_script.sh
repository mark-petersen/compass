#!/bin/bash
# NOTE : Quote it else use array to avoid problems #
#PATH="*/ocean/global_ocean/ARRM2to18/mesh/cull_mesh/culled_mesh.nc"
PATH="*/ocean/global_ocean/ARRM2to18/WOA23/init/initial_state/initial_state.nc"
for f in $PATH
do
  #echo $f
  echo "ncdump -h $f |head|grep nCells"
done
