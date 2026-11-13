"""F2 publication-sourced vessel bank research screening and negative QA.

No test case substitutes source paper kg H2 with empty equipment mass.
CoolProp states are real source-library thermo results. Pressure basis is
hypothesized absolute and must not be interpreted as a tank specification.
"""
import math
import pytest
pytest.importorskip("CoolProp")
from ptxflex.hydrogen_physics import HydrogenPropertyError
from ptxflex.storage_reference_vessels import (
  PUBLISHED_VESSELS,REFERENCE_DOI,screen_vessel_bank,
  make_source_based_sensitivity,
)


def test_published_table_is_direct_and_technology_specific():
    assert REFERENCE_DOI=="10.1016/j.ijhydene.2025.152849"
    assert len(PUBLISHED_VESSELS)==5
    assert PUBLISHED_VESSELS["I_200bar"].internal_volume_m3==1.8
    assert PUBLISHED_VESSELS["I_200bar"].empty_vessel_mass_kg==2400
    assert PUBLISHED_VESSELS["I_200bar"].publication_h2_at_rated_kg==26
    assert PUBLISHED_VESSELS["IV_350bar"].empty_vessel_mass_kg==1200
    assert PUBLISHED_VESSELS["I_30bar"].max_reference_pressure_bar==30


def test_original_20t_maximum_inventory_is_not_20t_usable():
    a=screen_vessel_bank("I_200bar",20000,20,298.15)
    assert a.source_capacity_semantics=="max_inventory"
    assert a.gross_hydrogen_at_max_pressure_kg>=20000
    assert a.withdrawable_hydrogen_between_pressures_kg<20000
    assert a.residual_heel_hydrogen_at_min_pressure_kg>0
    assert a.empty_reference_vessels_total_kg==a.number_of_reference_vessels*2400
    assert a.actual_usable_below_model_nominal_capacity
    assert not a.native_manufacturing_lca_calculated


def test_physical_20t_usable_requires_more_vessel_mass_than_original_20t_state_cap():
    a=screen_vessel_bank("I_200bar",20000,20,298.15,capacity_semantics="max_inventory")
    b=screen_vessel_bank("I_200bar",20000,20,298.15,capacity_semantics="usable_service")
    assert b.number_of_reference_vessels>a.number_of_reference_vessels
    assert b.withdrawable_hydrogen_between_pressures_kg>=20000
    assert b.empty_reference_vessels_total_kg>a.empty_reference_vessels_total_kg


def test_increased_min_delivery_pressure_increases_needed_usable_bank():
    low=screen_vessel_bank("I_200bar",20000,20,298.15,capacity_semantics="usable_service")
    high=screen_vessel_bank("I_200bar",20000,30,298.15,capacity_semantics="usable_service")
    assert high.number_of_reference_vessels>=low.number_of_reference_vessels
    assert high.residual_heel_hydrogen_at_min_pressure_kg>low.residual_heel_hydrogen_at_min_pressure_kg


def test_combined_reference_sensitivity_separates_20_40t_and_storage_interpretation():
    x=make_source_based_sensitivity()
    assert len(x["cases"])==20
    assert {z["original_model_case"] for z in x["cases"]}=={"E","E_plus_S"}
    assert {z["source_capacity_semantics"] for z in x["cases"]}=={"max_inventory","usable_service"}
    assert x["any_physical_BOM_complete"] is False
    assert x["any_native_tank_equipment_LCIA_executed"] is False
    assert all(z["empty_reference_vessels_total_kg"]>0 for z in x["cases"])
    assert all(z["supports_and_compressor_mass_known"] is False for z in x["cases"])
    assert all(z["vessels_are_certified_for_this_duty"] is False for z in x["cases"])


@pytest.mark.parametrize("kwargs",[
    {"vessel_id":"fabricated","original_model_capacity_kg":20000,"lower_pressure_bar_absolute":20,"temperature_k":298.15},
    {"vessel_id":"I_200bar","original_model_capacity_kg":-1,"lower_pressure_bar_absolute":20,"temperature_k":298.15},
    {"vessel_id":"I_200bar","original_model_capacity_kg":20000,"lower_pressure_bar_absolute":200,"temperature_k":298.15},
    {"vessel_id":"I_200bar","original_model_capacity_kg":20000,"lower_pressure_bar_absolute":20,"temperature_k":298.15,"capacity_semantics":"hydrogen_mass_equals_steel_mass"},
    {"vessel_id":"I_200bar","original_model_capacity_kg":20000,"lower_pressure_bar_absolute":20,"temperature_k":198.15},
])
def test_unphysical_or_unregistered_vessel_inference_blocked(kwargs):
    with pytest.raises(HydrogenPropertyError):
        screen_vessel_bank(**kwargs)
