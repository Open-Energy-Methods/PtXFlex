"""F3: fail-closed qualification of a proposed H2 top-up supply offer.

Pure mathematical evaluation against a SHA-verified 8760-hour shortage trace.
It is NOT evidence that an actual hydrogen supplier exists or can deliver.
No hypothetical source may be used in LCA/TEA or full-service release gates.

A proposed delivery profile is evaluated at the final hydrogen delivery
node. Pressure/purity are *documentary gate requirements*, not inferred
from the source PyNEXUS PEM pressure. Supply quantities are kg per hour.
Ramp is adjacent hourly change of delivered kg/h. Zero start/end are not
assumed at the year boundary. No upstream buffer is implied.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np


class SupplyQualificationError(ValueError):
    pass


def _series(values, label):
    a=np.asarray(values,dtype=np.float64)
    if a.shape!=(8760,) or not np.isfinite(a).all() or np.min(a)<0:
        raise SupplyQualificationError(label+" must be 8760 finite nonnegative hourly kg")
    return a


def certify_fixed_hourly_offer(shortfall_kg, proposed_delivery_kg,
        *, shortfall_trace_sha256, source_provenance,
        delivery_pressure_bar_absolute, minimum_required_pressure_bar_absolute,
        delivered_purity_mole_fraction, minimum_required_purity_mole_fraction,
        maximum_offer_ramp_kg_h_per_hour,
        pressure_and_purity_independently_documented=False):
    """Return a *mathematical* fixed-trace acceptance certificate.

    This is not a validated supplier: true documentary evidence is required
    for pressure and purity; no fabricated supplier evidence is accepted.
    Numerical tolerances apply only to floating point rounding, not capacity.
    """
    q=_series(shortfall_kg,"source-derived shortage")
    s=_series(proposed_delivery_kg,"proposed supplier delivery")
    if not isinstance(shortfall_trace_sha256,str) or len(shortfall_trace_sha256)!=64:
        raise SupplyQualificationError("original source hourly trace SHA required")
    if not isinstance(source_provenance,str) or not source_provenance.strip():
        raise SupplyQualificationError("original source evidence provenance required")
    values=(delivery_pressure_bar_absolute,minimum_required_pressure_bar_absolute,
            delivered_purity_mole_fraction,minimum_required_purity_mole_fraction,
            maximum_offer_ramp_kg_h_per_hour)
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in values):
        raise SupplyQualificationError("nonfinite or nonnumeric physical delivery gate")
    pressure,pmin,purity,minimum_purity,ramp=map(float,values)
    if min(pressure,pmin)<=0 or not 0<minimum_purity<=1 or not 0<purity<=1 or ramp<0:
        raise SupplyQualificationError("invalid physical gate bounds")
    # Hash canonical source evidence payload, not the raw float64 array.
    payload={"hourly_additional_shortfall_kg":q.tolist(),
       "derived_source_not_original_raw_prices_or_wind":True,
       "source_E_delivered_reference_profile_is_modelled":True}
    digest=hashlib.sha256((json.dumps(payload,sort_keys=True,
        allow_nan=False,separators=(",",":"))+"\n").encode("utf-8")).hexdigest()
    if digest!=shortfall_trace_sha256:
        raise SupplyQualificationError("source-hourly shortage trace SHA mismatch")
    max_deficit=float(np.max(np.maximum(q-s,0)))
    total_deficit=float(math.fsum(np.maximum(q-s,0).tolist()))
    peak_ramp=float(np.max(np.abs(np.diff(s))))
    pressure_ok=pressure>=pmin
    purity_ok=purity>=minimum_purity
    ramp_ok=peak_ramp<=ramp+1e-7
    mass_ok=max_deficit<=1e-7 and total_deficit<=1e-5
    documented=pressure_and_purity_independently_documented is True
    return {
      "schema_version":"ptxflex.F3_fixed_hourly_backup_offer_screen.v0.1",
      "source_trace_sha256":digest,
      "source_provenance":source_provenance,
      "hours":8760,
      "source_annual_modelled_shortfall_kg":float(math.fsum(q.tolist())),
      "proposed_annual_delivery_kg":float(math.fsum(s.tolist())),
      "peak_unserved_kg_h":max_deficit,
      "total_unserved_kg":total_deficit,
      "proposed_max_adjacent_hour_ramp_kg_h_per_hour":peak_ramp,
      "hourly_mass_service_met":mass_ok,
      "pressure_gate_met":pressure_ok,
      "purity_gate_met":purity_ok,
      "ramp_gate_met":ramp_ok,
      "pressure_purity_independently_documented":documented,
      "fixed_trace_supplier_offer_screen_pass":bool(mass_ok and pressure_ok and purity_ok and ramp_ok and documented),
      "real_supplier_or_2023_availability_verified":False,
      "external_transport_storage_cooling_LCA_TEA_verified":False,
      "full_plant_science_gate_passed":False,
      "not_a_minimum_supplier_rating_or_industrial_validation":True
    }


def screen_verified_artifact(source_json,proposed_delivery_kg,**kwargs):
    """Read original Stage A trace JSON without altering it."""
    raw=Path(source_json).read_bytes()
    obj=json.loads(raw)
    if set(obj)!={"hourly_additional_shortfall_kg",
                  "derived_source_not_original_raw_prices_or_wind",
                  "source_E_delivered_reference_profile_is_modelled"}:
        raise SupplyQualificationError("unexpected Stage A evidence schema")
    if obj["derived_source_not_original_raw_prices_or_wind"] is not True or obj["source_E_delivered_reference_profile_is_modelled"] is not True:
        raise SupplyQualificationError("missing explicit modelled source evidence")
    return certify_fixed_hourly_offer(
        obj["hourly_additional_shortfall_kg"],proposed_delivery_kg,
        shortfall_trace_sha256=hashlib.sha256(raw).hexdigest(),**kwargs)
