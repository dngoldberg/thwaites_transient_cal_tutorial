import numpy as np
from IPython import embed
import pickle as pkl
from pathlib import Path
from scipy.io import loadmat
import shutil
from scipy.interpolate import RegularGridInterpolator
from interpMouginotAmund import interp_mouginot_amund

import os
os.system('python snip_tc.py')

# We read the contents of the pickle file without having to name each variable explicitly.

f = open('interpolated_data.pkl','rb')    
data = pkl.load(f)
for key in data.keys():
        print(f"{key} = data['{key}']")
        exec(f"{key} = data['{key}']",globals())

def setup_experiment_tc(nx, ny, gx, gy, timesteps_per_year):


    # This function zero-fills "buffers" required for an integer
    #  number of processors
    def block(M):        
        return np.block([
            [M, np.zeros((ny, gx))],
            [np.zeros((gy, nx + gx))]
        ])

    filter_surf = False;

    # THESE VALUES SHOULD BE CONSISTENT WITH data.streamice
    density_ice = 917;
    density_oce = 1027;

    X, Y = np.meshgrid(x_mesh_mid,y_mesh_mid)

    # ADJUST BAMBER SURFACE
    surfadj = surf - firn - geoid
    surf[np.isnan(surf)]=0
    # that any ocean pixels in the pre-adjusted dataset are given zero thickness
    surfadj[surf==0]=0

    # find base for thickness calc 
    thick_floatation = (- density_oce*surfadj) / (density_ice - density_oce);
    thick_floatation[surfadj==0]=0;
    base_floatation = surfadj - thick_floatation
    bed = globals()['bed']
    base = np.maximum(bed,base_floatation)
    thick_mod = surfadj-base;
    thick_mod[surfadj==0]=0;
    thick = thick_mod;
    gr = (bed==base);
    
    # mask for defining thickness mask (Hmask). this mask array emulates
    #   the bedmachine mask: 0 is ocean, 1 is ice-free land, and 2 is ice covered
    mask = np.zeros_like(surf);
    mask[surf>0]=2;
    mask[maskbm==1]=1;
    mask[surf<0]=0;

    mask[(thick<0) & (mask!=1)] = 1; 

    #%%%%%%%%%%%%%%%%%%%%%

    #%%% HMASK IS DEFINED HERE
    #% HMASK = 1: active ice
    #% HMASK = -1: out of domain
    #% HMASK = 0: ocean
    #% ice-ocean boundaries have a calving front stress condition
    #% ice-"out of domain" boundaries have no-slip (zero velocity) conditions
    #%
    #% HMASK is -1 where ice is less then 10m (to avoid ill conditioning)
    #%

    hmask = np.ones_like(thick);
    hmask[mask==1]=-1;
    hmask[(surf==0) & (mask!=1)]=0;

    # the following ensures that all cells on the boundary of mesh are out of bounds
    # which avoids any issues with boundary nodes being out of domain
    hmask[0,:]  = -1;
    hmask[-1,:] = -1;
    hmask[:,0]  = -1;
    hmask[:,-1] = -1;
    
    # this filters out ice that is too thin and could cause instability
    hmask[thick<10 & ((hmask==1)|(hmask==2))]= -1;
    
    # this filters out very thin ice on nunataks
    hmask[surf>2000]=-1;
    hmask[~mask_dom]=-1;

    # this step is important for removing unconnecting floating components
    # as STREAMICE currently does not remove these automatically
    from skimage.measure import label

    labels = label(hmask == 1, connectivity=1)

    # Count pixels in each component (label 0 is background)
    sizes = np.bincount(labels.ravel())

    if len(sizes) > 2:  # background + at least two components
        largest = np.argmax(sizes[1:]) + 1
        hmask[(labels != 0) & (labels != largest)] = -1

    # a proxy bed -- to fool the control package
    faketopog = -1000*np.ones((ny,nx));
    faketopog[0,:] = 0
    faketopog[-1,:] = 0
    faketopog[:,0] = 0
    faketopog[:,-1] = 0
    faketopog[hmask!=1] = 0

    #########################
    
    vxmoug={};
    vymoug={};
    errxmoug={};
    errymoug={};

    # select the years to extract mouginot vel
    YEARS = np.arange(2006,2019)

    for year in YEARS:
        vxmougt,vymougt = interp_mouginot_amund(X, Y, year, 1)
        errxmougt, errymougt = interp_mouginot_amund(X, Y, year, 2)
        vxmoug[year] = vxmougt
        vymoug[year] = vymougt
        errxmoug[year] = errxmougt
        errymoug[year] = errymougt

    ####################################
    # process the velocity constraints #
    ####################################
    
    outdir = Path("velocity_constraints")
    outdir.mkdir(exist_ok=True)

    for f in outdir.iterdir():
        if f.is_file():
            f.unlink()

    for i, year in enumerate(YEARS):

        print(year)

        vxt = vxmoug[year].copy()
        vyt = vymoug[year].copy()
        errxt = errxmoug[year].copy()
        erryt = errymoug[year].copy()

        # Apply NaNs where v is NaN
        mask = np.isnan(v)
        vxt[mask] = np.nan
        vyt[mask] = np.nan
        errxt[mask] = np.nan
        erryt[mask] = np.nan

        # Determine invalid cells
        set_to_nan = (
            np.isnan(vxt)
            | np.isnan(vyt)
            | np.isnan(errxt)
            | np.isnan(erryt)
            | (mask_cost == 0)
        )

        fill_value = -999999

        vxt[set_to_nan] = fill_value
        vyt[set_to_nan] = fill_value
        errxt[set_to_nan] = fill_value
        erryt[set_to_nan] = fill_value

        # Pad arrays
        vxt = block(vxt)

        vyt = block(vyt)

        errxt = block(errxt)

        erryt = block(erryt)

        errt = np.sqrt(errxt**2 + erryt**2)

        # we consider this to be in the middle of the coverage period, so 6 mos before the year value
        timestep = timesteps_per_year * (year - 2004 - 0.5)
        suffix = str(timestep).zfill(10)

        vxt.byteswap().tofile('velocity_constraints/velobsMoug' + suffix + 'u.bin')
        vyt.byteswap().tofile('velocity_constraints/velobsMoug' + suffix + 'v.bin')
        errt.byteswap().tofile('velocity_constraints/velobsMoug' + suffix + 'err.bin')


    ####################################
    # process the surface constraints #
    ####################################
    
    outdir = Path("surface_constraints")
    outdir.mkdir(exist_ok=True)

    for f in outdir.iterdir():
        if f.is_file():
            f.unlink()

    dH_T3_cpom = (2007-2004) * cpomdict['dhdt_02_07']
    dH_T8_cpom = (2012-2007) * cpomdict['dhdt_07_12'] + dH_T3_cpom
    dH_T13_cpom = (2017-2012) * cpomdict['dhdt_12_17'] + dH_T8_cpom

    years=[3, 8, 13];
    Ismith = ~np.isnan(dhdtSmith);
    for yr in years:
        dhT = eval(f'dH_T{str(yr)}_cpom.copy()')
        surftemp = surfadj + dhT
        surftemp[~mask_cost] = np.nan
        surftemp[Y<-561e3] = np.nan

        surftemp[np.isnan(surftemp)] = -999999;
        surftemp_smith = surftemp.copy();
        surftemp_smith[Ismith] = surfadj[Ismith] + yr*dhdtSmith[Ismith]*(1-density_ice/density_oce)
        surftemp_smith[~np.isnan(dhdtSmith) & gr] = np.nan
        surftemp_smith[np.isnan(surftemp_smith)] = -999999;

        errCpom = np.ones_like(dhT)
        errCpom[dhT>(-.25*yr)] = 3;
        errCpomSmith = errCpom.copy();
        errCpomSmith[Ismith] = .3;

        surftemp = block(surftemp)
        surftemp_smith = block(surftemp_smith)
        errCpom = block(errCpom)
        errCpomSmith = block(errCpomSmith)

        surftemp.byteswap().tofile(f'surface_constraints/CPOM_surf{str(timesteps_per_year*yr).zfill(10)}.bin')
        surftemp_smith.byteswap().tofile(f'surface_constraints/CPOMSmith_surf{str(timesteps_per_year*yr).zfill(10)}.bin')

    ### initial bglen based on pattyn steady temp solution

    def apaterson(ttemp):

        ttrip=273.15;
        ttc=263.15;
        aa1=1.14e-5/3600/24/365;
        qq1=60e3;
        aa2=5.471e10/3600/24/365;
        qq2=139e3;
        rr=8.314;

        ttempk=ttrip+ttemp;

        ff=1.0e-9;

        I1 = ttempk<ttc;
        at = np.zeros_like(ttempk);
        at[I1]=aa1*np.exp(-qq1/rr/ttempk[I1]);
        at[~I1]=aa2*np.exp(-qq2/rr/ttempk[~I1]);

        return at

    # UPDATE PATH HERE FOR TEMPERATURE FILE

    pattyn_dir = '/exports/geos.ed.ac.uk/iceocean/dgoldber/pattyn/'

    Q = loadmat(pattyn_dir + 'Temp_2013')
    Z = loadmat(pattyn_dir + 'Zeta')
    xpat = Q['X']*1e3
    ypat = Q['Y']*1e3
    theta = Q['temp507']
    zeta = Z['zeta']
    Zeta = np.tile(zeta.flatten()[:, np.newaxis, np.newaxis],(1,1121, 1121))
    theta = np.transpose(theta,[2, 0, 1])
    Aglen = apaterson(theta-273.15) * 31104000;
    Bglen = Aglen**(-1/3);
    BBar = .5 * np.sum((Bglen[1:,:,:]+Bglen[:-1,:,:])*np.diff(Zeta,axis=0),axis=0)

    interper = RegularGridInterpolator(
            (ypat[:,0], xpat[0,:]),      # data shape is (len(y), len(x))
        BBar,
        bounds_error=False,
        fill_value=np.nan
    )

    BBar = np.sqrt(interper((Y,X)))
    BBar2 = BBar.copy()
    BBar[np.isnan(BBar)]=0;
    BBar[BBar==0]=700;
    BBar2[np.isnan(BBar2)]=0;


