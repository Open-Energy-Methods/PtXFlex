"""Independent synthetic ordering controls; no measured hydrogen plant data."""
import math
import pytest
from ptxflex.f2_eos_monotonicity import audit_sampled_eos_ordering


def ideal(rho,t):
    return rho*4124.0*t


def test_ideal_gas_reference_is_ordered():
    a=audit_sampled_eos_ordering(ideal,density_min=1,density_max=10,
                                temperature_min_k=250,temperature_max_k=450)
    assert a.points_checked==81 and a.passed_sampled_ordering
    assert a.density_order_violations==a.temperature_order_violations==0
    assert not a.continuous_domain_proven and not a.certified_vessel
    assert math.isclose(a.minimum_pressure_pa,ideal(1,250))
    assert math.isclose(a.maximum_pressure_pa,ideal(10,450))


def test_detect_density_inversion():
    a=audit_sampled_eos_ordering(lambda rho,t: 1e7-rho*1e5+t,
         density_min=1,density_max=10,temperature_min_k=250,temperature_max_k=450)
    assert not a.passed_sampled_ordering and a.density_order_violations>0


def test_detect_temperature_inversion():
    a=audit_sampled_eos_ordering(lambda rho,t: 1e7+rho*1e5-t*1e3,
         density_min=1,density_max=10,temperature_min_k=250,temperature_max_k=450)
    assert not a.passed_sampled_ordering and a.temperature_order_violations>0


@pytest.mark.parametrize('kwargs',[
    {'density_min':0}, {'density_max':1}, {'temperature_min_k':-1},
    {'temperature_max_k':200}, {'n':2}, {'n':True},
    {'relative_tolerance':float('nan')}, {'density_max':float('inf')},
])
def test_invalid_domain_fails_closed(kwargs):
    d=dict(density_min=1,density_max=10,temperature_min_k=250,
           temperature_max_k=450)
    d.update(kwargs)
    with pytest.raises(ValueError):
        audit_sampled_eos_ordering(ideal,**d)


@pytest.mark.parametrize('fn',[
    lambda rho,t: float('nan'),lambda rho,t: -1,
    lambda rho,t: 0,lambda rho,t: (_ for _ in ()).throw(RuntimeError('EOS')),
])
def test_bad_eos_fails_closed(fn):
    with pytest.raises(ValueError):
        audit_sampled_eos_ordering(fn,density_min=1,density_max=10,
                                    temperature_min_k=250,temperature_max_k=450)
