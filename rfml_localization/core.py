# AUTOGENERATED! DO NOT EDIT! File to edit: 00_core.ipynb (unless otherwise specified).

__all__ = ['HFF_k_matrix', 'sklearn_kt_regressor', 'glmnet_kt_regressor']

# Cell
import numpy as np
from sklearn.base import BaseEstimator
from sklearn.utils.validation import check_X_y, check_array, check_is_fitted
from sklearn.metrics import pairwise_kernels, mean_squared_error
from sklearn.preprocessing import Normalizer
from sklearn.linear_model import Lasso
import glmnet_python; from glmnet import glmnet; from glmnetPredict import glmnetPredict


# Cell
def HFF_k_matrix(fml = None,
                 fm = np.array([]),
                 kernel='laplacian',
                 num_meas_array = np.array([]),
                 varMs = np.array([])
                ):
    """ Function to generate a kernelized matrix.  The kernel used
    defaults to laplacian (manhattan distance).

    ___Parameters___


    >__fml__ : ndarray of shape (n_examples, n_features)
    >- dictionary of reference measurements/observations with format of
    >        [num_runs * n_types of measurements]x[measurements/features]
    >
    >__fm__ : ndarray of shape (n_examples, n_features), optional
    >- set of measurements/observations of same format as fml
    >
    >__kernel__ : str, default = 'laplacian'
    >- This determines kernel - see scikit-learn's pairwise kernels
    >    function. Values typically used here are 'rbf' and 'laplacian'
    >    with other values including [‘additive_chi2’, ‘chi2’, ‘linear’,
    >    ‘poly’, ‘polynomial’, ‘sigmoid’, ‘cosine’]
    >
    >__num_meas_array__ : ndarray of shape  (n_types of measurements,), default = np.array([])
    >- numpy array that provides the number of each type of measurements
    >    (112ea TDOA, 16ea RSS, 8ea AoA is np.array([112,16,8])).  Note
    >    that if single total number or empty array of measurements
    >    then defaults to simply pairwise_kernel for entire dictionary.
    >
    >__varMs__ : ndarray of shape (n_types of measurements,), default = np.array([])
    >- scale factor for kernel/similarity measurement of each
    >    measurement type. It can be related to variance of each
    >    measurement type.

    __Returns__

    >returns a kernel matrix (k_matrix)
    """
    #initialize some values and check entries
    if (np.size(num_meas_array) != np.size(varMs)):
        raise ValueError("Number of scales,{:d}, doesn't match number of feature types, {:d}".format(np.size(num_meas_array),np.size(varMs)))
    #check to see if 'new' measurements, if not, use reference measurements only
    if fm.size == 0:
        fm = fml
    #if number of measurements is not passed, then only one type of measurements
    if num_meas_array.size == 0:
        num_meas_array = np.array([np.size(fml.shape[1])])
    #if none passed, set all scales to one
    if varMs.size == 0:
        varMs = np.ones(num_meas_array.size)

    #basic parameter settings
    num_features = len(num_meas_array);

    idx = np.cumsum(num_meas_array)

    #calculate kernel matrix
    #calculate kernel matrix for first measurement type
    k_matrix = pairwise_kernels(fm[:,0:idx[0]],fml[:,0:idx[0]],
                               metric = kernel,
                               gamma = varMs[0])
    #loop through rest of measurement types, calculate kernels and concatenate them
    for m in np.arange(num_features-1):
        k_matrix = np.hstack((k_matrix, pairwise_kernels(fm[:,idx[m]:idx[m+1]],fml[:,idx[m]:idx[m+1]],
                               metric = kernel,
                               gamma = varMs[m+1])
                             ))
    return k_matrix

