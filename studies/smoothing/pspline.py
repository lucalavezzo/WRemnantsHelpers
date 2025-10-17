# Let's create an N-dimensional version using the ndsplines and scipy approaches
# First, let's implement the core N-dimensional tensor product structure

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import spsolve
from scipy.interpolate import BSpline
import warnings
from itertools import product
from functools import reduce

"""
Fit a histogram from a narf file with PySR.
"""

import os, sys
import argparse
from datetime import datetime
import h5py
import numpy as np
import copy
import hist
import matplotlib.pyplot as plt
import itertools

sys.path.append("../../WRemnants/")

from wums import ioutils
from wums import output_tools
from wums import plot_tools
from wums import boostHistHelpers as hh
from utilities import parsing

def load_results_h5py(h5file):
    if "results" in h5file.keys():
        return ioutils.pickle_load_h5py(h5file["results"])
    else:
        return {k: ioutils.pickle_load_h5py(v) for k, v in h5file.items()}

parser = argparse.ArgumentParser(
    description="Read in a hdf5 file."
)
parser.add_argument(
    "infile",
    type=str,
    help="hdf5 file.",
)
parser.add_argument(
    "--checkpoint",
    type=str,
    default=None,
    help="Directory containing checkpoint.pkl from which to initialize a regressor."
    "Will start training from this checkpoint, inheriting regressor parameters,"
    "but will impose this script's arguments to the regressor."
    "Will overwrite the existing checkpoint.pkl.",
)
parser.add_argument(
    "--select",
    nargs="+",
    dest="selection",
    type=str,
    default=None,
    help="Apply a selection to the histograms, if the axis exists."
    "This option can be applied to any of the axis, not necessarily one of the fitaxes, unlike --axlim."
    "Use complex numbers for axis value, integers for bin number."
    "e.g. --select 'ptll 0 10"
    "e.g. --select 'ptll 0j 10j",
)
parser.add_argument(
    "--refHistSelect",
    nargs="+",
    dest="refHistSelection",
    type=str,
    default=None,
    help="Apply a selection to the reference histogram, if the axis exists."
    "If left empty, the --select will apply to the reference hist."
)
parser.add_argument(
    "--hist",
    type=str,
    default="nominal",
    help="Histogram to fit."
)
parser.add_argument(
    "--refHist",
    type=str,
    default=None,
    help="Fit the ratio of --hist to --refHist."
)
parser.add_argument(
    "--axes",
    nargs="+",
    type=str,
    default=["ptll"],
    help="Axes to fit."
)
parser.add_argument(
    "--plotAxes",
    nargs="+",
    type=str,
    default=None,
    help="Axes to plot."
)
parser.add_argument(
    "--sample",
    type=str,
    default="ZmumuPostVFP",
    help="Sample to fit."
)
parser.add_argument(
    "-l",
    "--lam",
    default=1000,
    help="Lambda value."
)
parser.add_argument(
    "-k",
    "--knots-per-axis",
    nargs="+",
    default=None,
    help="Knots per axis value."
)
parser.add_argument(
    "-d",
    "--degree",
    default=3,
    help="Degree value."
)
parser.add_argument(
    "--rrange",
    default=(0.5, 1.5),
    type=float,
    nargs=2,
    help="Range for the ratio plot (default: 0.5, 1.5).",
)
parser.add_argument(
    "--ylim",
    nargs=2,
    type=float,
    default=None,
    help="y limits."
)
parser.add_argument(
    "-o",
    "--outdir",
    type=str,
    default="./",
    required=False,
    help="Output directory for the plots. Default is current directory.",
)
parser.add_argument(
    "-p",
    "--postfix",
    type=str,
    default=None,
    help="Postfix to add to the output file names.",
)
parser.add_argument(
    "--forceName",
    action='store_true',
    help="Force output name.",
)
args = parser.parse_args()


with h5py.File(args.infile, "r") as h5file:
    results = load_results_h5py(h5file)
    print(f"Samples in file: {results.keys()}\n")
    h = results[args.sample]['output'][args.hist].get()
    if args.refHist:
        h_ref = results[args.sample]['output'][args.refHist].get()

# needed for the weights
if h.storage_type != hist.storage.Weight and h.storage_type != hist.storage.Double:
    raise Exception()

