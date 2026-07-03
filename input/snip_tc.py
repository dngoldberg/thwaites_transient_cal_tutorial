import numpy as np
from scipy.io import loadmat
from matplotlib.path import Path
from interpMouginotAmund import interp_mouginot_amund
from interpBedmachineAntarctica import interp_bedmachine_antarctica
from interpRACMO1km import interp_racmo_1km
from interpMouginotAnt2017 import interp_mouginot_ant2017
from interpCpomDhdt import interp_cpom_dhdt
from scipy.interpolate import RegularGridInterpolator
from IPython import embed
import rasterio as rio
import pickle as pkl

# Load bounds1.mat
data1 = loadmat("bounds1.mat")
x = data1["x"].squeeze()
y = data1["y"].squeeze()

# Load bounds2.mat (if it contains additional variables you need)
data2 = loadmat("bounds2.mat")
x = data2["x"].squeeze()
y = data2["y"].squeeze()

# Domain limits
xlim_domain = np.array([
    np.floor(np.min(x) / 1e3) - 1,
    np.ceil(np.max(x) / 1e3) + 1
]) * 1e3

ylim_domain = np.array([
    np.floor(np.min(y) / 1e3) - 1,
    verr[(np.isnan(v)) | (~mask_dom) | np.isnan(verrstd)] = -999999;
    np.ceil(np.max(y) / 1e3) + 1
]) * 1e3

dx = 1500


# MATLAB colon operator includes the endpoint if exactly reached
x_mesh = np.arange(xlim_domain[0] - dx/2,
                   xlim_domain[1] + dx/2 + dx,
                   dx)

y_mesh = np.arange(ylim_domain[0] - dx/2,
                   ylim_domain[1] + dx/2 + dx,
                   dx)

# Cell centers
x_mesh_mid = 0.5 * (x_mesh[:-1] + x_mesh[1:])
y_mesh_mid = 0.5 * (y_mesh[:-1] + y_mesh[1:])

# Cell sizes
diffx = np.diff(x_mesh)
diffy = np.diff(y_mesh)

# Meshgrid (same orientation as MATLAB)
X, Y = np.meshgrid(x_mesh_mid, y_mesh_mid)


# ------------------------------------------------------------------
# Load bounds3.mat
data3 = loadmat("bounds3.mat")
xmask = data3["xmask"].squeeze()
ymask = data3["ymask"].squeeze()

# Equivalent of MATLAB roipoly
points = np.column_stack((X.ravel(), Y.ravel()))
polygon = Path(np.column_stack((xmask, ymask)))
mask_dom = polygon.contains_points(points).reshape(X.shape)

# ------------------------------------------------------------------
# Reload bounds1 (or reuse x and y already loaded)
data1 = loadmat("bounds1.mat")
x = data1["x"].squeeze()
y = data1["y"].squeeze()

polygon = Path(np.column_stack((x, y)))
mask_cost = polygon.contains_points(points).reshape(X.shape)

### INTERPOLATE FROM DATA SOURCES

# obtain velocities and errors from mosaic for snapshot 
verr = interp_mouginot_ant2017(X,Y,3,return_speed=True);
verrstd = interp_mouginot_ant2017(X,Y,2,return_speed=True);
vx, vy = interp_mouginot_ant2017(X,Y,1);
v = interp_mouginot_ant2017(X,Y,1,return_speed=True);

# fields from BedMachine (v3, approx)
bed = interp_bedmachine_antarctica(X,Y,'bed');
bmthick = interp_bedmachine_antarctica(X,Y,'thickness');
firn = interp_bedmachine_antarctica(X,Y,'firn');
geoid = interp_bedmachine_antarctica(X,Y,'geoid');
maskbm = interp_bedmachine_antarctica(X,Y,'mask');
surfbm = interp_bedmachine_antarctica(X,Y,'surface');
smb = interp_racmo_1km(X,Y);

# obtain dhdt on ice shelves from Smith 2020 (even though they are too small)
# UPDATE PATH HERE
tif_file = (
            "/exports/csce/datastore/geos/users/dgoldber/"
            "ice_data/Smith2020_updated/ICESat1_ICESat2_mass_change_updated_2_2021/dhdt/"
            "ais_dhdt_floating.tif"
           )

