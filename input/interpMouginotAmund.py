import numpy as np
import xarray as xr
from IPython import embed
from scipy.interpolate import RegularGridInterpolator


def interp_mouginot_amund(X, Y, year, data_type,
                          nc_file="/exports/csce/datastore/geos/users/dgoldber/ice_data/ThwaitesDataProphet/Velocities/ASE_TimeSeries_1973-2018.nc",
                          magnitude_only=False):
    """
    Interpolate Mouginot velocity data.

    Parameters
    ----------
    X, Y : ndarray
        Coordinates at which to interpolate.
    year : int
        Time 
    data_type : int
        1 = velocity (VX, VY)
        2 = uncertainty (STDX, STDY)
    nc_file : str
        Path to NetCDF file.
    magnitude_only : bool
        If True, return speed instead of (vx, vy).

    Returns
    -------
    vx, vy : ndarray
        Interpolated velocity components.
        If magnitude_only=True, returns speed.
    """

    ds = xr.open_dataset(nc_file)

    xdata = ds["x"].values.astype(float)
    ydata = ds["y"].values.astype(float)

    year2 = ds["YEAR2"].values.astype(int)
    year_ind = np.argmin(np.abs(year2-year))

    offset = 2

    xmin, xmax = np.min(X), np.max(X)
    ymin, ymax = np.min(Y), np.max(Y)

    # MATLAB uses 1-based indexing; Python uses 0-based
    id1x = max(0, np.searchsorted(xdata, xmin, side='left') - offset)
    id2x = min(len(xdata), np.searchsorted(xdata, xmax, side='right') + offset)

    # y coordinate is assumed descending (as in MATLAB code)
    posy = np.where(ydata >= ymin)[0]
    if len(posy) == 0:
        raise ValueError("No y values >= ymin")

    idx = np.where(ydata <= ymax)[0]
    if len(idx) == 0:
        raise ValueError("No y values <= ymax")

    id1y = max(0, idx[0] - offset)
    id2y = min(len(ydata), posy[-1] + offset + 1)

    print("   -- Mouginot 2017: loading velocities")

    if data_type == 1:
        vxdata = ds["VX"].isel(
            x=slice(id1x, id2x),
            y=slice(id1y, id2y),
            z=year_ind
        ).values

        vydata = ds["VY"].isel(
            x=slice(id1x, id2x),
            y=slice(id1y, id2y),
            z=year_ind
        ).values

    elif data_type == 2:
        vxdata = ds["STDX"].isel(
            x=slice(id1x, id2x),
            y=slice(id1y, id2y),
            z=year_ind
        ).values

        vydata = ds["STDY"].isel(
            x=slice(id1x, id2x),
            y=slice(id1y, id2y),
            z=year_ind
        ).values

    else:
        raise ValueError("data_type must be 1 or 2")

    xsub = xdata[id1x:id2x]
    ysub = ydata[id1y:id2y]

    print("   -- Mouginot 2017: interpolating")

    # RegularGridInterpolator expects ascending coordinates
    if ysub[0] > ysub[-1]:
        ysub = ysub[::-1]
        vxdata = vxdata[::-1, :]
        vydata = vydata[::-1, :]

    interp_vx = RegularGridInterpolator(
        (ysub, xsub),
        vxdata,
        bounds_error=False,
        fill_value=np.nan
    )

    interp_vy = RegularGridInterpolator(
        (ysub, xsub),
        vydata,
        bounds_error=False,
        fill_value=np.nan
    )

    pts = np.column_stack((Y.ravel(), X.ravel()))

    vxout = interp_vx(pts).reshape(X.shape)
    vyout = interp_vy(pts).reshape(X.shape)

    ds.close()

    if magnitude_only:
        return np.sqrt(vxout**2 + vyout**2)

    return vxout, vyout
