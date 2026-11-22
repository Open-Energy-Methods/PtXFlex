"""Bounded hypothetical electricity-to-H2-to-methanol MILP using SciPy/HiGHS.

Not a validated process simulator, bankable project or full life-cycle model.
"""
from datetime import datetime, timedelta
import hashlib
import json
import math

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

H2_PER_KG_MEOH = 3 * 2.016 / 32.04
CO2_PER_KG_MEOH = 44.01 / 32.04
SCHEMA = "ptxflex.methanol.v0.1"
FIELDS = ("wind_available_mwh", "grid_price_eur_mwh",
          "grid_gwp_kgco2e_mwh", "wind_gwp_kgco2e_mwh")


def finite(value, name, minimum=None):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    v = float(value)
    if minimum is not None and v < minimum:
        raise ValueError(f"{name} below {minimum}")
    return v


def validate(case):
    if case.get("schema_version") != SCHEMA or not case.get("scenario_id"):
        raise ValueError("unsupported case schema")
    if case.get("evidence", {}).get("kind") != "synthetic":
        raise ValueError("only explicitly synthetic baseline inputs supported")
    plant = case["plant"]
    limits = ("electrolyser_max_mw", "h2_yield_kg_mwh", "grid_max_mw",
              "methanol_max_kg_h", "h2_storage_capacity_kg",
              "methanol_target_kg", "co2_supply_kg_h",
              "methanol_electricity_mwh_kg", "methanol_ramp_kg_h",
              "wind_value_eur_mwh", "methanol_variable_eur_kg",
              "methanol_on_eur_hour", "direct_operational_gwp_kgco2e_kg_meoh")
    for key in limits:
        finite(plant.get(key), key, 0)
    for key in ("electrolyser_max_mw", "h2_yield_kg_mwh", "grid_max_mw", "methanol_max_kg_h", "methanol_target_kg"):
        if plant[key] == 0:
            raise ValueError(f"{key} must be positive")
    minload = finite(plant.get("methanol_min_load_fraction"), "methanol_min_load_fraction", 0)
    if minload > 1:
        raise ValueError("minload must be <= 1")
    initial = finite(plant.get("initial_h2_inventory_kg"), "initial_h2_inventory_kg", 0)
    if initial > plant["h2_storage_capacity_kg"]:
        raise ValueError("initial inventory exceeds capacity")
    dt = finite(case.get("dt_hours"), "dt_hours", 0)
    if dt <= 0:
        raise ValueError("dt must be positive")
    hours = case.get("hours")
    if not isinstance(hours, list) or not hours:
        raise ValueError("hourly arrays required")
    previous = None
    for item in hours:
        stamp = item.get("timestamp_utc")
        if not isinstance(stamp, str) or not stamp.endswith("Z"):
            raise ValueError("UTC timestamps required")
        try:
            now = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("invalid timestamp") from exc
        if previous is not None and now - previous != timedelta(hours=dt):
            raise ValueError("timestamps out of order")
        previous = now
        for f in FIELDS:
            finite(item.get(f), f, None if f == "grid_price_eur_mwh" else 0)
    return plant, hours, dt


