import numpy as np
from netCDF4 import Dataset
from scipy.interpolate import RegularGridInterpolator
from scipy.interpolate import NearestNDInterpolator


def interp_bedmachine_antarctica(
    X,
    Y,
    variable="bed",
    ncdate="2022-06-03",
    basename="",
    nc_file=None,
):
    """
    Interpolate BedMachine Antarctica data onto X, Y coordinates.

    Parameters
    ----------
    X, Y : array-like
        Coordinates where data should be interpolated.
    variable : str
        One of:
        'bed', 'surface', 'thickness', 'mask',
        'icemask', 'source', etc.
    ncdate : str
        BedMachine version date.
    basename : str
        Optional filename suffix.
    nc_file : str, optional
        Explicit path to NetCDF file.

    Returns
    -------
    output : ndarray
        Interpolated field.
    """

    if nc_file is None:
        nc_file = (
            "/exports/csce/datastore/geos/users/dgoldber/"
            "ice_data/ThwaitesDataProphet/BedMachine/"
            f"BedMachineAntarctica{basename}-{ncdate}.nc"
        )

    print(nc_file)
    print(f"   -- BedMachine Antarctica version: {ncdate}")

    with Dataset(nc_file, "r") as ds:

        xdata = ds.variables["x"][:].astype(float)
        ydata = ds.variables["y"][:].astype(float)

        offset = 2

        xmin, xmax = np.min(X), np.max(X)
        ymin, ymax = np.min(Y), np.max(Y)

        # Determine subset of grid to load
        posx = np.where(xdata <= xmax)[0]
        id1x = max(0, np.where(xdata >= xmin)[0][0] - offset)
        id2x = min(len(xdata) - 1, posx[-1] + offset)

        posy = np.where(ydata >= ymin)[0]
        id1y = max(0, np.where(ydata <= ymax)[0][0] - offset)
        id2y = min(len(ydata) - 1, posy[-1] + offset)

        print(f"   -- BedMachine Antarctica: loading {variable}")

        # Special handling for icemask
        if variable == "icemask":

            data = ds.variables["mask"][
                id1y:id2y + 1,
                id1x:id2x + 1
            ].astype(float)

            # ice-ocean interface treatment
            data[data == 3] = 0

        else:

            data = ds.variables[variable][
                id1y:id2y + 1,
                id1x:id2x + 1
            ].astype(float)

    xsub = xdata[id1x:id2x + 1]
    ysub = ydata[id1y:id2y + 1]

    print(f"   -- BedMachine Antarctica: interpolating {variable}")

    # MATLAB InterpFromGrid interpolation type
    if variable == "mask":
        method = "nearest"
    else:
        method = "linear"

    interpolator = RegularGridInterpolator(
        (ysub, xsub),
        data,
        method=method,
        bounds_error=False,
        fill_value=np.nan,
    )

    Xarr = np.asarray(X, dtype=float)
    Yarr = np.asarray(Y, dtype=float)

    points = np.column_stack([
        Yarr.ravel(),
        Xarr.ravel()
    ])

    output = interpolator(points).reshape(Xarr.shape)

    return output