# prepare the histogram
def prepare_hist(_h, axes, selection):
    for sel in selection:
        sel = sel.split()
        if len(sel) == 3:
            sel_ax, sel_lb, sel_ub = sel
            sel_lb = parsing.str_to_complex_or_int(sel_lb)
            sel_ub = parsing.str_to_complex_or_int(sel_ub)
            _h = _h[{sel_ax: slice(sel_lb, sel_ub, sum)}]
        elif len(sel) == 2:
            sel_ax, sel_val = sel
            try:
                sel_val = parsing.str_to_complex_or_int(sel_val)
            except argparse.ArgumentTypeError as e:
                print(e)
                print("Trying to use as string...")
                pass
            _h = _h[{sel_ax: sel_val}]
    if axes:
        _h = _h.project(*axes)
    _h_unroll = hh.unrolledHist(_h, binwnorm=1)
    _h_unroll = hh.normalize(_h_unroll, scale=1)
    return _h, _h_unroll

h, h_unroll = prepare_hist(h, args.axes, args.selection)
if args.refHist:
    h_ref, _ = prepare_hist(h_ref, args.axes, args.refHistSelection if args.refHistSelection else args.selection)
    h = hh.divideHists(h, h_ref)


def smooth_boost_histogram_nd_psplines(hist, lambda_smoothing=1000.0, degree=3, knots_per_axis=None):
    """
    Smooth an N-dimensional boost histogram using penalized B-splines (P-splines).
    
    This function implements tensor product P-splines for smoothing histograms of arbitrary
    dimensionality while preserving the underlying structure and reducing statistical 
    fluctuations. The method uses efficient Kronecker product operations to handle 
    high-dimensional cases.
    
    Parameters:
    -----------
    hist : boost_histogram.Histogram
        The input histogram to smooth. Supports arbitrary dimensions.
    lambda_smoothing : float or array-like, default=1000.0
        Regularization parameter(s) controlling the smoothness-fidelity trade-off.
        - Higher values produce smoother results
        - Can be a single value (same smoothing for all dimensions) or array with 
          one value per dimension for dimension-specific control
        - Typical range: 100-10000 depending on histogram statistics
    degree : int or array-like, default=3
        Degree of B-splines. Can be single value for all dimensions or array 
        with one value per dimension. 3 = cubic splines (recommended).
    knots_per_axis : int or list, optional
        Number of interior knots per axis. If None, automatically determined as
        min(n_bins//3, 15) for each axis, with minimum of 4 knots.
    
    Returns:
    --------
    smoothed_values : ndarray
        Smoothed histogram values with same shape as input hist.view()
    spline_function : callable
        Function that can evaluate the smoothed histogram at arbitrary points.
        Usage: spline_function(x1, x2, ..., xN) or spline_function([x1, x2, ..., xN])
        
    Examples:
    ---------
    >>> # 3D histogram
    >>> hist_3d = bh.Histogram(
    ...     bh.axis.Regular(20, -2, 2),
    ...     bh.axis.Regular(15, -1, 1), 
    ...     bh.axis.Regular(10, 0, 3)
    ... )
    >>> smoothed_3d, spline_3d = smooth_boost_histogram_nd_psplines(
    ...     hist_3d,
    ...     lambda_smoothing=[1000, 800, 1200],  # Different per axis
    ...     knots_per_axis=[8, 6, 4]
    ... )
    >>> 
    >>> # Evaluate at a point
    >>> value = spline_3d(0.5, 0.2, 1.5)
    >>> 
    >>> # 4D+ histograms work the same way
    >>> hist_4d = bh.Histogram(...)
    >>> smoothed_4d, spline_4d = smooth_boost_histogram_nd_psplines(hist_4d)
    
    Notes:
    ------
    - Memory complexity scales as O(prod(n_knots_i)) where n_knots_i are knots per axis
    - For very high dimensions (>6), consider reducing knots_per_axis significantly
    - The method preserves total histogram normalization
    - Uses sparse matrix operations for efficiency in high dimensions
    
    """
    
    # Input validation
    if not hasattr(hist, 'view') or not hasattr(hist, 'axes'):
        raise ValueError("Input must be a boost_histogram.Histogram object")
    
    # Extract data from boost histogram
    values = hist.values()
    axes = hist.axes
    ndim = len(axes)
    
    if ndim == 0:
        raise ValueError("Cannot smooth 0D histogram")
    
    if ndim > 10:
        warnings.warn(f"Smoothing {ndim}D histogram may be computationally intensive. "
                     f"Consider reducing knots_per_axis for better performance.")
    
    print(f"Processing {ndim}D histogram with shape: {values.shape}")
    
    # Validate and process lambda_smoothing parameters
    if np.isscalar(lambda_smoothing):
        lambdas = [float(lambda_smoothing)] * ndim
    else:
        lambdas = list(lambda_smoothing)
        if len(lambdas) != ndim:
            raise ValueError(f"lambda_smoothing must be scalar or have {ndim} elements")
    
    if any(l <= 0 for l in lambdas):
        raise ValueError("All lambda_smoothing values must be positive")
    
    # Validate and process degree parameters
    if np.isscalar(degree):
        degrees = [int(degree)] * ndim
    else:
        degrees = [int(d) for d in degree]
        if len(degrees) != ndim:
            raise ValueError(f"degree must be scalar or have {ndim} elements")
    
    if any(d < 1 or d > 5 for d in degrees):
        raise ValueError("All degree values must be between 1 and 5")
    
    # Set default number of knots
    if knots_per_axis is None:
        knots_per_axis = []
        for ax in axes:
            n_bins = len(ax.centers)
            # For higher dimensions, use fewer knots to control memory
            base_knots = max(4, min(n_bins // 3, 15))
            if ndim > 4:
                base_knots = max(4, min(n_bins // 4, 10))
            if ndim > 6:
                base_knots = max(3, min(n_bins // 5, 8))
            knots_per_axis.append(base_knots)
    elif np.isscalar(knots_per_axis):
        knots_per_axis = [int(knots_per_axis)] * ndim
    else:
        knots_per_axis = [int(k) for k in knots_per_axis]
        if len(knots_per_axis) != ndim:
            raise ValueError(f"knots_per_axis must be scalar or have {ndim} elements")
    
    # Validate knots
    for i, (ax, n_knots, deg) in enumerate(zip(axes, knots_per_axis, degrees)):
        if n_knots < max(3, deg):
            raise ValueError(f"Need at least max(3, degree) = {max(3, deg)} knots per axis, "
                           f"got {n_knots} for axis {i}")
        if n_knots >= len(ax.centers):
            warnings.warn(f"Number of knots ({n_knots}) for axis {i} is close to number of bins "
                         f"({len(ax.centers)}). Consider reducing knots_per_axis.")
    
    # Estimate memory requirements and warn if excessive
    total_basis_functions = np.prod([k + d + 1 for k, d in zip(knots_per_axis, degrees)])
    estimated_memory_gb = (total_basis_functions ** 2 * 8) / (1024**3)  # 8 bytes per float64
    
    if estimated_memory_gb > 100.0:
        warnings.warn(f"Estimated memory requirement: {estimated_memory_gb:.1f} GB. "
                     f"Consider reducing knots_per_axis for dimensions with many knots.")
    
    print(f"Using knots per axis: {knots_per_axis}")
    print(f"Using lambda values: {lambdas}")
    print(f"Using degrees: {degrees}")
    print(f"Total basis functions: {total_basis_functions}")
    
    # Get bin centers
    centers = [ax.centers for ax in axes]
    
    try:
        return _smooth_nd_psplines_tensor(values, centers, lambdas, degrees, knots_per_axis)
    except (np.linalg.LinAlgError, MemoryError) as e:
        raise RuntimeError(f"Failed to solve N-D P-splines system. Try reducing knots_per_axis "
                          f"or lambda_smoothing values. Original error: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error during N-D smoothing: {e}")

def _create_nd_knot_vectors(centers_list, knots_per_axis, degrees):
    """Create knot vectors for all dimensions."""
    knot_vectors = []
    for centers, n_knots, degree in zip(centers_list, knots_per_axis, degrees):
        x_min, x_max = centers[0], centers[-1]
        # Add small padding to avoid boundary issues
        padding = (x_max - x_min) * 1e-10
        x_min -= padding
        x_max += padding
        
        # Interior knots
        interior_knots = np.linspace(x_min, x_max, n_knots + 2)[1:-1]
        
        # Full knot vector with repeated end knots
        knots = np.concatenate([
            [x_min] * (degree + 1),
            interior_knots,
            [x_max] * (degree + 1)
        ])
        knot_vectors.append(knots)
    
    return knot_vectors

def _build_nd_design_matrices(centers_list, knot_vectors, degrees):
    """Build 1D design matrices for each dimension."""
    design_matrices = []
    
    for centers, knots, degree in zip(centers_list, knot_vectors, degrees):
        n_basis = len(knots) - degree - 1
        B = np.zeros((len(centers), n_basis))
        
        for i, x in enumerate(centers):
            for j in range(n_basis):
                try:
                    basis_spline = BSpline.basis_element(knots[j:j+degree+2])
                    B[i, j] = basis_spline(x)
                except:
                    B[i, j] = 0.0
        
        design_matrices.append(B)
    
    return design_matrices

def _build_nd_penalty_matrices(n_basis_list):
    """Build penalty matrices for each dimension."""
    penalty_matrices = []
    
    for n_basis in n_basis_list:
        # Second-order difference penalty
        if n_basis <= 2:
            # For very small basis, use identity penalty
            P = np.eye(n_basis)
        else:
            D = np.diff(np.eye(n_basis), n=2, axis=0)
            P = D.T @ D
        penalty_matrices.append(P)
    
    return penalty_matrices

def _kronecker_chain(matrices):
    """Compute Kronecker product of a list of matrices efficiently."""
    if len(matrices) == 1:
        return matrices[0]
    elif len(matrices) == 2:
        return sp.kron(matrices[0], matrices[1])
    else:
        # Build Kronecker product iteratively for efficiency
        result = matrices[0]
        for mat in matrices[1:]:
            result = sp.kron(result, mat)
        return result

def _smooth_nd_psplines_tensor(values, centers_list, lambdas, degrees, knots_per_axis):
    """Core N-dimensional P-splines smoothing using tensor products."""
    
    ndim = len(centers_list)
    
    # Create knot vectors
    knot_vectors = _create_nd_knot_vectors(centers_list, knots_per_axis, degrees)
    
    # Build design matrices for each dimension
    design_matrices = _build_nd_design_matrices(centers_list, knot_vectors, degrees)
    
    # Get number of basis functions per dimension
    n_basis_list = [B.shape[1] for B in design_matrices]
    
    # Build penalty matrices
    penalty_matrices = _build_nd_penalty_matrices(n_basis_list)
    
    print(f"Building {ndim}D tensor system...")
    
    # Vectorize the data (flatten in a way consistent with Kronecker structure)
    # For N-D tensor products, we need to be careful about axis ordering
    y_vec = values.flatten('C')  # C-order (row-major) flattening

    # Build tensor product design matrix using Kronecker products
    # B_total = B_0 ⊗ B_1 ⊗ ... ⊗ B_{n-1}
    print("Building tensor design matrix...")
    B_matrices_sparse = [sp.csr_matrix(B) for B in design_matrices]
    B_tensor = _kronecker_chain(B_matrices_sparse)
    
    print(f"Design matrix shape: {B_tensor.shape}")
    
    # Build penalty matrix using Kronecker products
    # For each dimension i, we add lambda_i * (I ⊗ ... ⊗ I ⊗ P_i ⊗ I ⊗ ... ⊗ I)
    print("Building penalty matrices...")
    
    # Start with zero penalty matrix
    total_penalty = sp.csr_matrix((np.prod(n_basis_list), np.prod(n_basis_list)))
    
    for dim, (lam, P) in enumerate(zip(lambdas, penalty_matrices)):
        if lam > 0:
            # Build Kronecker product for this dimension's penalty
            identity_matrices = []
            for d in range(ndim):
                if d == dim:
                    identity_matrices.append(sp.csr_matrix(P))
                else:
                    identity_matrices.append(sp.eye(n_basis_list[d]))
            
            P_tensor = _kronecker_chain(identity_matrices)
            total_penalty += lam * P_tensor
    
    print("Solving penalized system...")
    
    # Solve the penalized least squares system
    # (B^T B + P_total) c = B^T y
    A = B_tensor.T @ B_tensor + total_penalty
    b = B_tensor.T @ y_vec
    
    # Ensure A is in proper sparse format for solver
    A = A.tocsr()
    
    # Solve the system
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", sp.SparseEfficiencyWarning)
        coefficients = spsolve(A, b)
    
    # Compute smoothed values
    print("Computing smoothed values...")
    smoothed_vec = B_tensor @ coefficients
    # smoothed_values = smoothed_vec.reshape(values.shape, order='C')
    smoothed_values = smoothed_vec.reshape(values.shape)
    
    # Create N-dimensional evaluation function
    def spline_nd_func(*args):
        """
        Evaluate N-D spline at given points.
        
        Args can be:
        - spline_nd_func(x1, x2, ..., xN) for individual coordinates
        - spline_nd_func([x1, x2, ..., xN]) for array of coordinates
        """
        if len(args) == 1 and hasattr(args[0], '__len__') and len(args[0]) == ndim:
            # Single point as array
            eval_points = [np.atleast_1d(args[0][i]) for i in range(ndim)]
        elif len(args) == ndim:
            # Individual coordinates
            eval_points = [np.atleast_1d(arg) for arg in args]
        else:
            raise ValueError(f"Expected {ndim} coordinates or single {ndim}-element array")
        
        # Check that all coordinate arrays have the same length
        n_points = len(eval_points[0])
        if not all(len(pts) == n_points for pts in eval_points):
            raise ValueError("All coordinate arrays must have the same length")
        
        # Evaluate each 1D basis at the given points
        basis_values = []
        for dim, (points, knots, degree) in enumerate(zip(eval_points, knot_vectors, degrees)):
            basis_vals = np.zeros((n_points, n_basis_list[dim]))
            for i, x in enumerate(points):
                for j in range(n_basis_list[dim]):
                    try:
                        basis_spline = BSpline.basis_element(knots[j:j+degree+2])
                        basis_vals[i, j] = basis_spline(x)
                    except:
                        basis_vals[i, j] = 0.0
            basis_values.append(basis_vals)
        
        # Compute tensor product evaluation
        # For each point, compute the product of all 1D basis values
        result = np.zeros(n_points)
        
        # Reshape coefficients for tensor evaluation
        coeff_tensor = coefficients.reshape(n_basis_list, order='C')
        
        for pt_idx in range(n_points):
            # Get basis values for this point in all dimensions
            pt_basis = [basis_vals[pt_idx, :] for basis_vals in basis_values]
            
            # Compute tensor contraction: sum over all basis indices
            val = 0.0
            for indices in product(*[range(n) for n in n_basis_list]):
                # Product of basis values for these indices
                basis_prod = np.prod([pt_basis[dim][idx] for dim, idx in enumerate(indices)])
                # Add contribution from this basis combination
                val += coeff_tensor[indices] * basis_prod
            
            result[pt_idx] = val
        
        return result[0] if n_points == 1 else result
    
    print("N-D smoothing completed successfully!")
    
    return smoothed_values, spline_nd_func

smoothed_values, spline_nd_func = smooth_boost_histogram_nd_psplines(
    h,
    lambda_smoothing=args.lam,
    degree=args.degree,
    knots_per_axis=args.knots_per_axis
)
h_pred = copy.deepcopy(h)
h_pred.values()[...] = smoothed_values

if args.plotAxes:
    h_pred = h_pred.project(*args.plotAxes)
    h_pred = hh.normalize(h_pred, scale=np.prod(h_pred.values().shape))
    h = h.project(*args.plotAxes)
    h = hh.normalize(h, scale=np.prod(h_pred.values().shape))

h_pred_unroll = hh.unrolledHist(h_pred)
h_unroll = hh.unrolledHist(h)

label = f"p-spline smoothed\n$\\lambda$={args.lam}, knots per axis={args.knots_per_axis}, degree={args.degree}"
fig = plot_tools.makePlotWithRatioToRef(
    [h_unroll, h_pred_unroll],
    ["Data", label],
    ["black", "red"],
    xlabel="Bin",
    ylim=args.ylim,
    yerr=False,
    base_size=10,
    rrange=[args.rrange],
)        
if not os.path.isdir(args.outdir):
    os.makedirs(args.outdir)
plot_tools.save_pdf_and_png(args.outdir, f"results_pspline_{args.postfix}" if args.postfix else f"results_pspline", fig)

# unique identifier to store run results, input histogram
run_id = datetime.now().strftime("%y%m%d_%H%M")
if args.forceName:
    run_id = f"{args.postfix}"
elif args.postfix:
    run_id += f"_{args.postfix}"

odir = os.path.join("pspline", f"{run_id}")
if not os.path.isdir(odir):
    os.makedirs(odir)
output_tools.write_lz4_pkl_output(
    os.path.join(odir, "hist"),
    "output",
    {
        "h_pred":h_pred, "h_pred_unroll": h_pred_unroll, "isratio": True if args.refHist else False,
        "h":h, "h_unroll":h_unroll, "lambda": args.lam, "knots": args.knots_per_axis, "degree": args.degree
    },
    "./",
    args
)