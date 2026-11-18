"""RC2-C: public, deterministic numerical controls and environment fingerprint.

No private provider arrays, annual MILP solves, OEM evidence, native LCIA, or
scientific release approval. A wheel lock and numerical tolerance test address
repeatability, not physical model validity.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as md
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

LINE = re.compile(r"^([a-z0-9-]+)==([^\s]+) --hash=sha256:([0-9a-f]{64})  # ([^\s]+\.whl)$")
THREADS = ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "BLIS_NUM_THREADS")


def need(condition, message):
    if not condition:
        raise ValueError("RC2-C: " + message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def read_lock(path):
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        m = LINE.fullmatch(line)
        need(m is not None, "lock must contain exact versions and one wheel SHA256 per line")
        name, version, digest, filename = m.groups()
        need(name not in out, "duplicate distribution in lock")
        need(canonical(filename.split("-")[0]) == name, "wheel filename does not match project")
        need(filename.split("-")[1] == version, "wheel filename does not match version")
        out[name] = {"version": version, "sha256": digest, "wheel": filename}
    need(bool(out), "empty lock")
    return out


def installed_versions():
    return {canonical(d.metadata["Name"]): d.version for d in md.distributions()
            if d.metadata.get("Name")}


def verify_versions(lock, installed, allowed_project_names):
    need(all(installed.get(n) == v["version"] for n, v in lock.items()),
         "installed distribution version differs from wheel lock")
    extras = set(installed) - set(lock) - set(allowed_project_names)
    need(not extras, "unexpected unlocked distribution(s): " + ", ".join(sorted(extras)))
    need(all(installed.get(n) == "0.1.0" for n in allowed_project_names),
         "expected local research package version missing or changed")


def close(value, expected, atol, rtol=0.0):
    need(math.isfinite(float(value)) and math.isclose(float(value), expected,
                                                      abs_tol=atol, rel_tol=rtol),
         "numerical acceptance failed: expected " + str(expected) + ", got " + str(value))


def numerical_controls():
    # Explicit thread policy applied in clean CI and documented for local use.
    import numpy as np
    import scipy
    from scipy.optimize import Bounds, LinearConstraint, linprog, milp
    import CoolProp as cp
    from CoolProp.CoolProp import PropsSI

    matrix = np.array([[4., 1., -1.], [2., 7., 1.], [1., -3., 12.]])
    expected = np.array([1.25, -2.5, 3.75])
    rhs = matrix @ expected
    vector = np.linalg.solve(matrix, rhs)
    residual = float(np.max(np.abs(matrix @ vector - rhs)))
    need(residual <= 1e-12, "linear system residual exceeds 1e-12")
    need(float(np.max(np.abs(vector - expected))) <= 1e-12, "linear solve witness differs")

    # Two-variable analytic integer and continuous optima; no source data.
    # x + 2y >= 5, x,y >= 0. LP y=2.5 cost=10, MILP x=1,y=2 cost=11.
    c = np.array([3., 4.])
    lp = linprog(c, A_ub=[[-1., -2.]], b_ub=[-5.], method="highs")
    mi = milp(c, integrality=[1, 1], bounds=Bounds([0., 0.], [np.inf, np.inf]),
              constraints=LinearConstraint([[1., 2.]], 5., np.inf),
              options={"mip_rel_gap": 1e-9})
    need(lp.success and mi.success, "HiGHS analytical toy feasibility failed")
    close(lp.fun, 10., 1e-8)
    close(mi.fun, 11., 1e-8)
    need(float(np.max(np.abs(mi.x - np.rint(mi.x)))) <= 1e-8, "integer witness is fractional")
    need(float(mi.x @ [1., 2.]) >= 5. - 1e-8, "integer witness violates constraint")
    close(mi.fun, float(mi.x @ c), 1e-8)
    infeasible = milp([1.], integrality=[1], bounds=Bounds([0.], [1.]),
                      constraints=LinearConstraint([[1.]], [2.], [np.inf]))
    need(infeasible.status == 2, "HiGHS infeasible control not certified")

    # Independently reproduce original 313 K reference pressure swing density.
    rho_hi = float(PropsSI("Dmass", "T", 313., "P", 20e6, "Hydrogen"))
    rho_lo = float(PropsSI("Dmass", "T", 313., "P", 2e6, "Hydrogen"))
    need(0 < rho_lo < rho_hi, "invalid gas density ordering")
    usable = 20000. * (1. - rho_lo / rho_hi)
    close(usable, 17784.924849614785, 1e-5)

    # A separate analytically constructed H2/energy balance, in kg and kWh.
    initial, produced, delivered, leaked, final = 100., 12., 7., .2, 104.8
    h2_residual = initial + produced - delivered - leaked - final
    energy_residual = 630. - (600. + 20. + 10.)
    close(h2_residual, 0., 1e-10)
    close(energy_residual, 0., 1e-10)

    # SciPy does not expose a stable public standalone HiGHS version accessor.
    # Pin the actual SciPy wheel; record a bundled version only if discoverable.
    highs_version = None
    try:
        from scipy.optimize._highspy import _core
        vals = [getattr(_core, "HIGHS_VERSION_" + x, None)
                for x in ("MAJOR", "MINOR", "PATCH")]
        if all(isinstance(v, int) for v in vals):
            highs_version = ".".join(map(str, vals))
        elif hasattr(_core, "_Highs"):
            highs_version = str(_core._Highs().version())
    except (ImportError, AttributeError, TypeError, RuntimeError):
        pass
    def numeric_libraries(mod):
        try:
            found = mod.show_config(mode="dicts").get("Build Dependencies", {})
            result = {}
            for name in ("blas", "lapack"):
                entry = found.get(name, {})
                result[name] = {k: str(entry[k]) for k in ("name", "version",
                          "detection method", "openblas configuration") if k in entry}
            return result
        except (AttributeError, TypeError, ValueError):
            return {}
    return {
        "analytical_linear_residual_max_abs": residual,
        "highs_lp_objective": float(lp.fun),
        "highs_milp_objective": float(mi.fun),
        "highs_infeasible_control_status": int(infeasible.status),
        "reference_hydrogen_313K_20_to_200bar_usable_kg": usable,
        "synthetic_mass_balance_residual_kg": h2_residual,
        "synthetic_energy_balance_residual_kWh": energy_residual,
        "scipy_bundled_highs_version_if_exposed": highs_version,
        "highs_source_identity": "hash-locked SciPy wheel",
        "coolprop_git_revision": str(cp.__gitrevision__),
        "numpy_build_libraries": numeric_libraries(np),
        "scipy_build_libraries": numeric_libraries(scipy),
    }


def native_manifest(lens_root):
    if lens_root is None:
        return None
    pom = lens_root / "native-openlca/pom.xml"
    root = ET.parse(pom).getroot()
    ns = {"m": "http://maven.apache.org/POM/4.0.0"}
    def tag(obj, t):
        return obj.findtext("m:" + t, namespaces=ns)
    deps = {tag(d, "groupId") + ":" + tag(d, "artifactId"): tag(d, "version")
            for d in root.findall("m:dependencies/m:dependency", ns)}
    plugins = {tag(d, "groupId") + ":" + tag(d, "artifactId"): tag(d, "version")
               for d in root.findall("m:build/m:plugins/m:plugin", ns)}
    def command_version(cmd, pattern):
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=15, check=True)
        except (OSError, subprocess.SubprocessError):
            return None
        m = re.search(pattern, p.stdout + "\n" + p.stderr)
        return m.group(1) if m else None
    return {
        "pom_sha256": sha256(pom),
        "java_release_declared": root.findtext("m:properties/m:maven.compiler.release", namespaces=ns),
        "direct_maven_dependencies": deps,
        "declared_maven_plugins": plugins,
        "java_runtime_version_if_available": command_version(["java", "-version"], r'version "([^"]+)"'),
        "maven_version_if_available": command_version(["mvn", "-version"], r"Apache Maven ([0-9.]+)"),
        "native_engine_executed": False,
        "transitive_maven_jars_hash_locked": False,
        "native_database_read_or_hash_verified": False,
        "native_lcia_reproduced": False,
    }


def audit(flex_root, lens_root=None):
    flex_root = flex_root.resolve()
    lens_root = lens_root.resolve() if lens_root else None
    need(sys.implementation.name == "cpython" and sys.version_info[:2] == (3, 11),
         "CPython 3.11 required")
    system = platform.system()
    need(system in ("Linux", "Windows") and platform.machine().lower() in ("x86_64", "amd64"),
         "only Linux/Windows x86-64 lock profiles qualified")
    lock_rel = Path("requirements") / ("rc2c-" + system.lower() + "-py311.lock")
    lock_path = flex_root / lock_rel
    if lens_root is not None:
        need(lock_path.read_bytes() == (lens_root / lock_rel).read_bytes(),
             "cross-repository lock bytes diverged")
    lock = read_lock(lock_path)
    projects = ["ptxflex"] + (["ptxlens"] if lens_root else [])
    verify_versions(lock, installed_versions(), projects)
    need(all(os.environ.get(k) == "1" for k in THREADS), "set all four numerical thread limits to 1")
    controls = numerical_controls()
    def git_revision(root):
        return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"],
                                       text=True, timeout=15).strip()
    return {
        "schema_version": "oem.ptx.rc2c.environment_fingerprint.v1",
        "status": "RC2C_LOCKED_PYTHON_NUMERICAL_CONTROLS_PASS_NOT_SCIENTIFIC_V1",
        "platform": system,
        "machine": platform.machine(),
        "python_version": platform.python_version(),
        "python_implementation": sys.implementation.name,
        "os_release": platform.release(),
        "thread_policy": {k: os.environ[k] for k in THREADS},
        "wheel_lock_sha256": sha256(lock_path),
        "locked_distribution_count": len(lock),
        "installed_locked_versions": {n: x["version"] for n, x in lock.items()},
        "ptxflex_commit": git_revision(flex_root),
        "ptxlens_commit": git_revision(lens_root) if lens_root else None,
        "numerical_controls": controls,
        "native_openlca": native_manifest(lens_root),
        "original_annual_private_milps_rerun": False,
        "scientific_v1_approved": False,
        "physical_validation_completed": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--flex-root", type=Path, required=True)
    p.add_argument("--lens-root", type=Path)
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    result = audit(a.flex_root, a.lens_root)
    body = json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if a.output:
        with a.output.open("x", encoding="utf-8", newline="\n") as f:
            f.write(body)
    print(result["status"])
    print(body)


if __name__ == "__main__":
    main()
