import pickle as pkl
import numpy as np
import os
from IPython import embed
import setupExperimentTc

npx = 10; # number of x-processors to use (nPx in SIZE.h)
npy = 10; # number of y-processors to use (nPy in SIZE.h)

timesteps_per_year = 12;

f = open('interpolated_data.pkl','rb')
data = pkl.load(f)

nx = len(data['x_mesh_mid']);
ny = len(data['y_mesh_mid']);

# size of "padding" cells to ensure all tiles are same size
gx = int(np.ceil(nx/npx) * npx - nx);
gy = int(np.ceil(ny/npy) * npy - ny);

# displays values that are needed for sNx, sNy
print('tile nx: ' + str(np.ceil(nx/npx))) # sNx in SIZE.h
print('tile ny: ' + str(np.ceil(ny/npy))) # sNx in SIZE.h
print('grid nx: ' + str(nx+gx)) # sNx in SIZE.h
print('grid ny: ' + str(ny+gy)) # sNx in SIZE.h

setupExperimentTc.setup_experiment_tc(nx,ny,gx,gy,timesteps_per_year);
