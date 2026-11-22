"""Independent OEM 50L 330bar PED H2 cylinder against prior IJHE 200bar 1.8m3.

Source product: genuine heiserTEC Type I hydrogen PED EN1964-1, 50L,
catalogue pressure class 330bar, empty cylinder weight 85.5kg.
Operating at 200bar(a) and 313K is a hypothetical EOS comparison:
this is NOT the vendor 210bar 36×87L stationary COSMOS module, and not
its 935kg empty TPED mobile hydrogen bundle.
"""
import json
import math
import pytest
pytest.importorskip("CoolProp")

import ptxflex.f2_oem_PED_cylinder_200bar_sensitivity as x


def test_real_heisertec_Ped_50L_330bar_data_and_CEN_stationary_standard_scope():
    meta,prior=x.read_oem()
    c=meta["manufacturer"];n=meta["local_standards"]
    assert c["product_service"]=="hydrogen"
    assert c["pressure_category"]=="PED stationary-compatible cylinder candidate"
    assert c["catalogue_empty_cylinder_weight_kg"]==85.5
    assert c["working_pressure_catalogue_bar"]==330
    assert c["cylinder_water_volume_litre"]==50
    assert c["catalogue_test_pressure_bar"]==472
    assert c["actual_50L_PED_unit_pressure_cycling_certified_for_20bar_to_200bar_313K_site"] is False
    assert n["name"]=="NEN-EN 17533:2025"
    assert n["explicitly_excludes_manifolded_assemblies"] is True
    assert n["explicitly_excludes_external_piping"] is True
    assert not meta["system_complete_manufacturer_BOM_available"]


def test_two_oem_330bar_referenced_cylinders_contain_proper_20bar_heel_and_empty_mass():
    meta,prior=x.read_oem()
    d=x.compare_hydrogen_working_mass(meta,prior)
    assert d["schema_version"]==x.SCHEMA
    assert d["manufacturer_oem_product_330bar_nominal_pressure_not_same_as_200bar_screen"]
    assert d["source_2023_PyNEXUS_project_not_actual_heiserTEC_installation"]
    assert d["OEM_product_working_pressure_basis_gauge_absolute_unverified"]
    assert d["standard_for_individual_cylinders_not_manifolded_assemblies"]
    assert d["whole_plant_comparison_release_ready"] is False
    assert set(d["modeled_source_inventory_modes"])=={"max_inventory","usable_service"}
    for mode,v in d["modeled_source_inventory_modes"].items():
        assert 0<v["hypothetical_20bar_abs_313K_H2_unrecoverable_heel_per_50L_kg"]<v["hypothetical_200bar_abs_313K_H2_max_mass_per_50L_cylinder_kg"]
        assert v["hypothetical_200bar_to_20bar_abs_313K_withdrawable_H2_per_50L_kg"]>0
        assert v["hypothetical_200bara_E20t_cylinder_count"]>1000
        assert v["hypothetical_200bara_EplusS40t_cylinder_count"]>v["hypothetical_200bara_E20t_cylinder_count"]
        assert v["hypothetical_extra_cylinders_count"]==(
            v["hypothetical_200bara_EplusS40t_cylinder_count"]-
            v["hypothetical_200bara_E20t_cylinder_count"])
        assert v["hypothetical_extra_OEM_empty_cylinder_hardware_mass_kg"]==(
            v["hypothetical_extra_cylinders_count"]*85.5)
        assert v["hypothetical_extra_OEM_empty_cylinder_hardware_mass_kg"]>1e6
        assert v["both_source_candidates_different_cylinder_dimensions_rated_pressure_not_identical_products"]
        assert v["mobile_TPED_935kg_empty_complete_bundle_weight_used_here"] is False
        assert v["vendor_module_frame_manifold_valves_fabrication_mass_kg"] is None
        assert v["manufacturer_grade_and_H2_fatigue_conformity_for_actual_200bar_313K_duty"] is None
        assert v["native_BAFU2026_v1_1_typeI_compatible_manufacturing_GWP_kgCO2e"] is None
        assert v["full_tank_inc_CAPEX_EUR"] is None
        assert not v["actual_completed_manufacturer_BOM"]


def test_usable_mode_requires_more_actual_oem_cylinders_than_max_gross():
    meta,prior=x.read_oem()
    d=x.compare_hydrogen_working_mass(meta,prior)["modeled_source_inventory_modes"]
    for k in ("hypothetical_200bara_E20t_cylinder_count",
              "hypothetical_200bara_EplusS40t_cylinder_count"):
        assert d["usable_service"][k]>d["max_inventory"][k]


@pytest.mark.parametrize("mutate",[
    lambda d:d["manufacturer"].update(catalogue_empty_cylinder_weight_kg=935),
    lambda d:d["manufacturer"].update(working_pressure_catalogue_bar=200),
    lambda d:d["manufacturer"].update(actual_50L_PED_unit_pressure_cycling_certified_for_20bar_to_200bar_313K_site=True),
    lambda d:d["manufacturer"].update(material_alloy_grade_certificate_available=True),
    lambda d:d["local_standards"].update(explicitly_excludes_manifolded_assemblies=False),
    lambda d:d["scientific_analog"].update(selected_reference_isothermal_K=298.15),
    lambda d:d.update(full_GWP100_or_lifetime_Cost_possible=True),
])
def test_oem_manufacturer_unit_mass_pressure_or_EN_17533_source_misrepresentation_rejected(tmp_path,monkeypatch,mutate):
    z=json.loads(x.REGISTRY.read_text())
    mutate(z)
    p=tmp_path/"tampered.json"
    p.write_text(json.dumps(z))
    monkeypatch.setattr(x,"REGISTRY",p)
    with pytest.raises(x.BadOemEngineeringClaim):
        x.read_oem()