def solve(case, *, emissions_cap_kgco2e=None):
    """Minimize variable operating cost with binary synthesis commitment.

    Emissions cap applies to operating factor accounting, not full LCIA.
    Methanol total service is fixed at requested target, so no ratio objective.
    """
    plant, hours, dt = validate(case)
    if emissions_cap_kgco2e is not None:
        emissions_cap_kgco2e = finite(emissions_cap_kgco2e, "emissions_cap_kgco2e", 0)
    n = len(hours)
    # Variables per period: wind MWh, grid MWh, produced H2 kg,
    # terminal H2 inventory kg, methanol kg, synthesis on/off binary.
    W, G, H, S, M, U = range(6)
    idx = lambda t, k: 6*t + k
    size = 6*n
    c, emission, lo, hi, integrality = [np.zeros(size) for _ in range(5)]
    integrality = integrality.astype(int)
    for t, row in enumerate(hours):
        c[idx(t,W)] = plant["wind_value_eur_mwh"]
        c[idx(t,G)] = row["grid_price_eur_mwh"]
        c[idx(t,M)] = plant["methanol_variable_eur_kg"]
        c[idx(t,U)] = plant["methanol_on_eur_hour"]*dt
        emission[idx(t,W)] = row["wind_gwp_kgco2e_mwh"]
        emission[idx(t,G)] = row["grid_gwp_kgco2e_mwh"]
        emission[idx(t,M)] = plant["direct_operational_gwp_kgco2e_kg_meoh"]
        hi[idx(t,W)] = row["wind_available_mwh"]
        hi[idx(t,G)] = plant["grid_max_mw"]*dt
        hi[idx(t,H)] = plant["electrolyser_max_mw"]*dt*plant["h2_yield_kg_mwh"]
        hi[idx(t,S)] = plant["h2_storage_capacity_kg"]
        hi[idx(t,M)] = min(plant["methanol_max_kg_h"]*dt,
                          plant["co2_supply_kg_h"]*dt/CO2_PER_KG_MEOH)
        hi[idx(t,U)] = 1
        integrality[idx(t,U)] = 1
    constraints = []
    def add(entries, low=-np.inf, high=np.inf):
        constraints.append((entries, low, high))
    yield_ = plant["h2_yield_kg_mwh"]
    meoh_power = plant["methanol_electricity_mwh_kg"]
    initial = plant["initial_h2_inventory_kg"]
    maximum = plant["methanol_max_kg_h"]*dt
    minimum = maximum*plant["methanol_min_load_fraction"]
    for t in range(n):
        # Electricity supplies electrolysis PLUS auxiliary synthesis electricity.
        add({idx(t,H):1, idx(t,W):-yield_, idx(t,G):-yield_,
             idx(t,M):yield_*meoh_power}, 0, 0)
        # Inventory at end of hour; H2 consumption set by methanol stoichiometry.
        coeffs = {idx(t,S):1, idx(t,H):-1, idx(t,M):H2_PER_KG_MEOH}
        if t:
            coeffs[idx(t-1,S)] = -1
        add(coeffs, initial if t == 0 else 0, initial if t == 0 else 0)
        # Discrete synthesis commitment and minimum stable load.
        add({idx(t,M):1, idx(t,U):-maximum}, high=0)
        add({idx(t,M):-1, idx(t,U):minimum}, high=0)
        if t:
            ramp = plant["methanol_ramp_kg_h"]*dt
            add({idx(t,M):1, idx(t-1,M):-1}, high=ramp)
            add({idx(t,M):-1, idx(t-1,M):1}, high=ramp)
    add({idx(t,M):1 for t in range(n)}, plant["methanol_target_kg"], plant["methanol_target_kg"])
    add({idx(n-1,S):1}, initial, initial)  # prevent free use of initial inventory
    if emissions_cap_kgco2e is not None:
        add({i:float(v) for i,v in enumerate(emission) if v}, high=emissions_cap_kgco2e)

    data, rr, cc, lows, highs = [], [], [], [], []
    for rownum, (entries, bottom, top) in enumerate(constraints):
        lows.append(bottom); highs.append(top)
        for j,v in entries.items():
            if v:
                rr.append(rownum); cc.append(j); data.append(v)
    A = coo_matrix((data,(rr,cc)),shape=(len(constraints),size)).tocsr()
    result = milp(c=c, integrality=integrality, bounds=Bounds(lo,hi),
                  constraints=LinearConstraint(A,np.asarray(lows),np.asarray(highs)),
                  options={"mip_rel_gap":1e-8, "time_limit":60})
    if not result.success or result.x is None:
        raise ValueError(f"MILP failed or infeasible: status={result.status}; {result.message}")
    x = result.x
    per_hour = []
    for t, row in enumerate(hours):
        per_hour.append({
            "timestamp_utc": row["timestamp_utc"], "wind_used_mwh":float(x[idx(t,W)]),
            "grid_used_mwh":float(x[idx(t,G)]),
            "h2_produced_kg":float(x[idx(t,H)]), "h2_stored_kg":float(x[idx(t,S)]),
            "methanol_kg":float(x[idx(t,M)]), "synthesis_on":int(round(x[idx(t,U)])),
            "h2_to_methanol_kg":float(x[idx(t,M)]*H2_PER_KG_MEOH),
            "co2_consumed_kg":float(x[idx(t,M)]*CO2_PER_KG_MEOH),
            "operational_gwp_kgco2e":float(sum(
                x[idx(t,k)]*emission[idx(t,k)] for k in (W,G,M))),
        })
    output = {
        "schema_version":"ptxflex.result.v0.1",
        "scenario_id":case["scenario_id"], "source_kind":"synthetic",
        "input_sha256":hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest(),
        "solver":"SciPy MILP / HiGHS",
        "solver_status":int(result.status),
        "mip_relative_gap":float(getattr(result,"mip_gap",0.0)),
        "claim":"hypothetical dispatch with simplified stoichiometry; NOT process/LCA validation",
        "variable_operating_cost_eur":float(c@x),
        "operational_gwp_kgco2e":float(emission@x),
        "emissions_cap_kgco2e":emissions_cap_kgco2e,
        "methanol_total_kg":float(sum(z["methanol_kg"] for z in per_hour)),
        "hours":per_hour
    }
    audit_solution(case, output)
    return output


