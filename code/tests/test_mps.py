import sys
sys.path.append('/Users/emilyhaworth/thesis_fmps/env/fMPS-qnumbers/code/src')
print(sys.path)

import unittest
import numpy as np
import fMPS as ptn


class TestMPS(unittest.TestCase):

    def test_orthonormalization(self):

        # create random matrix product state
        d = 7
        D = [1, 4, 15, 13, 7, 1]
        mps0 = ptn.fMPS(np.random.randint(2, size=d), [np.random.randint(2, size=Di) for Di in D], fill='random')

        self.assertEqual(mps0.bond_dims, D, msg='virtual bond dimensions')

        # wavefunction on full Hilbert space
        psi = mps0.as_vector()

        # performing left-orthonormalization...
        cL = mps0.orthonormalize(mode='left')
        print(" performing left-orthonormalization now done")

        self.assertLessEqual(mps0.bond_dims[1], d,
            msg='virtual bond dimension can only increase by a factor of "d" per site')

        for i in range(mps0.nsites):
            self.assertTrue(ptn.is_qsparse(mps0.A[i], [mps0.qd, mps0.qD[i], -mps0.qD[i+1]]),
                            msg='sparsity pattern of MPS tensors must match quantum numbers')

        psiL = mps0.as_vector()
        # wavefunction should now be normalized
        self.assertAlmostEqual(np.linalg.norm(psiL), 1., delta=1e-12, msg='wavefunction normalization')

        # wavefunctions before and after left-normalization must match
        # (up to normalization factor)
        self.assertAlmostEqual(np.linalg.norm(cL*psiL - psi), 0., delta=1e-10,
                               msg='wavefunctions before and after left-normalization must match')

        # check left-orthonormalization
        for i in range(mps0.nsites):
            s = mps0.A[i].shape
            assert s[0] == d
            Q = mps0.A[i].reshape((s[0]*s[1], s[2]))
            self.assertTrue(np.allclose(Q.conj().T @ Q, np.identity(s[2]), rtol=1e-12),
                            msg='left-orthonormalization')

        # performing right-orthonormalization...
        cR = mps0.orthonormalize(mode='right')

        self.assertLessEqual(mps0.bond_dims[-2], d,
            msg='virtual bond dimension can only increase by a factor of "d" per site')

        for i in range(mps0.nsites):
            self.assertTrue(ptn.is_qsparse(mps0.A[i], [mps0.qd, mps0.qD[i], -mps0.qD[i+1]]),
                            msg='sparsity pattern of MPS tensors must match quantum numbers')

        self.assertAlmostEqual(abs(cR), 1., delta=1e-12,
            msg='normalization factor must have magnitude 1 due to previous left-orthonormalization')

        psiR = mps0.as_vector()
        # wavefunctions must match
        self.assertTrue(np.allclose(psiL, cR*psiR, rtol=1e-10),
                        msg='wavefunctions after left- and right-orthonormalization must match')

        # check right-orthonormalization
        for i in range(mps0.nsites):
            s = mps0.A[i].shape
            assert s[0] == d
            Q = mps0.A[i].transpose((0, 2, 1)).reshape((s[0]*s[2], s[1]))
            self.assertTrue(np.allclose(Q.conj().T @ Q, np.identity(s[1]), rtol=1e-12),
                            msg='right-orthonormalization')


    def test_split_tensor(self):

        # physical dimensions
        d0, d1 = 3, 5
        # outer virtual bond dimensions
        D0, D2 = 14, 17

        Apair = crandn((d0*d1, D0, D2)) / np.sqrt(d0*d1*D0*D2)

        # fictitious quantum numbers
        qd0 = np.random.randint(2, size=d0)
        qd1 = np.random.randint(2, size=d1)
        qD = [np.random.randint(2, size=D0), np.random.randint(2, size=D2)]

        # enforce block sparsity structure dictated by quantum numbers
        mask = ptn.qnumber_outer_sum([ptn.qnumber_flatten([qd0, qd1]), qD[0], -qD[1]])
        Apair = np.where(mask == 0, Apair, 0)

        for svd_distr in ['left', 'right', 'sqrt']:
            (A0, A1, qbond) = ptn.split_mps_tensor(Apair, qd0, qd1, qD, svd_distr=svd_distr, tol=0)

            self.assertTrue(ptn.is_qsparse(A0, [qd0, qD[0], -qbond]),
                            msg='sparsity pattern of A0 tensors must match quantum numbers')
            self.assertTrue(ptn.is_qsparse(A1, [qd1, qbond, -qD[1]]),
                            msg='sparsity pattern of A1 tensors must match quantum numbers')

            # merged tensor must agree with the original tensor
            Amrg = ptn.merge_mps_tensor_pair(A0, A1)
            self.assertTrue(np.allclose(Amrg, Apair, rtol=1e-13),
                            msg='splitting and subsequent merging must give the same tensor')


    def test_from_vector(self):

        # physical local dimension
        d = 3
        # number of lattice sites
        nsites = 7
        # random vector
        v = crandn(d**nsites)
        mps = ptn.fMPS.from_vector(d, nsites, v)
        self.assertTrue(np.allclose(mps.as_vector(), v, rtol=1e-13),
                        msg='MPS constructed from a vector must match original vector')


    def test_add(self):

        # physical quantum numbers
        qd = np.random.randint(2, size=5)

        # create random matrix product states
        qD0 = [np.random.randint(2, size=Di) for Di in [1, 8, 15, 23, 18,  9, 1]]
        qD1 = [np.random.randint(2, size=Di) for Di in [1, 7, 23, 11, 17, 13, 1]]
        # leading and trailing (dummy) virtual bond quantum numbers must agree
        qD1[ 0] = qD0[ 0].copy()
        qD1[-1] = qD0[-1].copy()
        mps0 = ptn.fMPS(qd, qD0, fill='random')
        mps1 = ptn.fMPS(qd, qD1, fill='random')

        # MPS addition
        mps = mps0 + mps1

        # reference calculation
        mps_ref = mps0.as_vector() + mps1.as_vector()

        # compare
        self.assertTrue(np.allclose(mps.as_vector(), mps_ref, rtol=1e-13),
            msg='addition of two matrix product states must agree with vector representation')


    def test_add_singlesite(self):

        # separate test for a single site since implementation is a special case

        # physical quantum numbers
        qd = np.random.randint(2, size=7)

        # create random matrix product states for a single site
        # leading and trailing (dummy) virtual bond quantum numbers
        qD = [np.array([-1]), np.array([-2])]
        mps0 = ptn.fMPS(qd, qD, fill='random')
        mps1 = ptn.fMPS(qd, qD, fill='random')

        # MPS addition
        mps = mps0 + mps1

        # reference calculation
        mps_ref = mps0.as_vector() + mps1.as_vector()

        # compare
        self.assertTrue(np.allclose(mps.as_vector(), mps_ref, rtol=1e-13),
            msg='addition of two matrix product states must agree with vector representation')


    def test_sub(self):

        # physical quantum numbers
        qd = np.random.randint(2, size=5)

        # create random matrix product states
        qD0 = [np.random.randint(2, size=Di) for Di in [1, 8, 15, 23, 18,  9, 1]]
        qD1 = [np.random.randint(2, size=Di) for Di in [1, 7, 23, 11, 17, 13, 1]]
        # leading and trailing (dummy) virtual bond quantum numbers must agree
        qD1[ 0] = qD0[ 0].copy()
        qD1[-1] = qD0[-1].copy()
        mps0 = ptn.fMPS(qd, qD0, fill='random')
        mps1 = ptn.fMPS(qd, qD1, fill='random')

        # MPS subtraction
        mps = mps0 - mps1

        # reference calculation
        mps_ref = mps0.as_vector() - mps1.as_vector()

        # compare
        self.assertTrue(np.allclose(mps.as_vector(), mps_ref, rtol=1e-12),
            msg='subtraction of two matrix product states must agree with vector representation')


    def test_sub_singlesite(self):

        # separate test for a single site since implementation is a special case

        # physical quantum numbers
        qd = np.random.randint(2, size=7)

        # create random matrix product states for a single site
        # leading and trailing (dummy) virtual bond quantum numbers
        qD = [np.array([-1]), np.array([-2])]
        mps0 = ptn.fMPS(qd, qD, fill='random')
        mps1 = ptn.fMPS(qd, qD, fill='random')

        # MPS subtraction
        mps = mps0 - mps1

        # reference calculation
        mps_ref = mps0.as_vector() - mps1.as_vector()

        # compare
        self.assertTrue(np.allclose(mps.as_vector(), mps_ref, rtol=1e-12),
            msg='subtraction of two matrix product states must agree with vector representation')


def crandn(size):
    """
    Draw random samples from the standard complex normal (Gaussian) distribution.
    """
    # 1/sqrt(2) is a normalization factor
    return (np.random.standard_normal(size)
       + 1j*np.random.standard_normal(size)) / np.sqrt(2)


if __name__ == '__main__':
    unittest.main()