import sys
sys.path.append('/Users/emilyhaworth/thesis_fmps/env/fMPS-qnumbers/code/src')
print(sys.path)


import unittest
import numpy as np
import fMPS as ptn


class TestBondOps(unittest.TestCase):

    def test_qr(self):

        A = crandn((23, 15))

        # fictitious quantum numbers
        q0 = np.random.randint(2, size=A.shape[0]) #changed so only = 0,1 
        q1 = np.random.randint(2, size=A.shape[1])

        # enforce block sparsity structure dictated by quantum numbers
        mask = ptn.qnumber_outer_sum([q0, -q1])
        A = np.where(mask == 0, A, 0)

        # perform QR decomposition, taking quantum numbers into account
        Q, R, qinterm = ptn.qr(A, q0, q1)

        self.assertTrue(np.allclose(Q @ R, A, rtol=1e-14),
                        msg='Q @ R must match A matrix')

        self.assertTrue(np.allclose(Q.conj().T @ Q, np.identity(Q.shape[1]), rtol=1e-14),
                        msg='columns of Q matrix must be orthonormalized')

        self.assertTrue(ptn.is_qsparse(Q, [q0, -qinterm]),
                        msg='sparsity pattern of Q matrix must match quantum numbers')
        self.assertTrue(ptn.is_qsparse(R, [qinterm, -q1]),
                        msg='sparsity pattern of R matrix must match quantum numbers')


    def test_split_matrix_svd(self):

        A = crandn((17, 26))

        # fictitious quantum numbers
        q0 = np.random.randint(2, size=A.shape[0]) #changed so only = 0,1 
        q1 = np.random.randint(2, size=A.shape[1])

        # enforce block sparsity structure dictated by quantum numbers
        mask = ptn.qnumber_outer_sum([q0, -q1])
        A = np.where(mask == 0, A, 0)

        # perform SVD decomposition without truncation
        u, s, v, qinterm = ptn.split_matrix_svd(A, q0, q1, 0.)

        self.assertTrue(np.allclose((u * s) @ v, A, rtol=1e-13),
                        msg='U @ S @ V must match A matrix')

        self.assertTrue(np.allclose(u.conj().T @ u, np.identity(u.shape[1]), rtol=1e-14),
                        msg='columns of U matrix must be orthonormalized')

        self.assertTrue(ptn.is_qsparse(u, [q0, -qinterm]),
                        msg='sparsity pattern of U matrix must match quantum numbers')
        self.assertTrue(ptn.is_qsparse(v, [qinterm, -q1]),
                        msg='sparsity pattern of V matrix must match quantum numbers')

        s_norm = np.linalg.norm(s)

        # perform SVD decomposition with truncation
        u, s, v, qinterm = ptn.split_matrix_svd(A, q0, q1, 0.15)

        self.assertAlmostEqual(np.linalg.norm((u * s) @ v - A), np.sqrt(s_norm**2 - np.linalg.norm(s)**2),
                               delta=1e-14, msg='weight of truncated singular values must agree with norm of matrix difference')

        self.assertTrue(np.allclose(u.conj().T @ u, np.identity(u.shape[1]), rtol=1e-14),
                        msg='columns of U matrix must be orthonormalized')

        self.assertTrue(ptn.is_qsparse(u, [q0, -qinterm]),
                        msg='sparsity pattern of U matrix must match quantum numbers')
        self.assertTrue(ptn.is_qsparse(v, [qinterm, -q1]),
                        msg='sparsity pattern of V matrix must match quantum numbers')


def crandn(size):
    """
    Draw random samples from the standard complex normal (Gaussian) distribution.
    """
    # 1/sqrt(2) is a normalization factor
    return (np.random.standard_normal(size)
       + 1j*np.random.standard_normal(size)) / np.sqrt(2)


if __name__ == '__main__':
    unittest.main()