def audit_solution(case, solution, tol=1e-5):
    """Independent reconstruction of target, balances, constraints and cap."""
    plant, raw, dt = validate(case)
    rows = solution["hours"]
    if len(rows) != len(raw):
        raise ValueError("output hour count mismatch")
    prev = plant["initial_h2_inventory_kg"]
    total = 0.0
    cost = 0.0
    emissions = 0.0
    prev_m = None
    for inp, out in zip(raw, rows):
        w,g,h,s,m = (out[k] for k in ("wind_used_mwh","grid_used_mwh",
                                     "h2_produced_kg","h2_stored_kg","methanol_kg"))
        if min(w,g,h,s,m) < -tol or w > inp["wind_available_mwh"]+tol or g > plant["grid_max_mw"]*dt+tol:
            raise ValueError("electricity flow bounds fail")
        if h > plant["electrolyser_max_mw"]*dt*plant["h2_yield_kg_mwh"]+tol:
            raise ValueError("electrolyser capacity fails")
        if abs(h - plant["h2_yield_kg_mwh"]*(w+g-plant["methanol_electricity_mwh_kg"]*m)) > tol:
            raise ValueError("electricity-to-H2 identity fails")
        if abs(s-prev-h+H2_PER_KG_MEOH*m) > tol:
            raise ValueError("hydrogen inventory identity fails")
        if s > plant["h2_storage_capacity_kg"]+tol or m > plant["methanol_max_kg_h"]*dt+tol:
            raise ValueError("stock or synthesis nameplate exceeded")
        if m*CO2_PER_KG_MEOH > plant["co2_supply_kg_h"]*dt+tol:
            raise ValueError("CO2 availability violated")
        if out["synthesis_on"] not in (0,1) or m > plant["methanol_max_kg_h"]*dt*out["synthesis_on"]+tol:
            raise ValueError("binary commitment violated")
        if m + tol < plant["methanol_max_kg_h"]*dt*plant["methanol_min_load_fraction"]*out["synthesis_on"]:
            raise ValueError("minimum load violated")
        if prev_m is not None and abs(m-prev_m) > plant["methanol_ramp_kg_h"]*dt+tol:
            raise ValueError("synthesis ramp violated")
        prev_m = m
        prev = s
        total += m
        cost += w*plant["wind_value_eur_mwh"] + g*inp["grid_price_eur_mwh"] + (
            m*plant["methanol_variable_eur_kg"] + out["synthesis_on"]*plant["methanol_on_eur_hour"]*dt)
        emissions += w*inp["wind_gwp_kgco2e_mwh"] + g*inp["grid_gwp_kgco2e_mwh"] + (
            m*plant["direct_operational_gwp_kgco2e_kg_meoh"])
    if abs(total-plant["methanol_target_kg"]) > tol or abs(prev-plant["initial_h2_inventory_kg"]) > tol:
        raise ValueError("methanol service or terminal inventory wrong")
    if abs(cost-solution["variable_operating_cost_eur"]) > tol or abs(emissions-solution["operational_gwp_kgco2e"]) > tol:
        raise ValueError("objective or emissions do not reconstruct")
    cap = solution["emissions_cap_kgco2e"]
    if cap is not None and emissions > cap + tol:
        raise ValueError("emissions limit breached")
    return True