# remove nans from snapshot obs files

    verrstd = globals()['verrstd']
    vx = globals()['verrstd']
    vy = globals()['verrstd']
    vx[(np.isnan(v)) | (~mask_dom) | np.isnan(verrstd)] = -999999;
    vy[(np.isnan(v)) | (~mask_dom) | np.isnan(verrstd)] = -999999;
    verrstd[(np.isnan(v)) | (~mask_dom) | np.isnan(verrstd)] = -999999;



# write remaining binaries to file

    BBar = block(BBar)
    BBar2 = block(BBar2)
    BBar.byteswap().tofile('BglenPattyn.bin')
    BBar2.byteswap().tofile('BglenPattynMask.bin')

    smb = globals()['smb']
    smb = block(smb)
    smb.byteswap().tofile('RACMOant.bin')

    bed = block(bed)
    bed.byteswap().tofile('topog.bin')

    faketopog = block(faketopog)
    faketopog.byteswap().tofile('faketopog.bin')

    thick = block(thick)
    thick.byteswap().tofile('BedMachineThick.bin')

    vx = block(vx)
    vx.byteswap().tofile('velobsSnapu.bin')

    vy = block(vy)
    vy.byteswap().tofile('velobsSnapv.bin')

    verrstd = block(verrstd)
    verrstd.byteswap().tofile('velobsSnaperr.bin')

    ufacemask = -1 * np.ones((ny,nx));
    ufacemask = block(ufacemask)
    ufacemask.byteswap().tofile('ufacemask.bin')
    vfacemask = -1 * np.ones((ny,nx));
    vfacemask = block(vfacemask)
    vfacemask.byteswap().tofile('vfacemask.bin')

    hmask = np.block([
            [hmask, -1*np.ones((ny, gx))],
            [-1*np.ones((gy, nx + gx))]
        ]) 
    hmask.byteswap().tofile('hmask.bin')

    np.concatenate((diffx,np.ones(gx))).byteswap().tofile('delX.bin')
    np.concatenate((diffy,np.ones(gy))).byteswap().tofile('delY.bin')
