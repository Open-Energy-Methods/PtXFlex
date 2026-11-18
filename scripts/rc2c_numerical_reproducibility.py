"""RC2-C synthetic numerical controls and honest runtime fingerprint.

This is portable numerical regression, not physical validation, a native LCA
result, or evidence that a private historical MILP was rerun on this platform.
The exact platform wheel lock is enforced by rc2c_environment_lock.py.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata as md
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys

from rc2c_environment_lock import host, pins, parse_lock, ROOT, sha256


def need(ok, msg):
    if not ok:
        raise ValueError("RC2-C benchmark: " + msg)


def close(actual, expected, atol=1e-8, rtol=1e-10):
    need(math.isfinite(float(actual)) and math.isclose(
        float(actual), float(expected), rel_tol=rtol, abs_tol=atol),
        f"observed {actual!r} != reference {expected!r}")


def solver_version():
    """Read the SciPy-bundled library's version, never substitute a highspy wheel."""
    for name in ("scipy.optimize._highspy._core", "scipy.optimize._highs._highs_wrapper"):
        try:
            mod = importlib.import_module(name)
        except ImportError:
            continue
        for cls in ("_Highs", "Highs"):
            try:
                return {"version": str(getattr(mod, cls)().version()), "source": name}
            except (AttributeError, TypeError):
                pass
        vals = [getattr(mod, "HIGHS_VERSION_" + field, None)
                for field in ("MAJOR", "MINOR", "PATCH")]
        if all(v is not None for v in vals):
            return {"version": ".".join(map(str, vals)), "source": name}
    return {"version": None, "source": "not exposed by installed SciPy; no substitution"}


def git_commit(root):
    return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"],
                                   text=True, timeout=20).strip()


def fingerprint(lens_root=None):
    import numpy as np
    import scipy
    import scipy.linalg as la
    import CoolProp
    from CoolProp.CoolProp import get_global_param_string
    from threadpoolctl import threadpool_info
    # Load both NumPy and SciPy numerical libraries before querying thread pools.
    np.linalg.solve(np.eye(2), np.ones(2))
    la.solve(np.eye(2), np.ones(2))
    target = host()
    lock = ROOT / "environment" / ("rc2c-" + target + ".lock")
    versions = {name: md.version(name) for name in pins()}
    expected = parse_lock(lock, pins())
    need(all(versions[k] == v["version"] for k, v in expected.items()),
         "not the locked numerical environment")
    pools = [{k: pool.get(k) for k in (
        "user_api", "internal_api", "version", "num_threads", "threading_layer", "architecture")}
             for pool in threadpool_info()]
    cfg = getattr(np.__config__, "CONFIG", {})
    libs = cfg.get("Build Dependencies", {}) if isinstance(cfg, dict) else {}
    def build_library(kind):
        value = libs.get(kind, {})
        return {k: value.get(k) for k in ("name", "version", "openblas configuration", "found")} if isinstance(value, dict) else {}
    return {
        "schema_version": "oem.ptx.rc2c.runtime_fingerprint.v1",
        "target": target, "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "python_compiler": platform.python_compiler(),
        "os": platform.system(), "os_release": platform.release(), "machine": platform.machine(),
        "byteorder": sys.byteorder, "float64_epsilon": float(np.finfo(np.float64).eps),
        "locked_wheel_requirements_sha256": sha256(lock),
        "versions": versions,
        "scipy_bundled_HiGHS": solver_version(),
        "coolprop_version": CoolProp.__version__,
        "coolprop_git_revision": get_global_param_string("gitrevision"),
        "numpy_BLAS_build_configuration": build_library("blas"),
        "numpy_LAPACK_build_configuration": build_library("lapack"),
        "loaded_BLAS_OpenMP_pools_without_paths": pools,
        "thread_env": {k: os.environ.get(k) for k in (
            "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")},
        "ptxflex_commit": git_commit(ROOT),
        "ptxlens_commit": git_commit(lens_root) if lens_root else None,
        "native_openlca_or_private_source_replayed": False,
    }


