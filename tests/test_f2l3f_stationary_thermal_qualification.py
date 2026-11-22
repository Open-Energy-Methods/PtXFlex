"""L3-F Type I source-gated H2 thermal sizing, real EOS + independent oracle.

No manufacturer, PED, plant-site, emissions or actual certified bank evidence.
"""
import math
import sys
import types

import pytest

from ptxflex import f2l3f_stationary_thermal_qualification as m


def kwargs():
    return {
        "max_inventory_kg":20000.,
        "usable_kg":17784.924849614785,
        "vessel_free_volume_m3":1.8,
        "maximum_pressure_bar_absolute":200.,
        "withdrawal_heel_bar_absolute":20.,
        "reference_temperature_k":313.,
        "cold_temperature_k":293.,
        "hot_temperature_k":333.,
    }


@pytest.fixture
def ideal_oracle(monkeypatch):
    root=types.ModuleType("CoolProp")
    cp=types.ModuleType("CoolProp.CoolProp")
    def PropsSI(out,p_name,p,t_name,t,fluid):
        assert (out,p_name,t_name,fluid)==("Dmass","P","T","Hydrogen")
        return p/(4124.*t)
    cp.PropsSI=PropsSI
    monkeypatch.setitem(sys.modules,"CoolProp",root)
    monkeypatch.setitem(sys.modules,"CoolProp.CoolProp",cp)


def test_source_F2_reference_distinguishes_max_inventory_from_usable():
    a=m.source_reference()
    assert a["extra_gross_H2_at_maximum_kg"]==20000.
    assert a["original_pressure_swing_extra_withdrawable_H2_kg"]==pytest.approx(17784.924849614785)
    assert a["published_extra_empty_reference_vessel_positions"]==802
    assert a["published_reference_one_vessel_internal_FREE_volume_m3"]==1.8
    assert a["published_empty_equipment_mass_PER_paper_vessel_kg"]==2400.
    assert a["reference_vessel_is_not_supplier_certified"]
    assert len(a["original_19_component_scope_ids"])==19


def test_independent_ideal_gas_oracle_gross_usable_minimum_discrete_count(ideal_oracle):
    x=kwargs()
    r=m.screen_one(**x)
    hot_rho=200.*1e5/(4124.*333.)
    usable_density=1e5/4124.*(200./333.-20./293.)
    expected_gross=20000./hot_rho
    expected_usable=x["usable_kg"]/usable_density
    expected_count=math.ceil(max(expected_gross,expected_usable)/1.8)
    assert r["required_FREE_volume_for_MAX_inventory_m3"]==pytest.approx(expected_gross,rel=1e-12)
    assert r["required_FREE_volume_for_WORKING_service_m3"]==pytest.approx(expected_usable,rel=1e-12)
    assert r["mathematical_minimum_discrete_paper_positions_for_BOTH"]==expected_count
    assert r["independently_forward_EOS_hot_gross_kg"]>=20000.
    assert r["independently_forward_EOS_conservative_working_kg"]>=x["usable_kg"]
    assert r["actual_OEM_vessel_count"] is None
    assert r["pressure_design_certified_under_EU_PED"] is False


def test_more_extreme_thermal_envelope_requires_more_volume(ideal_oracle):
    x=kwargs()
    moderate=m.screen_one(**{**x,"cold_temperature_k":303.,"hot_temperature_k":323.})
    wide=m.screen_one(**x)
    cold=m.screen_one(**{**x,"cold_temperature_k":313.,"hot_temperature_k":313.})
    assert wide["required_FREE_volume_for_BOTH_m3"]>moderate["required_FREE_volume_for_BOTH_m3"]>cold["required_FREE_volume_for_BOTH_m3"]


@pytest.mark.parametrize("key,value",[
    ("max_inventory_kg",0.),("usable_kg",-1.),
    ("vessel_free_volume_m3",float("nan")),
    ("maximum_pressure_bar_absolute",True),
    ("withdrawal_heel_bar_absolute",200.),
    ("cold_temperature_k",340.),
    ("hot_temperature_k",300.),
])
def test_nonphysical_source_or_service_inputs_fail_closed(ideal_oracle,key,value):
    with pytest.raises(m.L3FQualificationError):
        m.screen_one(**{**kwargs(),key:value})


def test_real_CoolProp_screen_has_three_unqualified_temperature_scenarios():
    pytest.importorskip("CoolProp.CoolProp")
    r=m.build()
    assert r["schema_version"]==m.SCHEMA
    assert len(r["scenarios"])==3
    assert all(c["independently_forward_EOS_hot_gross_kg"]>=20000.
               for c in r["scenarios"])
    assert all(c["independently_forward_EOS_conservative_working_kg"]>=17784.924849
               for c in r["scenarios"])
    assert r["OEM_qualified_specific_station"] is False
    assert r["native_BAFU_2026_v11_manufacturing_inventory"] is None
    assert r["installed_incremental_CAPEX_eur"] is None
    assert "NOT OEM qualification" in m.markdown(r)
