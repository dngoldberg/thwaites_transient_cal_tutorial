import numpy as np
from netCDF4 import Dataset
from scipy.interpolate import RegularGridInterpolator


def interp_mouginot_ant2017(X, Y, data_type, nc_file=None, return_speed=False):
    """
    Python equivalent of MATLAB interpMouginotAnt2017.

    Parameters
    ----------
    X, Y : array-like
        Coordinates where velocities should be interpolated.
    data_type : int
        1 -> VX, VY
        2 -> STDX, STDY
        3 -> ERRX, ERRY
    nc_file : str, optional
        Path to netCDF file.
    return_speed : bool, optional
        If True, return speed magnitude only.

    Returns
    -------
    vxout, vyout : ndarray
        Interpolated fields.
    OR
    speed : ndarray
        If return_speed=True.
    """

    if nc_file is None:
        nc_file = (
            "/exports/csce/datastore/geos/users/dgoldber/"
            "ice_data/ThwaitesDataProphet/Velocities/"
            "vel_nsidc.CF16_2.nc"
        )

    with Dataset(nc_file, "r") as ds:

        xdata = ds.variables["x"][:].astype(float)
        ydata = ds.variables["y"][:].astype(float)

        offset = 2

        xmin, xmax = np.min(X), np.max(X)
        ymin, ymax = np.min(Y), np.max(Y)

        # MATLAB indices are 1-based; Python uses 0-based indexing
        posx = np.where(xdata <= xmax)[0]
        id1x = max(0, np.where(xdata >= xmin)[0][0] - offset)
        id2x = min(len(xdata) - 1, posx[-1] + offset)

        posy = np.where(ydata >= ymin)[0]
        id1y = max(0, np.where(ydata <= ymax)[0][0] - offset)
        id2y = min(len(ydata) - 1, posy[-1] + offset)

        print("   -- Mouginot 2017: loading velocities")

        if data_type == 1:
            vxdata = ds.variables["VX"][id1y:id2y + 1,
                                        id1x:id2x + 1].astype(float)
            vydata = ds.variables["VY"][id1y:id2y + 1,
                                        id1x:id2x + 1].astype(float)

        elif data_type == 2:
            vxdata = ds.variables["STDX"][id1y:id2y + 1,
                                          id1x:id2x + 1].astype(float)
            vydata = ds.variables["STDY"][id1y:id2y + 1,
                                          id1x:id2x + 1].astype(float)

        elif data_type == 3:
            vxdata = ds.variables["ERRX"][id1y:id2y + 1,
                                          id1x:id2x + 1].astype(float)
            vydata = ds.variables["ERRY"][id1y:id2y + 1,
                                          id1x:id2x + 1].astype(float)

        else:
            raise ValueError("check type input")

    xsub = xdata[id1x:id2x + 1]
    ysub = ydata[id1y:id2y + 1]

    print("   -- Mouginot 2017: interpolating")

    # Match MATLAB output shape
    Xarr = np.asarray(X, dtype=float)
    Yarr = np.asarray(Y, dtype=float)

    points = np.column_stack([Yarr.ravel(), Xarr.ravel()])

    vx_interp = RegularGridInterpolator(
        (ysub, xsub),
        vxdata,
        bounds_error=False,
        fill_value=np.nan
    )

    vy_interp = RegularGridInterpolator(
        (ysub, xsub),
        vydata,
        bounds_error=False,
        fill_value=np.nan
    )

    vxout = vx_interp(points).reshape(Xarr.shape)
    vyout = vy_interp(points).reshape(Yarr.shape)

    if return_speed:
        return np.sqrt(vxout**2 + vyout**2)

    return vxout, vyout
