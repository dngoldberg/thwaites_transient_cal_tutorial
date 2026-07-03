import numpy as np
from netCDF4 import Dataset
from scipy.interpolate import RegularGridInterpolator
from scipy.io import loadmat
from IPython import embed


def interp_racmo_1km(X, Y, ncname=None):
    """
    Interpolate RACMO 1 km SMB data onto arbitrary coordinates.

    Parameters
    ----------
    X : array_like
        X coordinates.
    Y : array_like
        Y coordinates.

    Returns
    -------
    output : ndarray
        Interpolated SMB values (m/yr ice equivalent).
    """

    # Update path accordingly
    

    q = loadmat('/exports/csce/datastore/geos/users/dgoldber/ice_data/ThwaitesDataProphet/RACMO2.3/basin_Antarctica_1km_RACMO2') 
    xdata = q['x_m'].astype(np.float64).flatten()
    ydata = q['y_m'].astype(np.float64).flatten()

    offset = 2

    xmin, xmax = np.min(X), np.max(X)
    ymin, ymax = np.min(Y), np.max(Y)

        # Determine x indices
    id1x = max(0, np.searchsorted(xdata, xmin) - offset)
    id2x = min(len(xdata), np.searchsorted(xdata, xmax, side="right") + offset)

        # Determine y indices
    id1y = max(0, np.searchsorted(ydata, ymin) - offset)
    id2y = min(len(ydata), np.searchsorted(ydata, ymax, side="right") + offset)

        # Read only the required subset
    data = np.flipud(q["accumulation"])[id1y:id2y, id1x:id2x].astype(np.float64)

    # Extract matching coordinate vectors
    xdata = xdata[id1x:id2x]
    ydata = ydata[id1y:id2y]

    # Replace missing values
    data[data == -9999] = np.nan

    # Convert from mm/yr water equivalent to m/yr ice equivalent

    # Create interpolator
    interp = RegularGridInterpolator(
        (ydata, xdata),      # data shape is (len(y), len(x))
        data,
        bounds_error=False,
        fill_value=np.nan
    )

    # Prepare query points
    pts = np.column_stack((np.ravel(Y), np.ravel(X)))
    
    output = interp(pts).reshape(np.shape(X))
    return output