# Cell
class sklearn_kt_regressor(BaseEstimator):
    """
    This is kernel trick regressor model class based on Sci-Kit Learn's
    base estimator class. Estimator wraps any passed SKLearn model along
    with kernel parameters which allows leveraging SKLearn tools and
    methods for optimizing and tuning kernel trick models.

    __Parameters__

    >__skl_model__ : SKLearn estimator object, default = Lasso()
    >- Typical models used are Ridge() and Lasso() for regression
    >
    >__skl_kernel__ : str, default = 'laplacian'
    >- This determines kernel used in kernel trick - see scikit-learn's
    > pairwise kernels function. Values typically used here are 'rbf'
    > and 'laplacian' with other values including [‘additive_chi2’,
    > ‘chi2’, ‘linear’, ‘poly’, ‘polynomial’, ‘sigmoid’, ‘cosine’]
    >
    >__n_kernels__ : integer, default = 1
    >- Number of kenerls concatenated together in kernel trick
    >
    >__kernel_s1-s3__ : float, default = 1e-3, None, None
    >- Kernel scales applied to each of the `skl_kernel`s.  The total
    > number of kernels deteremined by `kernel_scales`
    >
    >__n_meas_array__ : integer ndarray, default = np.array([])
    >- ndarray that provides the number of each type of measurements
    >    (112ea TDOA, 16ea RSS, 8ea AoA is np.array([112,16,8])).  Note
    >    that if one measurement then defaults to simply pairwise_kernel
    >    for entire dictionary.
    """

    def __init__(self, skl_model=Lasso(), skl_kernel='laplacian', n_kernels=1,
                 kernel_s0 = 1e-3, kernel_s1 = None, kernel_s2 = None,
                 n_meas_array=np.array([])):
        self.skl_model = skl_model
        self.skl_kernel = skl_kernel
        self.n_kernels = n_kernels
        self.kernel_s0 = kernel_s0
        self.kernel_s1 = kernel_s1
        self.kernel_s2 = kernel_s2
        self.n_meas_array = n_meas_array

    def fit(self, X, y):
        """
        Kernelizes passed data and then fits data according to passed
        model.  Function inherits all attributes and features of
        SKLearn's base esimator class as well as passed model.

        __Parameters__

        > __X__ : ndarray of shape (n_samples, n_features)
        >- Training data
        >
        > __y__ : ndarray of shape (n_samples, spatial dimensions)
        >- Response data (location of Tx for each sample set
        >  of measurements)

        __Returns__

        > Self, sets self.X_, self.Y_

        """

        # Check that X and y have correct shape
        X, y = check_X_y(X, y, multi_output=True)
        # Check that number of kernels and number of kernel scales is same
        if self.n_kernels != len(self.n_meas_array):
            raise ValueError("n_kernels is not same as number of n_meas_array")
        # Check that number of each measurement types is correct
        if sum(self.n_meas_array) != X.shape[1]:
            raise ValueError("Sum of n_meas_array is not same as number of features in X")

        #put kernel scales together (reset in case called multiple times)
        kernel_scales = np.array([self.kernel_s0])
        for i in range(1,self.n_kernels):
            kernel_scales = np.append(kernel_scales,self.get_params()["kernel_s"+str(i)])

        # Generate kernelized matrix for fit input
        X_kernel = HFF_k_matrix(fml=X, kernel=self.skl_kernel,
                                num_meas_array=self.n_meas_array,
                                varMs=kernel_scales)
        #normalize
        X_kernel = Normalizer().fit_transform(X_kernel)

        # Fit
        self.skl_model.fit(X_kernel, y)

        # Store X,y seen during fit
        self.X_ = X
        self.y_ = y

        # Return the regressor
        return self

    def predict(self, X):
        """
        Applies pair-wise kernel between observed with fitted data.  The
        predicts based on fitted model.

        __Parameters__

        > __X__ : ndarray of shape (n_samples, n_features)
        >- Sample data used for predictions
        >

        __Returns__

        > Estimated target(s)

        """

        # Check is fit had been called
        check_is_fitted(self)

        # Input validation
        X = check_array(X)

        #put kernel scales together (reset in case called multiple times)
        kernel_scales = np.array([self.kernel_s0])
        for i in range(1,self.n_kernels):
            kernel_scales = np.append(kernel_scales,self.get_params()["kernel_s"+str(i)])

        #kernelize input
        X_kernel = HFF_k_matrix(fml=self.X_, fm=X,
                        kernel=self.skl_kernel,
                        num_meas_array=self.n_meas_array,
                        varMs=kernel_scales)
        #normalize
        X_kernel = Normalizer().fit_transform(X_kernel)

        #predict and return
        return self.skl_model.predict(X_kernel)

