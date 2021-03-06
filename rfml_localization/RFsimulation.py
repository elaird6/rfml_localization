# AUTOGENERATED! DO NOT EDIT! File to edit: 01_RFsimulation.ipynb (unless otherwise specified).

__all__ = ['RFchannel']

# Cell
import numpy as np
import matplotlib.pyplot as plt
from scipy.special import comb
from itertools import combinations
from sklearn.utils import check_array

# Cell
class RFchannel:
    """
    The class enables the creation of a parameterized RF channel
    environment.  The default channel parameters are based on academic
    literature that represent, in average, a typical office building
    with an exponential distribution of multipath clusters, a path loss
    characterized by a log-Gaussian distribution around a distant
    dependent mean, and a Laplacian distribution with respect to angle
    of arrival.  Using these parameters plus user input, there are a
    number of functions within the class enabling simulation of
    measurements.

    The methods within this class can be used as stand-alone functions
    if pulled out of the class.  Parameters that are set by the class
    instantiation are noted as such.

    __Parameters__

    Multipath parameters for temporal measurements (e.g. ToA/TDoA) as
    described by ([^1]) are:

    >__maxSpreadT__ : float, default = 100
    >- Max delay spread to check (ns)
    >
    >__PoissonInvLambda__ : float, default = 50
    >- Poisson Cluster Arrival Parameter (ns)
    >
    >__Poissoninvlambda__ : float, default = 10
    >- Poisson Multipath Arrival Parameter (ns)

    >__PoissonGamma__ : float, default = 50
    >- Amplitude Decay of Cluster

    >__Poissongamma__ : float, default = 29
    >-Amplitude Decay of Multipath

    Channel gain parameters for power/amplitude measurements (e.g.
    RSS/DRSS) as described by ([^2]) are:

    >__PathLossN__ : float, default = 3.0
    >- Path Loss Exponent (dB)
    >
    >__Xsigma__ : float, default =  7
    >- Std deviation of Gaussian RV (log-normal)
    >
    >__Wavelength__ : float, default = 3.0e8 / 205.267e6
    >- Frequency dependent (Hz), units of meter

    Multipath parameters for spatial measurements (e.g. AoA/DAoA) as
    described by ([^3]) are:

    >__AoAsigma__ : float, default = 26*np.pi/180
    >- Std deviation of Laplacian RV (rad)

    __Notes__

    [^1]: A. A. M. Saleh and R. Valenzuela, "A Statistical Model for
        Indoor Multipath Propagation," in IEEE Journal on Selected
        Areas in Communications, vol. 5, no. 2, pp. 128-137, February
        1987, doi: 10.1109/JSAC.1987.1146527.
    [^2]: Theodore S. Rappaport's Wireless Communications: Principles
        and Practice by IEEE Press, Inc. Prentic Hall ISBN:
        0-7803-1167-1. Chapters 3 and 4
    [^3]: Q. H. Spencer, B. D. Jeffs, M. A. Jensen and A. L.
        Swindlehurst, "Modeling the statistical time and angle of
        arrival characteristics of an indoor multipath channel," in
        IEEE Journal on Selected Areas in Communications, vol. 18, no.
        3, pp. 347-360, March 2000, doi: 10.1109/49.840194.
    """

    def __init__(self, maxSpreadT = 100, PoissonInvLambda = 50, Poissoninvlambda = 10,
                 PoissonGamma = 50, Poissongamma = 29, PathLossN = 3.0, Xsigma = 7,
                 Wavelength = 3.0e8 / 205.267e6, AoAsigma = 26*np.pi/180):
        self.maxSpreadT=maxSpreadT
        self.PoissonInvLambda=PoissonInvLambda
        self.Poissoninvlambda=Poissoninvlambda
        self.PoissonGamma=PoissonGamma
        self.Poissongamma=Poissongamma
        self.PathLossN=PathLossN
        self.Xsigma=Xsigma
        self.Wavelength=Wavelength
        self.AoAsigma=AoAsigma

    def generate_RxTxlocations(self, n_rx=6, areaWL=np.array([20,60]), n_runs=1000,
                               sensor_locs= np.array([[[6.3], [14.1], [7.2], [14.5], [7.5], [13.5]],[[15.3], [15.1], [30.1], [30.5], [44.9], [44.5]]]),
                               rxtx_flag=3, grid_flag=0, seed=None):
        """
        Generate a three dimensional array (cartesian coordinates -- each
        row a dim) x (sensors -- each col a specific sensor) x (num_runs --
        3rd dimension is number of observations) that provides locations of
        a Tx source and a set of RF sensors across multiple
        observations/runs. Each column is a sensor (except first col
        is Tx) location, next col is sensor 1 location, then sensor 2, etc.
        3rd dimension marks either a new or same Rx sensor arrangement
        (depending on flag) at next observation.  Values are in meters.

        __Parameters__

        >__n_rx__ : integer, default=6
        >- Number of receivers/sensors
        >
        >__areaWL__ : ndarray of shape (2,), default= np.array([20,60])
        >- Bounding size of area of interest, square/rectangle
        >
        >__n_runs__ : integer, default=1000
        >- Number of observations/samples/runs to generate
        >
        >__sensor_locs__ : ndarray of shape (2,n_rx,1), default= np.array([[[6.3], [14.1], [7.2], [14.5], [7.5], [13.5]],[[15.3], [15.1], [30.1], [30.5], [44.9], [44.5]]])
        >- Location of sensors, only used if `rxtx_flag`=3
        >
        >__rxtx_flag__ : integer, default=3
        >- Flag on how Tx and/or Rx location are randomly chosen. Values are as follows,
        >    - 0 -same Tx location, random Rx locations
        >    - 1 -random Tx location, same Rx locations
        >    - 2 -random Tx locations, random Rx locations
        >    - 3 -random Tx, fixed Rx locations based on rx_layout
        >
        >__grid_flag__ : boolean, default=0
        >    - Flag on generating random Tx location on evenly spaced
        >    grid (1m x 1m spacing).  Default is random, non-grid.
        >
        >__seed__ : integer, default=None
        >- set for reprodducible results

        __Returns__

        >Self, sets self.rxtx_locs

        """
        #get basic parameters from class, set required variables
        grid_dim = len(areaWL)#.size
        if grid_dim != 2:
            raise ValueError('{areaWL} not supported, not handling anything other than 2'.format(grid_dim=repr(grid_dim)))

        #generate locations on grid
        if (grid_flag):
            #needs to be fixed if higher than 3 dimensions
            dict_size=areaWL[0]*areaWL[1]
            #generate matrix with Tx locations at all grid points
            rxtxlocations = np.mgrid[1:areaWL[0]+1,1:areaWL[1]+1].reshape((2,1,dict_size),order='C')
            if n_runs != dict_size:
                raise ValueError('num_runs is not {dict_size} for dictionary making'.format(dict_size=repr(dict_size)))
            if rxtx_flag != 3:
                raise ValueError('RxTx_flag not matching Dict_flag for dictionary making')
            #concatenate random rx points which will be overwritten based on flag
            rxtxlocations = np.concatenate((rxtxlocations,np.random.default_rng(seed).uniform(0,1,(grid_dim, n_rx, n_runs))),axis=1)

        #generate locations randomly
        else:
            rxtxlocations = np.random.default_rng(seed).uniform(0,1,size=(grid_dim, n_rx+1, n_runs))
            #scale locations to given rectangular volume
            for i in np.arange(grid_dim):
                rxtxlocations[i,:,:] = rxtxlocations[i,:,:]*areaWL[i]

        #fix locations based on flag sent
        #set all Tx locations the same, keep random rx
        if rxtx_flag == 0:
            rxtxlocations[:,0,:]=np.expand_dims(rxtxlocations[:,0,0],axis=1)
        #random Tx, same Rx
        elif rxtx_flag == 1:
            rxtxlocations[:,1:,:]=np.expand_dims(rxtxlocations[:,1:,0],axis=2)
        #random Tx, random Rx (already there)
        elif rxtx_flag == 2:
            pass
        #use provided layout for rx
        elif rxtx_flag == 3:
            try:
                rxtxlocations[:,1:,:]=sensor_locs
            except ValueError:
                print("ValueError: check rx_layout parameter.  Passed numpy array of right shape?")
        else:
            raise ValueError('{rxtx_flag} wrong rxtx_flag, check value'.format(rxtx_flag=repr(rxtx_flag)))

        #save passed parameters and location information to instance
        self.n_runs=n_runs
        self.n_rx=n_rx
        self.areaWL=areaWL
        self.sensor_locs=sensor_locs
        self.rxtx_flag=rxtx_flag
        self.grid_flag=grid_flag
        self.seed_loc = seed
        self.rxtx_locs=rxtxlocations

        return self

    def calculate_Rxxdelay(self, ch_delay_flag = 1, tdoa_flag = 1, seed=None):
        """
        Calculates relative delay of wireless signals from a
        transmitter (Tx) to different receivers (Rx) based on given Rx
        and Tx locations for each run/observation. Assumes structure of
        first column is Tx, rest of columns are Rx. Third dimension is
        multiple runs of data (see `generate_RxTxlocations`). These
        relative delays are time delay estimates (TDE's).

        Time related variables are assumed to be nanoseconds in
        PoissonArray, time intervals are normalized to same.  Note that
        rxtx_locations is given in meters.  Perturbs the ideal TDE
        based on given statistical distribution(s) parameterized by
        values in PoissonArray.  In other words, describes impairments
        caused by multipath in a statistical sense ([^4]).

        __Parameters__

        >__ch_delay_flag__ : Integer/boolean, default=1
        >- Channel flag whether to add multipath (random) based on
        >PoissonArray parameters.
        >    - 0 - return ideal delays (absolute
        >or differential)
        >    - 1 (default) - return random offsets
        >characterized by poissonarray parameters
        >
        >__tdoa_flag__ : Integer/boolean, default=1
        >- Type of measurement to return,
        >    - 0 - rtn abs time of flight (i.e. ToF) between Tx and Rx.
        >    - 1-(default)- returns differential time (i.e., TDOA) between
        >        pairs of sensors of format (rx1-rx2, rx1-rx3,... rx1-rxn,
        >        rx2-rx3,..., rx(n-1) - rxn
        >
        >__rxtx_locations__ : ndarray, self.rxtx_locs_
        >- *set by class instantiation*
        >- Format of [location dims] x [num_rx + 1] x [num_runs] array
        >
        >__poissonarray__ : list,[maxSpreadT, PoissonInvLambda, Poissoninvlambda, PoissonGamma, Poissongamma]
        >- *set by class instantiation*
        >- List of time-related propagation parameters in integers
        >    (nanosecond units)
        >
        >__seed__ : integer, default=None
        >- set for reprodducible results

        __Returns__

        >Self, sets self.rxx_delay
        >- Format is [num_runs] x [abs (num_rx)/diff delay measurements
        >(num_rx choose 2)] - units of nanoseconds

        __Notes__

        [^4]: A. A. M. Saleh and R. Valenzuela, "A Statistical Model for
            Indoor Multipath Propagation," in IEEE Journal on Selected
            Areas in Communications, vol. 5, no. 2, pp. 128-137, February
            1987, doi: 10.1109/JSAC.1987.1146527.

        """
        #get basic parameters inherent in rxtx_locations
        rxtx_locations = self.rxtx_locs
        poissonarray = [self.maxSpreadT, self.PoissonInvLambda,
                        self.Poissoninvlambda, self.PoissonGamma,
                        self.Poissongamma]
        _, num_rx, num_runs = rxtx_locations.shape
        num_rx -= 1 #2nd dimension has one Tx and rest Rx

        #get Tx positions
        tx_vec=np.expand_dims(rxtx_locations[:,0,:],axis=1)
        #get Rx positions
        rx_array=rxtx_locations[:,1:,:]
        #note that we (currently) assume that first entry is transmitter
        #calculate absolute delays from Tx to each Rx (convert from meters to ns)
        abs_delay = np.linalg.norm(tx_vec-rx_array, axis=0)*10/3
        offsets=np.zeros(abs_delay.shape)

        if (ch_delay_flag):
            #add in Poisson delays and scale using Rayleigh values
            maxspreadt,pIL, pil, pG, pg = poissonarray
            #set up typical cluster, ray numbers based on provide values
            num_clstrs = maxspreadt // pIL
            if num_clstrs == 0: num_clstrs=1
            num_rays = (2*pIL) // pil
            clstr_idx = np.arange(0, num_clstrs)
            ray_idx = np.arange(0, num_rays)
            #generate cluster and ray timing
            clstr_times = np.expand_dims(np.random.default_rng(seed).gamma(clstr_idx,pIL*np.ones((num_rx,num_runs,1))),axis=3)
            ray_times = np.random.default_rng(seed).gamma(ray_idx,pil*np.ones((num_rx,num_runs,num_clstrs, num_rays)))

            #get path gains for cluster/ray combos
            clstr_ray_gains = np.random.default_rng(seed).rayleigh(np.multiply(np.exp(-clstr_times/pG),np.exp(-ray_times/pg))/2)

            #reshape to make easier to index, find largest path gain
            clstr_ray_gains = clstr_ray_gains.reshape(num_rx, num_runs, num_rays*num_clstrs)
            times_matrix_idx = np.expand_dims(np.argmax(clstr_ray_gains, axis=2), axis=2)
            #make it easy to find associated cluster, ray times for biggest path gain
            clstr_times1 = np.matmul(clstr_times,np.ones((1,num_rays)))
            #ray_times1 = np.matmul(np.ones((num_clstrs,1)),ray_times)
            times_matrix = (clstr_times1 + ray_times).reshape(clstr_ray_gains.shape)
            #get offset
            offsets = np.take_along_axis(times_matrix,times_matrix_idx,axis=2).squeeze(axis=2)

        if (tdoa_flag):
            #from absolute delays+offsets, get relative delays
            # so create array to hold values, set abs+offsets, then iterate to get diff
            rxx_delay = np.zeros((num_runs,comb(num_rx,2,exact=True)))
            temp = abs_delay+offsets
            for i,j in zip(range(rxx_delay.shape[1]),combinations(range(num_rx),2)):
                rxx_delay[:,i]=temp[j[0],:]-temp[j[1],:]
        else:
            #return absolute values of time of flight
            rxx_delay = np.transpose(abs_delay + offsets)

        #save parameters to self
        self.ch_delay_flag = ch_delay_flag
        self.tdoa_flag = tdoa_flag
        self.seed_tdoa = seed
        self.rxx_delay = rxx_delay

        return self

    def calculate_RxxRssi(self, ch_gain_flag=1, drss_flag=0, seed=None):
        """
        Calculates absolute or relative received power at each sensor
        (or pair of sensors) based on given Rx and Tx locations. Assumes
        structure of first column is Tx, rest of columns are Rx. Third
        dimension is multiple runs of data (see
        `generate_RxTxlocations`).  Returns absolute received signal
        strength (RSS) or relative power (RSSI).

        Received power is a log-normal Gaussian/Normal RV around a
        distance dependent mean ([^5]).

        __Parameters__

        >__ch_gain_flag__ : integer/boolean, default =1
        >- Whether to add shadowing based on LogNormalArray parameters
        >    - 0 - ideal free space loss
        >    - 1 - (default) - shadowing path loss
        >
        >__drss_flag__ : integer/boolean, default=0
        >- Type of measurement to return,
        >    - 0 - (default) return RSS
        >    - 1 - rtn differential RSS (n choose 2) between pairs of
        >    sensors of format (rx1-rx2, rx1-rx3,... rx1-rxn,
        >    rx2-rx3,..., rx(n-1) - rxn
        >
        >__rxtx_locations__ : ndarray, self.rxtx_locs_
        >- *set by class instantiation*
        >-Format of [location dims] x [num_rx + 1] x [num_runs] array
        >
        >__LogNormalArray__ : list,
        >- *set by class instantiation*
        >- List of RF channel parameters in relevant units:
        >    [PathLossN, Xsigma, Wavelength] where PathLossN is path loss
        >    exponent (ideal is 2) in dB, Xsigma is Std deviation of
        >    received power in dB (log-normal Gaussian RV), Wavelength
        >    is of RF signal emanating from Tx source in Hz
        >
        >__seed__ : integer, default=None
        >- set for reprodducible results

        __Returns__

        >Self, sets self.rxx_rssi
        >- Format is [num_runs] x [abs (num_rx)/diff delay measurements
        >    (num_rx choose 2)] - units of dB

        __Notes__

        [^5]: Theodore S. Rappaport's Wireless Communications: Principles
            and Practice by IEEE Press, Inc. Prentic Hall ISBN:
            0-7803-1167-1. Chapters 3 and 4
        """
        #get basic parameters inherent in rxtx_locations
        rxtx_locations = self.rxtx_locs
        lognormalarray = [self.PathLossN, self.Xsigma,
                          self.Wavelength]
        _, num_rx, num_runs = rxtx_locations.shape
        num_rx -= 1 #2nd dimension has one Tx and rest Rx
        #
        tx_vec=np.expand_dims(rxtx_locations[:,0,:],axis=1)
        rx_array=rxtx_locations[:,1:,:]
        #note that we (currently) assume that num_tx == 1
        #calculate absolute distances from Tx to each Rx
        #measurements stay in meters
        abs_dist = np.linalg.norm(tx_vec-rx_array, axis=0)
        #get reference loss in db, normalize d0 to lambda
        pln, xsigma, wavelength=lognormalarray
        PLd0=-10*np.log10(wavelength*wavelength/(16*np.pi*np.pi))*np.ones((num_rx,num_runs))
        offsets=np.zeros(abs_dist.shape)

        # if shadowing flag (or ch_gain_flag)
        if (ch_gain_flag):
            #calculate loss based on PL exponent and shadowing factors
            rssi_vals = PLd0 + 10*pln*np.log10(abs_dist) + np.random.default_rng(seed).normal(scale=xsigma,size=abs_dist.shape)
        else:
            #calculate loss based on ideal path loss (free space)
            rssi_vals = PLd0 + 10*2*np.log10(abs_dist)

        #return either differential or absolute received signal strength
        if (drss_flag):
            #from absolute rssi_vals, get relative rss
            # so create array to hold values, then iterate to get diff
            rxx_rssi = np.zeros((num_runs,comb(num_rx,2,exact=True)))
            for i,j in zip(range(rxx_rssi.shape[1]),combinations(range(num_rx),2)):
                rxx_rssi[:,i]=rssi_vals[j[0],:]-rssi_vals[j[1],:]
        else:
            rxx_rssi = np.transpose(rssi_vals)

        #save parameters to self
        self.ch_gain_flag = ch_gain_flag
        self.drss_flag = drss_flag
        self.seed_rss = seed
        self.rxx_rssi = rxx_rssi

        return self

    def calculate_AoA(self, ch_angle_flag= 1, daoa_flag= 0, seed=None):

        """ Calculates AoA based on given Rx and Tx locations. Assumes
        structure of first column is Tx, rest of columns are Rx. Third
        dimension is multiple runs of data.  For noisy case, ([^7])
        assumes uniform distribution [0,2pi) of clusters, each cluster
        has Laplacian distribution around a specific AoA with width
        just under 30 degrees.  Assumption is specular component (or
        strongest) mean value is correct value.

        __Parameters__

        >__ch_angle_flag__ : Integer/boolean, default=1
        >- Flag whether to add multipath affect based on AoAsigma
        >    parameters.
        >    - 0 - return ideal AoA (absolute or differential)
        >    - 1 (default) - return random offsets characterized by
        >    AoAsigma parameters
        >
        >__daoa_flag__ : integer/boolean, default=0
        >- Type of measurement to return,
        >    - 0 - (default) return AoA
        >    - 1 - rtn differential AoA (n choose 2) between pairs of
        >    sensors of format (rx1-rx2, rx1-rx3,... rx1-rxn,
        >    rx2-rx3,..., rx(n-1) - rxn
        >
        >__rxtx_locations__ : ndarray, self.rxtx_locs_
        >- *set by class instantiation*
        >- Format of [location dims] x [num_rx + 1] x [num_runs] array
        >
        >__AoAArray__ : list, self.AoAsigma
        >- *set by class instantiation*
        >- List of RF channel parameters in relevant units: [AoAsigma]
        >    which is Laplacian standard deviation of angle of arrival
        >    error in radians of RF signal emanating from Tx source
        >
        >__seed__ : integer, default=None
        >- set for reprodducible results

        __Returns__

        >Self, sets self.rxx_rssi
        >- Format is [num_runs] x [abs (num_rx)/diff angle measurements
        >    (num_rx choose 2)] - units of radians

        __Notes__

        [^7]: Q. H. Spencer, B. D. Jeffs, M. A. Jensen and A. L.
            Swindlehurst, "Modeling the statistical time and angle of
            arrival characteristics of an indoor multipath channel," in
            IEEE Journal on Selected Areas in Communications, vol. 18, no.
            3, pp. 347-360, March 2000, doi: 10.1109/49.840194.
        """
        #get basic parameters inherent in rxtx_locations
        rxtx_locations = self.rxtx_locs
        aoasigma = self.AoAsigma
        _, num_rx, num_runs = rxtx_locations.shape
        num_rx -= 1 #2nd dimension has one Tx and rest Rx
        #
        tx_vec=np.expand_dims(rxtx_locations[:,0,:],axis=1)
        rx_array=rxtx_locations[:,1:,:]
        #note that we (currently) assume that num_tx == 1
        #calculate angle from Rx to each Tx in radians
        diff_vec = tx_vec - rx_array
        abs_aoa = np.arctan2(diff_vec[1,:,:],diff_vec[0,:,:])
        #
        if (ch_angle_flag):
            #calculate angle based on Laplacian
            abs_aoa = abs_aoa+ np.random.default_rng(seed).laplace(scale=aoasigma,size=abs_aoa.shape)

        if (daoa_flag):
            #from absolute aoa vals, get relative aoa
            # so create array to hold values, then iterate to get diff
            rel_aoa = np.zeros((num_runs,comb(num_rx,2,exact=True)))
            for i,j in zip(range(rel_aoa.shape[1]),combinations(range(num_rx),2)):
                    rel_aoa[:,i]=abs_aoa[j[0],:]-abs_aoa[j[1],:]
        else:
            rel_aoa = np.transpose(abs_aoa)

        #save parameters to self
        self.ch_angle_flag = ch_angle_flag
        self.daoa_flag = daoa_flag
        self.seed_aoa = seed
        self.rxx_aoa = rel_aoa

        return self

    def generate_Xmodel(self, ch_delay_flag=1, ch_gain_flag=1, ch_angle_flag=1,
                        meas_flag=6, diff_array= [1,0,0], seed=None):

        """ Generates a set of measurements based on passed parameters
        that can be used for a dictionary or training/testing of
        different optimization algorithms.

        ___Parameters___

        >__rxtx_locations__ : ndarray, self.rxtx_locs_
        >- *set by class instantiation*
        >- Format of [location dims] x [num_rx + 1] x [num_runs] array
        >
        >__poissonarray__ : list, default=[maxSpreadT, PoissonInvLambda, Poissoninvlambda, PoissonGamma, Poissongamma]
        >- *set by class instantiation*
        >- List of time-related propagation parameters in integers
        >    (nanosecond units)
        >
        >__ch_delay_flag__ : Integer/boolean, default=1
        >- Channel flag whether to add multipath (random) based on
        >    PoissonArray parameters.
        >    - 0 - return ideal delays (absolute
        >    - or differential) 1 (default) - return random offsets
        >    characterized by poissonarray parameters
        >
        >__LogNormalArray__ : list, default=[PathLossN, Xsigma, Wavelength]
        >- *set by class instantiation*
        >- List of RF channel parameters in relevant units:
        >     where PathLossN is path loss
        >    exponent (ideal is 2) in dB, Xsigma is Std deviation of
        >    received power in dB (log-normal Gaussian RV), Wavelength
        >    is of RF signal emanating from Tx source in Hz
        >
        >__ch_gain_flag__ : integer/boolean, default =1
        >- Whether to add shadowing based on LogNormalArray parameters
        >    - 0 - ideal free space loss
        >    - 1 - (default) - shadowing path loss
        >
        >__AoAArray__ : list, self.AoAsigma
        >- *set by class instantiation*
        >- List of RF channel parameters in relevant units: [AoAsigma]
        >    which is Laplacian standard deviation of angle of arrival
        >    error in radians of RF signal emanating from Tx source
        >
        >__ch_angle_flag__ : Integer/boolean, default=1
        >- Flag whether to add multipath affect based on AoAsigma
        >    parameters.
        >    - 0 - return ideal AoA (absolute or differential)
        >    - 1 (default) - return random offsets characterized by
        >    AoAsigma parameters
        >
        >__meas_flag__ : Integer, default=6
        >    - Determines which measurement types are generated for
        >    a given channel.  Options are:
        >        - 0-tdoa,
        >        - 1-drss,
        >        - 2-aoa,
        >        - 3-tdoa/drss,
        >        - 4-tdoa/aoa,
        >        - 5-drss/aoa,
        >        - 6-tdoa/drss/aoa
        >
        >__diff_array__ : Boolean list, default = [1,0,0]
        >- List sets whether measurement types are differential or
        >    absolute measurements for TDOA, RSS, and AoA, e.g.,
        >    - [1,0,0] - TDOA, RSS, and AoA
        >    - [1,1,0] - TDOA, DRSS, and AoA
        >    - [1,1,1] - TDOA, DRSS, and DAoA
        >    - [tdoa_flag, drss_flag, daoa_flag]
        >
        >__seed__ : integer, default=None
        >- set for reprodducible results

        ___Returns___

        >Self, sets self.X_model
        >- Format is [n_runs]x[measurements] (sized set by meas_flag,
        >    diff_array parameters)

        """
        #get basic parameters inherent in rxtx_locations
        rxtx_locs=self.rxtx_locs
        tdoa_flag, drss_flag, daoa_flag = diff_array

        # generate delay based on Tx and Rx locations
        self.calculate_Rxxdelay(ch_delay_flag = ch_delay_flag, tdoa_flag = tdoa_flag, seed=seed)
        tde_len=self.rxx_delay.shape[1]
        Rxx_delay=self.rxx_delay

        #generate power measurements based on Tx and Rx locations
        self.calculate_RxxRssi(ch_gain_flag=ch_gain_flag, drss_flag=drss_flag, seed=seed)
        rss_len = self.rxx_rssi.shape[1]
        Rxx_rssi= self.rxx_rssi

        #generate aoa measurements based on Tx and Rx locations
        self.calculate_AoA(ch_angle_flag= ch_angle_flag, daoa_flag= daoa_flag, seed=seed)
        aoa_len=self.rxx_aoa.shape[1]
        Abs_aoa=self.rxx_aoa

        if (meas_flag == 0): X_model = Rxx_delay
        elif (meas_flag==1): X_model = Rxx_rssi
        elif (meas_flag==2): X_model = Abs_aoa
        elif (meas_flag==3): X_model = np.concatenate((Rxx_delay, Rxx_rssi),axis=1)
        elif (meas_flag==4): X_model = np.concatenate((Rxx_delay, Abs_aoa),axis=1)
        elif (meas_flag==5): X_model = np.concatenate((Rxx_rssi, Abs_aoa), axis=1)
        elif (meas_flag==6): X_model = np.concatenate((Rxx_delay, Rxx_rssi, Abs_aoa), axis=1)
        else: raise ValueError('bad meas_flag')

        #save parameters to self
        self.ch_delay_flag = ch_delay_flag
        self.ch_gain_flag = ch_gain_flag
        self.ch_angle_flag = ch_angle_flag
        self.tdoa_flag = tdoa_flag
        self.drss_flag = drss_flag
        self.daoa_flag = daoa_flag
        self.seed_Xmodel = seed
        self.X_model = X_model

        return self