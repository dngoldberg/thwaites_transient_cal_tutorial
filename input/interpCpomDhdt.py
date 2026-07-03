import numpy as np
from netCDF4 import Dataset
from scipy.interpolate import RegularGridInterpolator
from IPython import embed


def interp_cpom_dhdt(X, Y, nc_file=None):
    """
    Python equivalent of MATLAB interpMouginotAnt2017.

    Parameters
    ----------
    X, Y : array-like
        Coordinates where velocities should be interpolated.

    Returns
    -------
    dhdt, vyout : ndarray
        Interpolated fields.
    """

    if nc_file is None:
        nc_file = (
            "/exports/csce/datastore/geos/users/dgoldber/"
            "ice_data/cryosat_data/dhdt_cpom/"
            "antarctic_dhdt_5km_grid_1992_2017.nc"
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

        posy = np.where(ydata <= ymax)[0]
        id1y = max(0, np.where(ydata >= ymin)[0][0] - offset)
        id2y = min(len(ydata) - 1, posy[-1] + offset)

        print("   -- Mouginot 2017: loading velocities")

        # metadata: 1-Jan-2002 to 31-Dec-2007 but i suspect the 2nd date should be 31-Dec-2006  
        dhdt_02_07 = ds.variables["dhdt_2002_2006"][:].data[id1y:id2y + 1,
                                        id1x:id2x + 1].astype(float)

        # metadata: 1-Jan-2007 to 31-Dec-2011
        dhdt_07_12 = ds.variables["dhdt_2007_2011"][:].data[id1y:id2y + 1,
                                        id1x:id2x + 1].astype(float)

        # metadata: 1-Jan-2012 to 31-Dec-2016
        dhdt_12_17 = ds.variables["dhdt_2012_2016"][:].data[id1y:id2y + 1,
                                        id1x:id2x + 1].astype(float)

        #uncertainties
        dhdt_02_07_err = ds.variables["uncert_2002_2006"][:].data[id1y:id2y + 1,
                                        id1x:id2x + 1].astype(float)
        dhdt_07_12_err = ds.variables["uncert_2007_2011"][:].data[id1y:id2y + 1,
                                        id1x:id2x + 1].astype(float)
        dhdt_12_17_err = ds.variables["uncert_2012_2016"][:].data[id1y:id2y + 1,
                                        id1x:id2x + 1].astype(float)



    xsub = xdata[id1x:id2x + 1]
    ysub = ydata[id1y:id2y + 1]

    # Match MATLAB output shape
    Xarr = np.asarray(X, dtype=float)
    Yarr = np.asarray(Y, dtype=float)

    points = np.column_stack([Yarr.ravel(), Xarr.ravel()])

    return_dict = {}

    for yrange in ['02_07','07_12','12_17']:
      for add in ['','_err']:
        string = (
                    f'dhdt_{yrange}_interp = RegularGridInterpolator((ysub, xsub),'
                    f'dhdt_{yrange}{add},bounds_error=False,fill_value=np.nan)'
                 )
        exec(string)
        string = f'dhdt_{yrange}{add}_interp = dhdt_{yrange}_interp(points).reshape(Xarr.shape)'
        exec(string)
        string = f"return_dict['dhdt_{yrange}{add}'] = dhdt_{yrange}{add}_interp"
        exec(string)
    return return_dict
