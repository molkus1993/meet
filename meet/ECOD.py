"""
Submodule of the Modular EEg Toolkit - MEET for Python.

Implements the extended complete orthogonal decomposition and a least
squares algorithm based on it.

"Robust extreme learning machine", Horata, Chiewchanwattana, Sunat et al.,
Neurocomputing 102 (2013) 31-44

ECOD_LS solves the system Ax = b

For rank-deficient matrix A, the solution x using ECOD_LS has smaller norm
than that of np.lstsq and is computationally more efficient than SVD.

Matlab source code for trap2tri:

https://github.com/carandraug/testmatrix/blob/master/Test%20Matrix%20Toolbox/trap2tri.m
"""


if __name__ != "__main__":
    from . import _np
    from . import _linalg
else:
    import numpy as _np
    import scipy.linalg as _linalg

def ECOD_LS(A, b):
    """
    Solve the system Ax = b for x using the
    extended complete orthogonal decomposition
    """
    if not type(A) == _np.ndarray:
        raise TypeError('A must be numpy array')
    if not A.dtype == _np.float64:
        raise TypeError('A must be an array of float64')
    if not A.ndim == 2:
        raise TypeError('A must be 2d')
    if not _np.all(_np.isfinite(A)):
        raise TypeError('all elements in A must be finite')
    m,n = A.shape
    ######################################################
    if not type(b) == _np.ndarray:
        raise TypeError('b must be numpy array')
    if not b.dtype == _np.float64:
        raise TypeError('b must be an array of float64')
    if not b.ndim <= 2:
        raise TypeError('A must be 1d or 2d')
    if not _np.all(_np.isfinite(b)):
        raise TypeError('all elements in A must be finite')
    if not b.shape[0] == m:
        raise ValueError('1st dim of b must be first dim of A')
    ######################################################
    Q, R, V, rank = ECOD(A, check=False)
    if m >= n:
        x = V[:rank].T.dot(_np.linalg.solve(R, Q[:,:rank].T.dot(b)))
    else:
        x = V[:,:rank].dot(_np.linalg.solve(R, Q[:,:rank].T.dot(b)))
    return x

def ECOD(A, check=True):
    """
    The extended complete orthogonal decomposition
    """
    ########################
    # checking the array A #
    ########################
    if check:
        if not type(A) == _np.ndarray:
            raise TypeError('A must be numpy array')
        if not A.dtype == _np.float64:
            raise TypeError('A must be an array of float64')
        if not A.ndim == 2:
            raise TypeError('A must be 2d')
        if not _np.all(_np.isfinite(A)):
            raise TypeError('all elements in A must be finite')
    ########################
    # Step 1: rank-revealing qr decomposition
    m, n = A.shape
    Q, Z, P = _linalg.qr(A, pivoting=True, mode='economic')
    rank = _np.sum(_np.abs(_np.diag(Z)) >=
            (_np.abs(Z[0,0])*_np.finfo(Z.dtype).eps*_np.max(A.shape)))
    # Step 2
    if rank == n:
        # case 3 in the publication
        # keep R from the qr decomposition
        V = _np.eye(n)[P]
        R = Z[:rank]
    else:
        PP = _np.argsort(P)
        L = Z[:rank].T
        if m >= n:
            # first case in the publication
            # householder transformations trap2tri
            Q1, U = trap2tri(L, check=False)
            V = Q1[:,PP]
            R = U.T
        else:
            # m < n and rank != n, case 2 in the publication
            # qr decomposition
            Q1, U = _linalg.qr(L, mode='economic')
            V = Q1[PP]
            R = U.T
    return Q, R, V, rank

def trap2tri(L, overwrite=False, check=False):
    """
    Unitary reduction of trapezoidal matrix to triangular form.
    Q, T = TRAP2TRI(L), where L is an m-by-n lower trapezoidal
    matrix with m >= n, produces a unitary Q such that QL = [T; 0],
    where T is n-by-n and lower triangular.
    Q is a product of Householder transformations.
    Matlab source code for trap2tri:

    https://github.com/carandraug/testmatrix/blob/master/Test%20Matrix%20Toolbox/trap2tri.m
    """
    if check:
        # test that L is a lower trapezoidal matrix
        if not type(L) == _np.ndarray:
            raise TypeError('L must be numpy array')
        if not L.dtype == _np.float64:
            raise TypeError('L must be an array of float64')
        if not L.ndim == 2:
            raise TypeError('L must be 2d')
        if not _np.all(_np.isfinite(L)):
            raise TypeError('all elements in L must be finite')
    n,r = L.shape
    if check:
        if r > n:
            raise TypeError('1st dim of L must be >= 2nd dim')
        if not _np.allclose(L - _np.tril(L),0):
            raise TypeError('L must be lower trigonal or lower trapezoidal')
        if not type(overwrite) == bool:
            raise TypeError('overwrite must be a boolean')
    if not overwrite:
        L = L.copy() # if not done, L will be overwritten
    Q = _np.eye(n)
    if r != n:
        for j in range(r-1,-1,-1):
            x = (L[j:,j]).copy().reshape(-1,1)
            x[1:r-j] = 0 # these elements are left unchanged
            s = _np.sqrt(_np.sum(x**2))*(
                    _np.sign(x[0,0]) + int(_np.sign(x[0,0])==0))
            if s != 0: # if all(x==0), nothing to do
                x[0] = x[0] + s
                beta = s*x[0]
                # Implicilty apply H.T to pivot column
                L[j,j] = -s
                # Apply H.T to rest of matrix
                if j > 0:
                    y = _np.dot(x.T, L[j:,:j])
                    L[j:,:j] = L[j:,:j] - _np.dot(x, (y/beta))
                # update H.T product
                y = _np.dot(x.T, Q[j:])
                Q[j:] = Q[j:] - _np.dot(x, (y/beta))
    T = L[:r] # rows r+1:n have been zeroed out
    return Q, T

if __name__=='__main__':
    # generate a random overdetermined system
    A = _np.random.rand(1000,10)
    U,s,V = _np.linalg.svd(A, full_matrices=False)
    s[5:] = 0
    A = _np.dot(U, _np.diag(s)).dot(V)
    b = _np.random.rand(1000,3)
    # get the original least-squares solution
    x_lstsq = _np.linalg.lstsq(A, b)[0]
    x_ecod = ECOD_LS(A, b)

