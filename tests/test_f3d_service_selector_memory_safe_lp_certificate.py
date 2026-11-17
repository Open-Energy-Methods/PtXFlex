"""Hermetic certificate regression: memory-bounded F3-D annual service selector.

These are unit-size synthetic LP constraints, NOT 2022/2024 provider observations,
not industry validation, and not a replacement for full real source-year MILPs.
"""
import numpy as np
from scipy.sparse import csr_matrix
import pytest

from ptxflex import f3d_year_matched_service as f


def micro_problem(n=3,upper=.8):
    nvar=n*f.DIM+1
    c=np.zeros(nvar,dtype=float)
    c[-1]=-1.
    lo=np.zeros(nvar,dtype=float)
    hi=np.ones(nvar,dtype=float)
    # A global LP upper bound is certified by a real linear inequality,
    # not a floating point comparison with an unsolved branch node.
    A=csr_matrix(([1.],([0],[nvar-1])),shape=(1,nvar))
    lb=np.array([-np.inf])
    ub=np.array([upper])
    return c,A,lb,ub,lo,hi


def test_lp_integer_fixed_primal_plus_root_global_bound_is_exact_certificate():
    args=micro_problem(3,.82)
    result=f.try_lp_bound_fixed_binary_certificate(
        *args,n=3,time_limit_s=30,gap_tolerance=1e-6)
    assert result is not None
    assert result.status==0
    assert result.certificate_kind==(
        "LP_GLOBAL_UPPER_BOUND_AND_INTEGER_FIXED_BINARY_FEASIBLE_PRIMAL")
    assert result.x[-1]==pytest.approx(.82,abs=1e-8)
    assert result.mip_gap<=1e-6
    assert -result.mip_dual_bound+1e-7>=result.x[-1]


def test_no_integral_witness_means_root_lp_alone_cannot_certify():
    n=3
    c,A,lb,ub,lo,hi=micro_problem(n,1.)
    # LP feasible only with commitment U_0=0.5, which is not a valid
    # integer physical dispatch. The helper must never call that certified.
    lhs=csr_matrix(([1.],([0],[f.U])),shape=(1,len(c)))
    A=csr_matrix(np.vstack((A.toarray(),lhs.toarray())))
    lb=np.array([-np.inf,.5])
    ub=np.array([1.,.5])
    result=f.try_lp_bound_fixed_binary_certificate(
        c,A,lb,ub,lo,hi,n=n,time_limit_s=30,gap_tolerance=1e-6)
    assert result is None


def test_root_solver_out_of_memory_cannot_produce_a_fake_certificate(monkeypatch):
    def fails(*args,**kwargs):
        raise MemoryError("std::bad_alloc")
    monkeypatch.setattr(f,"milp",fails)
    result=f.try_lp_bound_fixed_binary_certificate(
        *micro_problem(),n=3,time_limit_s=30)
    assert result is None


def test_original_small_integer_model_solver_still_works():
    p=f.load_source_parameters()["E"]
    wind=np.full(8,110.,dtype=float)
    result=f.select_max_uniform_fraction(
        wind,p,None,testing_only=True,time_limit_s=30)
    assert result["selected_fraction_50t_per_day"]==pytest.approx(1.,abs=1e-6)
    assert result["E_max_service_global_optimality_certificate_method"]==(
        "HIGHS_ORIGINAL_FULL_INTEGER_MIP_PRIMAL_DUAL")
    assert result["E_max_service_global_LP_upper_bound_matches_fixed_binary_primal"] is False
