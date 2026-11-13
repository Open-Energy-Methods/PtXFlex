"""2023 source-derived F3 hourly backup envelopes: pinned data, no invented provider."""
import hashlib
import json
import math
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]/"data/results"
SHA={
 "max_inventory":"c65fda894ef4b30e09339ad88a3972625af78c17802fd0cb9a2fc25d3205882f",
 "usable_service":"d893c6388f14d276b2ef5d4bff4b6c8057dd252067f307f83b9baafcfa1e5308",
}


@pytest.mark.parametrize("mode",["max_inventory","usable_service"])
def test_original_hourly_stageB_backup_source_is_hash_locked_and_unpriced(mode):
    p=ROOT/f"F3_2023_original_E_source_hypothetical_backup_{mode}.json"
    raw=p.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==SHA[mode]
    data=json.loads(raw)
    assert data["schema_version"]=="ptxflex.F3_2023_hypothetical_source_hourly_H2_backup_load_envelope.v1"
    assert data["source_pressure_screen_case"]=="E"
    assert data["capacity_semantics"]==mode
    assert data["source_E_zip_sha256"]=="069455704573825f4e709e6705f5db43823722909cb93a37bd86b978636fb051"
    assert data["source_EplusS_zip_sha256"]=="cd4101fe62c3f1b8aa2d7508d3651d2fee40d2bafe6d5b87e40d5f4d055070f9"
    assert data["single_incumbent_hypothetical_topup_annual_kg"]>0
    assert math.isclose(data["single_incumbent_hypothetical_topup_annual_kg"],
       data["stageA_original_feasible_dispatch_shortage_upper_bound_kg"],abs_tol=.0002)
    assert 0<data["stageA_original_MILP_min_shortage_certified_lower_bound_kg"]<=data["single_incumbent_hypothetical_topup_annual_kg"]
    assert data["single_incumbent_hypothetical_topup_occupied_hours"]>0
    assert not data["external_H2_supplier_physically_specified"]
    assert data["incremental_backup_H2_kgCO2e_per_kg"] is None
    assert data["incremental_backup_cost_EUR_per_kg"] is None
    assert not data["matched_service_LCA_TEA_comparison_permitted"]