rdr = rio.open(tif_file)
smith_dhdt = rdr.read(1)
height = smith_dhdt.shape[0]
width = smith_dhdt.shape[1]
cols, rows = np.meshgrid(np.arange(width), np.arange(height))
xs, ys = rio.transform.xy(rdr.transform, rows, cols)
xs = xs.reshape((height,width))
ys = ys.reshape((height,width))
ys = np.flipud(ys)
smith_dhdt = np.flipud(smith_dhdt)
xs = xs[0,:]
ys = ys[:,0]

interper = RegularGridInterpolator(
        (ys, xs),
        smith_dhdt,
        bounds_error=False,
        fill_value=np.nan,
    )

dhdtSmith = interper((Y,X))
dhdtSmith[Y<-5e5] = np.nan

# Bamber dem: UPDATE PATH HERE

bamber_file = '/home/dgoldber/network_links/ice_data/bamber/krigged_dem_nsidc.bin'
bamber_dem = np.fromfile(bamber_file,dtype='float32').reshape((5601,5601))
bamber_dem = np.flipud(bamber_dem);
bamber_x = np.arange(-2800500,(-2800500+5.601e6),1e3)
bamber_y = np.arange(-2800500,(-2800500+5.601e6),1e3);
interper = RegularGridInterpolator(
        (bamber_y, bamber_x),
        bamber_dem,
        bounds_error=False,
        fill_value=np.nan,
    )
surf = interper((Y,X))
# without this, i was left with parts of an ice shelf that were extremely thin, dynamically unimportant,
# jutting out as peninsulas that caused issues because of the lack of calving front movement
surf[surf<-8]=np.nan

# CPOM DHDT
cpomdict = interp_cpom_dhdt(X,Y)

def inv_dist_weighting(x, y, v, xq, yq, p, max_rad):
    """
    Inverse Distance Weighting (IDW) interpolation.

    Parameters
    ----------
    x, y : ndarray
        Coordinates of known data points.
    v : ndarray
        Values at known data points.
    xq, yq : ndarray
        Query points where interpolation is desired.
    p : float
        Power parameter.
    max_rad : float
        Maximum search radius.

    Returns
    -------
    vq : ndarray
        Interpolated values at query points.
    """
    x = np.asarray(x)
    y = np.asarray(y)
    v = np.asarray(v)
    xq = np.asarray(xq)
    yq = np.asarray(yq)
    vq = np.full_like(xq, np.nan, dtype=float)
    for i in range(len(xq)):
        if (i + 1) % 100 == 0:
            print(f"{i + 1} points processed")
        d = np.sqrt((xq[i] - x)**2 + (yq[i] - y)**2)
        mask = d < max_rad
        if np.any(mask):
            # Handle exact match
            if np.any(d[mask] == 0):
                vq[i] = v[mask][d[mask] == 0][0]
            else:
                w = 1.0 / (d[mask] ** p)
                vq[i] = np.dot(w, v[mask]) / np.sum(w)
    return vq

# Bedmachine Firn thickness to rest of ice shelf
hasfirn = (firn>0)
nofirn = (firn==0) & (~np.isnan(surf))
firn[nofirn] = inv_dist_weighting(X[hasfirn],Y[hasfirn],firn[hasfirn],X[nofirn],Y[nofirn],2,5.e4)

list_out = ['bed', 'firn', 'geoid', 'surf', 'surfbm', 'x_mesh_mid', 'y_mesh_mid', 'mask_dom', 'cpomdict', 'x_mesh_mid', 'y_mesh_mid']
list_out = list_out + ['smb', 'diffx', 'diffy', 'verrstd', 'vx', 'vy', 'v', 'maskbm', 'bmthick', 'mask_cost', 'dhdtSmith']

dict_out = {}
for varname in list_out:
    exec(f"dict_out['{varname}'] = {varname}")


f = open('interpolated_data.pkl','wb')
pkl.dump(dict_out,f)
f.close()