def benchmark(lens_root=None):
    import numpy as np
    import scipy.linalg as la
    from scipy.optimize import Bounds, LinearConstraint, milp, linprog
    from scipy.sparse import csr_matrix
    from scipy.sparse.linalg import spsolve
    from ptxflex.hydrogen_physics import (
        usable_storage_volume, compression_work, conservation_residual_kg,
    )
    from ptxflex.model import solve, audit_solution
    # Analytic solution of an SPD linear system, including dense and sparse paths.
    a = np.array([[4., 1., 0.], [1., 3., 1.], [0., 1., 2.]])
    expected = np.array([1., -2., 3.])
    b = np.array([2., -2., 4.])
    dense, sparse = la.solve(a, b), spsolve(csr_matrix(a), b)
    for x in (dense, sparse):
        close(np.max(np.abs(x - expected)), 0., atol=1e-12)
        close(np.max(np.abs(a @ x - b)), 0., atol=1e-12)
    # Analytic LP relaxation min 3x+2y, 2x+y>=7, x+2y>=7.
    # Unique MILP optimum (2,3), cost=12, verified by independent enumeration.
    c = np.array([3., 2.])
    mat = np.array([[2., 1.], [1., 2.]])
    lower = np.array([7., 7.])
    lp = linprog(c, A_ub=-mat, b_ub=-lower, bounds=(0., 10.), method="highs")
    need(lp.success, "LP failed")
    close(lp.fun, 35. / 3.)
    brute = sorted((3*x + 2*y, x, y) for x in range(11) for y in range(11)
                   if 2*x+y >= 7 and x+2*y >= 7)
    need(brute[0] == (12, 2, 3) and brute[1][0] > 12, "analytic enumeration incorrect")
    opt = milp(c, integrality=np.ones(2), bounds=Bounds(0.,10.),
               constraints=LinearConstraint(mat, lower, np.inf),
               options={"mip_rel_gap": 1e-9})
    need(opt.success and opt.status == 0, "MILP did not solve to optimum")
    close(opt.fun, brute[0][0])
    close(np.max(np.abs(opt.x - np.array(brute[0][1:]))), 0., atol=1e-7)
    close(opt.mip_gap, 0., atol=1e-8)
    bad = milp(c, integrality=np.ones(2), bounds=Bounds(0.,1.),
               constraints=LinearConstraint(mat, lower, np.inf))
    need(bad.status == 2 and not bad.success, "known infeasible MILP accepted")
    # Independent numerical reference from already-published 20/200 bar(a), 313 K
    # original 20,000 kg max inventory pressure swing. Not an independent EOS.
    storage = usable_storage_volume(17784.924849614785, 20., 200., 313.)
    close(storage.initial_hydrogen_capacity_at_max_pressure_kg, 20000., atol=2e-6)
    close(storage.initial_hydrogen_capacity_at_max_pressure_kg -
          storage.residual_hydrogen_capacity_at_min_pressure_kg,
          17784.924849614785, atol=2e-6)
    comp = compression_work(30., 200., 313., .8, .9, 2)
    close(comp.total_electrical_kwh_per_kg_hydrogen * .9,
          comp.total_shaft_energy_kwh_per_kg_hydrogen, atol=1e-10)
    need(comp.total_electrical_kwh_per_kg_hydrogen > 0 and
         not comp.intercooler_power_and_hardware_included, "compression scope")
    close(conservation_residual_kg(20., 7., 4., 20., 2., 1.), 0.)
    # Actual PtXFlex synthetic model. For the fixed 400 kg service, theoretical
    # energy is stoichiometric H2 / 20 + auxiliary power. Cheapest 5 EUR/MWh
    # grid interval has enough capacity; next-cheapest option is wind at 25.
    case = json.loads((ROOT / "examples/illustrative_methanol.json").read_text(encoding="utf-8"))
    energy = 400. * (3. * 2.016 / 32.04 / 20. + .0003)
    cheap_grid_at_cap = (200. - 15. * energy) / (600. - 15.)
    baseline = solve(case)
    limited = solve(case, emissions_cap_kgco2e=200.)
    target_cost = 5. * energy
    cap_cost = 25. * (energy - cheap_grid_at_cap) + 5. * cheap_grid_at_cap
    for r, cost in ((baseline, target_cost), (limited, cap_cost)):
        need(audit_solution(case, r), "PtXFlex original equation audit did not pass")
        close(r["variable_operating_cost_eur"], cost, atol=1e-5)
        close(r["methanol_total_kg"], 400., atol=1e-5)
    close(limited["operational_gwp_kgco2e"], 200., atol=1e-5)
    out = {
        "schema_version": "oem.ptx.rc2c.synthetic_numerical_benchmarks.v1",
        "dense_and_sparse_linear_residual_max": float(max(
            np.max(np.abs(a @ dense - b)), np.max(np.abs(a @ sparse - b)))),
        "analytic_lp_optimum": float(lp.fun), "enumerated_milp_optimum": float(opt.fun),
        "known_infeasible_milp_status": int(bad.status),
        "hydrogen_reference_gross_kg": storage.initial_hydrogen_capacity_at_max_pressure_kg,
        "hydrogen_reference_usable_kg": storage.useful_hydrogen_kg,
        "model_compression_kwh_per_kg": comp.total_electrical_kwh_per_kg_hydrogen,
        "synthetic_methanol_cost_eur": baseline["variable_operating_cost_eur"],
        "synthetic_methanol_capped_cost_eur": limited["variable_operating_cost_eur"],
        "synthetic_methanol_capped_emissions_kgco2e": limited["operational_gwp_kgco2e"],
        "private_annual_solver_or_hardware_or_lcia_replayed": False,
    }
    if lens_root is not None:
        from ptxlens.core import assess, inventory
        from ptxlens.rc2_provenance_governance import audit
        d = json.loads((lens_root / "examples/illustrative.json").read_text(encoding="utf-8"))
        r = assess(d)
        i = inventory(d)
        # Independent nominal synthetic annualization/discounted stream arithmetic.
        years = 20
        pv = math.fsum((1.07)**(-t) for t in range(1, years + 1))
        annual_h2 = 84. * 2190.
        annual_capital = (1.2e6 + 100000. * 1.07**-10) / pv
        total_cost = annual_capital + 20000. + 0.05 * annual_h2 + 2190. * (60. - 2.5 + 2.5 * 35.)
        ghg = 2190. * (400. + 150. + 2.5*15.) + 110000. / 20. + .1 * annual_h2
        close(r["annual_delivered_h2_kg"], annual_h2)
        close(i["reference_product"]["amount"], annual_h2)
        close(r["screening_cost_eur_per_kg_delivered"], total_cost / annual_h2)
        close(r["screening_gwp_kgco2e_per_kg_delivered"], ghg / annual_h2)
        paired = audit(lens_root, ROOT)
        need(paired["full_scientific_v1_approved"] is False, "RC2 wrongly granted v1")
        out.update({"synthetic_lens_screening_cost_eur_per_kg": r["screening_cost_eur_per_kg_delivered"],
                    "synthetic_lens_screening_gwp_kgco2e_per_kg": r["screening_gwp_kgco2e_per_kg_delivered"],
                    "paired_source_receipt_and_RC1_public_artifact_gate": paired["decision"]})
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--lens-root", type=Path)
    p.add_argument("--output", type=Path)
    a = p.parse_args(argv)
    lens = a.lens_root.resolve() if a.lens_root else None
    report = {"environment": fingerprint(lens), "numerics": benchmark(lens),
              "full_scientific_v1_approved": False}
    text = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if a.output:
        with a.output.open("x", encoding="utf-8", newline="\n") as f:
            f.write(text)
    print("RC2C_FINGERPRINT " + json.dumps(report["environment"], sort_keys=True))
    print("RC2C_NUMERICS " + json.dumps(report["numerics"], sort_keys=True))
    print("RC2C_LOCKED_NUMERICAL_BENCHMARK_PASS_NOT_PRIVATE_ANNUAL_REPLAY_OR_SCIENTIFIC_V1")


if __name__ == "__main__":
    main()