# Cell
class glmnet_kt_regressor(BaseEstimator):
    """
    This is kernel trick regressor model class based on Sci-Kit Learn's
    base estimator class. Estimator wraps a GLMnet model along
    with kernel parameters which allows leveraging SKLearn tools and
    methods for optimizing and tuning kernel trick models.

    See [Glmnet Vignette](https://glmnet-python.readthedocs.io/en/latest/glmnet_vignette.html)
    for indepth information on GLMnet model.

    __Parameters__

    >__glm_alpha__ : float, default = 1
    >- glmnet elasticnet parameter where
    >    - 0 is Ridge regressino
    >    - 1 is Lasso
    >    - (0,1) is ElasticNet
    >
    >__lambdau__ : float, default = 1e-3
    >- lambda for penalty (aka alpha in SKLearn). Note that this is
    > converted to an ndarray internally due GLMnet accepting an
    > array of lambda's.  **This is not supported with this wrapper!**
    >
    >__skl_kernel__ : str, default = 'laplacian'
    >- This determines kernel used in kernel trick - see scikit-learn's
    > pairwise kernels function. Values typically used here are 'rbf'
    > and 'laplacian' with other values including [‘additive_chi2’,
    > ‘chi2’, ‘linear’, ‘poly’, ‘polynomial’, ‘sigmoid’, ‘cosine’]
    >
    >__n_kernels__ : integer, default = 1
    >- Number of kenerls concatenated together in kernel trick
    >
    >__kernel_scales__ : integer ndarray, default = np.array([])
    >- Kernel scales applied to each of the `skl_kernel`.  The total
    > number of kernels deteremined by `kernel_scales`
    >
    >__n_meas_array__ : integer ndarray, default = np.array([])
    >- ndarray that provides the number of each type of measurements
    >    (112ea TDOA, 16ea RSS, 8ea AoA is np.array([112,16,8])).  Note
    >    that if one measurement then defaults to simply pairwise_kernel
    >    for entire dictionary.
    >
    >__glmnet_args__ : dictionary, default = {}
    >- parameters for underlying GLMnet object
    """

    def __init__(self, glm_alpha=1, lambdau=1e-3, skl_kernel='laplacian', n_kernels=1,
                 kernel_s0 = 1e-3, kernel_s1 = None, kernel_s2 = None,
                 n_meas_array=np.array([]), glmnet_args = {}):
        self.glm_alpha=glm_alpha
        self.lambdau=lambdau
        self.skl_kernel = skl_kernel
        self.n_kernels = n_kernels
        self.kernel_s0 = kernel_s0
        self.kernel_s1 = kernel_s1
        self.kernel_s2 = kernel_s2
        self.n_meas_array = n_meas_array
        self.glmnet_args = glmnet_args

    def set_glmnet_args(self, glmnet_args):
        """Enables setting any of glmnet params except alpha and lambdau
        initialized in class instance.  For alpha and lambdau, use
        inherited set_params().

        __Parameter__

        > __glmnet_args__ : dictionary
        >- dictionary of arguments to pass to glmnet

        """

        self.glmnet_args={**self.glmnet_args,**glmnet_args}

        return self

    def fit(self, X, y):
        """
        Kernelizes passed data and then fits data according to passed
        model.  Function inherits all attributes and features of
        SKLearn's base esimator class as well as passed model.

        __Parameters__

        > __X__ : ndarray of shape (n_samples, n_features)
        >- Training data
        >
        > __y__ : ndarray of shape (n_samples, spatial dimensions)
        >- Response data (location of Tx for each sample set
        >  of measurements)

        __Returns__

        > Self, sets self.X_, self.Y_

        """

        # Check that X and y have correct shape
        X, y = check_X_y(X, y, multi_output=True)
        # Check that number of kernels and number of kernel scales is same
        if self.n_kernels != len(self.n_meas_array):
            raise ValueError("n_kernels is not same as number of n_meas_array")
        # Check that number of each measurement types is correct
        if sum(self.n_meas_array) != X.shape[1]:
            raise ValueError("Sum of n_meas_array is not same as number of features in X")

        #put lambdau into ndarray
        self.lambdau = np.array([self.lambdau])
        #put kernel scales together (reset in case called multiple times)
        kernel_scales = np.array([self.kernel_s0])
        for i in range(1,self.n_kernels):
            kernel_scales = np.append(kernel_scales,self.get_params()["kernel_s"+str(i)])

        # Generate kernelized matrix for fit input
        X_kernel = HFF_k_matrix(fml=X, kernel=self.skl_kernel,
                                num_meas_array=self.n_meas_array,
                                varMs=kernel_scales)
        #normalize
        X_kernel = Normalizer().fit_transform(X_kernel)

        # Fit
        self.glmnet_model = glmnet(x = X_kernel, y = y.copy(), alpha = self.glm_alpha,
                                     lambdau = self.lambdau, **self.glmnet_args)

        # Store X,y seen during fit
        self.X_ = X
        self.y_ = y

        # Return the regressor
        return self

    def predict(self, X):
        """
        Applies pair-wise kernel between observed with fitted data.  The
        predicts based on fitted model.

        __Parameters__

        > __X__ : ndarray of shape (n_samples, n_features)
        >- Sample data used for predictions
        >

        __Returns__

        > Estimated target(s)

        """

        # Check is fit had been called
        check_is_fitted(self)

        # Input validation
        X = check_array(X)

        #put kernel scales together (reset in case called multiple times)
        kernel_scales = np.array([self.kernel_s0])
        for i in range(1,self.n_kernels):
            kernel_scales = np.append(kernel_scales,self.get_params()["kernel_s"+str(i)])

        #kernelize input
        X_kernel = HFF_k_matrix(fml=self.X_, fm=X,
                        kernel=self.skl_kernel,
                        num_meas_array=self.n_meas_array,
                        varMs=kernel_scales)
        #normalize
        X_kernel = Normalizer().fit_transform(X_kernel)

        #predict and return
        #glmnet returns with extra dimension, squeeze to remove
        return np.squeeze(glmnetPredict(self.glmnet_model, X_kernel))