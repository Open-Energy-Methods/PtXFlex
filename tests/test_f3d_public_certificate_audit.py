import unittest
from ptxflex.f3d_public_certificate_audit import audit,SCHEMA
H="a"*64
FLAGS=("actual_industrial_H2_delivery_or_independent_measurements","vendor_200bar_compressor_and_storage_station_BOM_verified","native_BAFU_whole_plant_GWP_verified","installed_plant_LCOH_or_investment_DCF_certified","independent_external_scientific_peer_review_completed","v1_0_scientific_release_allowed")
def fixture():
    annual=8784*50000/24*.8
    return dict(schema_version=SCHEMA,year=2024,year_UTC_hours=8784,capacity_semantics="max_inventory",mathematically_matched_exact_same_modelled_hourly_H2_target=True,E_price_blind_identical_model_H2_service_selection=dict(selected_fraction_50t_per_day=.8,certified_fraction_upper_bound=.800001,modelled_E_annual_h2_service_kg=annual,selected_h2_target_float64_sha256=H),E=dict(modelled_hourly_H2_service_sha256=H,modelled_annual_hydrogen_kg=annual,modelled_cost_eur_in_source_calendar_not_inflation_adjusted=100,solver_cost_lower_bound_eur=99,mip_relative_gap=1e-7),E_plus_S=dict(modelled_hourly_H2_service_sha256=H,modelled_annual_hydrogen_kg=annual,modelled_cost_eur_in_source_calendar_not_inflation_adjusted=80,solver_cost_lower_bound_eur=79,mip_relative_gap=1e-7),solver_difference_guaranteed_lower_upper_interval_eur=[19,21],cost_savings_E_minus_EplusS_source_calendar_nominal_eur=20,**{k:False for k in FLAGS})
class AuditTests(unittest.TestCase):
    def test_valid_synthetic(self): self.assertEqual(audit(fixture())["nominal_saving_eur"],20)
    def test_different_hourly_service(self):
        x=fixture();x["E_plus_S"]["modelled_hourly_H2_service_sha256"]="b"*64
        with self.assertRaises(ValueError): audit(x)
    def test_inverted_dual(self):
        x=fixture();x["E"]["solver_cost_lower_bound_eur"]=101
        with self.assertRaises(ValueError): audit(x)
    def test_wrong_interval(self):
        x=fixture();x["solver_difference_guaranteed_lower_upper_interval_eur"]=[20,20]
        with self.assertRaises(ValueError): audit(x)
    def test_wrong_leap_calendar(self):
        x=fixture();x["year_UTC_hours"]=8760
        with self.assertRaises(ValueError): audit(x)
    def test_false_release_claim(self):
        x=fixture();x["native_BAFU_whole_plant_GWP_verified"]=True
        with self.assertRaises(ValueError): audit(x)
    def test_nonfinite_gap(self):
        x=fixture();x["E"]["mip_relative_gap"]=float("nan")
        with self.assertRaises(ValueError): audit(x)
if __name__=="__main__": unittest.main()
