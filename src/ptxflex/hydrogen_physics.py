"""Physically explicit, SOURCE-LIBRARY based hydrogen property and storage screening.

F2 *foundation* only: computes real-gas pressure inventory and reversible/
isentropic compressor work using the official CoolProp v8 hydrogen EOS.
NO preferred 200-bar vessel design is implied. NO tank equipment mass,
compressor motor rating, leakage rate, fabrication source or native BAFU
impact is manufactured from a capacity in kg H2.

Scientific scope:
  - hydrogen treated as pure fluid; dry H2 reference
  - isothermal static storage at *user supplied* gas temperature;
  - pressure input is ABSOLUTE (bar), not gauge;
  - compressor staged isentropic model with ideal interstage return to
    specified inlet T; no actual intercooler equipment, compressor map,
    pressure drops, hydrogen purity correction or time-varying station control.
Limits are research model screening bounds, not engineering design approval.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math

try:
    import CoolProp
    from CoolProp.CoolProp import PropsSI
except ImportError:
    CoolProp = None
    PropsSI = None

R_UNIVERSAL_J_PER_MOL_K=8.31446261815324
HYDROGEN_MOLAR_MASS_KG_PER_MOL=0.00201588  # CoolProp H2 source fluid properties.
SUPPORTED_COOLPROP_MAJOR=8


class HydrogenPropertyError(ValueError):
    """Invalid thermodynamic state or unsupported source library."""


def require_coolprop():
    if CoolProp is None or PropsSI is None:
        raise HydrogenPropertyError("CoolProp 8.0.0 required: pip install -e '.[physics]'")
    version=getattr(CoolProp,"__version__","")
    if not version.startswith(f"{SUPPORTED_COOLPROP_MAJOR}."):
        raise HydrogenPropertyError(f"unsupported hydrogen EOS version {version}; pin CoolProp 8.x")
    return version


def finite_positive(value,name):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:
        raise HydrogenPropertyError(f"{name} must be finite, positive and physical")
    return float(value)


def checked_state(pressure_bar_abs,temperature_k):
    p=finite_positive(pressure_bar_abs,"absolute pressure, bar")
    t=finite_positive(temperature_k,"gas temperature, Kelvin")
    # Research screening envelope, explicitly NOT a tank design standard.
    if not (1.0 <= p <= 700.0):
        raise HydrogenPropertyError("screening absolute gas pressure must be within 1-700 bar")
    if not (200.0 <= t <= 500.0):
        raise HydrogenPropertyError("screening gas T must be within 200-500 K")
    require_coolprop()
    return p*100_000.0,t


def hydrogen_density_kg_m3(pressure_bar_abs,temperature_k):
    p,t=checked_state(pressure_bar_abs,temperature_k)
    d=float(PropsSI("Dmass","P",p,"T",t,"Hydrogen"))
    if not math.isfinite(d) or d<=0:
        raise HydrogenPropertyError("CoolProp hydrogen EOS returned invalid density")
    return d


def ideal_gas_density_kg_m3(pressure_bar_abs,temperature_k):
    p,t=checked_state(pressure_bar_abs,temperature_k)
    return p*HYDROGEN_MOLAR_MASS_KG_PER_MOL/(R_UNIVERSAL_J_PER_MOL_K*t)


@dataclass(frozen=True)
class UsableStorageResult:
    useful_hydrogen_kg:float
    pressure_minimum_bar_absolute:float
    pressure_maximum_bar_absolute:float
    temperature_k:float
    density_minimum_kg_m3:float
    density_maximum_kg_m3:float
    usable_density_swing_kg_m3:float
    required_free_gas_volume_m3:float
    initial_hydrogen_capacity_at_max_pressure_kg:float
    residual_hydrogen_capacity_at_min_pressure_kg:float
    real_gas_compressibility_factor_at_max_pressure:float
    coolprop_version:str
    hardware_mass_kg:None
    equipment_manufacturing_lca_complete:bool
    scientific_claim:str


def usable_storage_volume(usable_hydrogen_kg,minimum_pressure_bar_absolute,
                          maximum_pressure_bar_absolute,temperature_k):
    """For same-temperature stationary H2: usable kg = V*(rho_max-rho_min).

    This is an isothermal screening calculation, NOT a validated vessel,
    fatigue/fire-code assessment or measured storage operating cycle.
    """
    amount=finite_positive(usable_hydrogen_kg,"usable hydrogen mass, kg")
    pmin=finite_positive(minimum_pressure_bar_absolute,"minimum absolute bar")
    pmax=finite_positive(maximum_pressure_bar_absolute,"maximum absolute bar")
    if not pmax>pmin:
        raise HydrogenPropertyError("max absolute pressure must exceed min")
    dmin=hydrogen_density_kg_m3(pmin,temperature_k)
    dmax=hydrogen_density_kg_m3(pmax,temperature_k)
    if dmax<=dmin:
        raise HydrogenPropertyError("real-gas storage density must increase with pressure")
    vol=amount/(dmax-dmin)
    z=pmax*1e5*HYDROGEN_MOLAR_MASS_KG_PER_MOL/(dmax*R_UNIVERSAL_J_PER_MOL_K*temperature_k)
    return UsableStorageResult(
        useful_hydrogen_kg=amount,pressure_minimum_bar_absolute=pmin,
        pressure_maximum_bar_absolute=pmax,temperature_k=float(temperature_k),
        density_minimum_kg_m3=dmin,density_maximum_kg_m3=dmax,
        usable_density_swing_kg_m3=dmax-dmin,required_free_gas_volume_m3=vol,
        initial_hydrogen_capacity_at_max_pressure_kg=vol*dmax,
        residual_hydrogen_capacity_at_min_pressure_kg=vol*dmin,
        real_gas_compressibility_factor_at_max_pressure=z,
        coolprop_version=require_coolprop(),hardware_mass_kg=None,
        equipment_manufacturing_lca_complete=False,
        scientific_claim="EOS-only, no vessel dimensions, equipment weight, compression auxiliaries or full BAFU LCA")


@dataclass(frozen=True)
class CompressorStage:
    stage:int
    inlet_pressure_bar_absolute:float
    discharge_pressure_bar_absolute:float
    inlet_temperature_k:float
    discharge_temperature_k:float
    isentropic_work_j_per_kg:float
    shaft_work_j_per_kg:float


@dataclass(frozen=True)
class CompressionResult:
    gas_inlet_pressure_bar_absolute:float
    gas_discharge_pressure_bar_absolute:float
    inlet_temperature_k:float
    isentropic_efficiency:float
    motor_efficiency:float
    stages:int
    total_electrical_kwh_per_kg_hydrogen:float
    total_shaft_energy_kwh_per_kg_hydrogen:float
    stage_diagnostics:tuple
    intercooler_power_and_hardware_included:bool
    coolprop_version:str
    scientific_claim:str


def compression_work(from_pressure_bar_absolute,to_pressure_bar_absolute,
                     inlet_temperature_k,isentropic_efficiency,motor_efficiency,
                     number_of_stages):
    """Intercooled staged H2 compressor model from actual H(P,T), S(P,T).

    Assumes interstage gas returns to inlet T, not a measured process map.
    Does not include intercooler electrical use/equipment, leaks, motor
    part-load performance or capex; do not call it complete compression LCA.
    """
    pin=finite_positive(from_pressure_bar_absolute,"inlet absolute pressure")
    pout=finite_positive(to_pressure_bar_absolute,"outlet absolute pressure")
    eta=finite_positive(isentropic_efficiency,"isentropic efficiency")
    em=finite_positive(motor_efficiency,"motor efficiency")
    if not isinstance(number_of_stages,int) or isinstance(number_of_stages,bool) or not 1<=number_of_stages<=10:
        raise HydrogenPropertyError("number_of_stages must be 1-10 explicit integer")
    if pin>pout:
        raise HydrogenPropertyError("compression outlet pressure cannot be below inlet")
    if eta>1 or em>1:
        raise HydrogenPropertyError("compressor and motor efficiencies cannot exceed one")
    checked_state(pin,inlet_temperature_k)
    checked_state(pout,inlet_temperature_k)
    if pin==pout:
        return CompressionResult(pin,pout,float(inlet_temperature_k),eta,em,
            number_of_stages,0.0,0.0,tuple(),False,require_coolprop(),
            "No compression required; excludes hardware standby or other auxiliaries")

    per_stage_ratio=(pout/pin)**(1/number_of_stages)
    shaft_total=0.0
    stages=[]
    for i in range(number_of_stages):
        p1=pin*per_stage_ratio**i
        p2=pin*per_stage_ratio**(i+1)
        h1=float(PropsSI("Hmass","P",p1*1e5,"T",inlet_temperature_k,"Hydrogen"))
        s1=float(PropsSI("Smass","P",p1*1e5,"T",inlet_temperature_k,"Hydrogen"))
        h2s=float(PropsSI("Hmass","P",p2*1e5,"Smass",s1,"Hydrogen"))
        dh=h2s-h1
        if not all(map(math.isfinite,(h1,s1,h2s,dh))) or dh<=0:
            raise HydrogenPropertyError("nonphysical isentropic property calculation")
        dh_actual=dh/eta
        outlet_t=float(PropsSI("T","P",p2*1e5,"Hmass",h1+dh_actual,"Hydrogen"))
        if not math.isfinite(outlet_t) or outlet_t<inlet_temperature_k:
            raise HydrogenPropertyError("nonphysical compressor discharge temperature")
        shaft_total+=dh_actual
        stages.append(CompressorStage(i+1,p1,p2,float(inlet_temperature_k),
                                      outlet_t,dh,dh_actual))
    return CompressionResult(
        pin,pout,float(inlet_temperature_k),eta,em,number_of_stages,
        shaft_total/(em*3_600_000),shaft_total/3_600_000,
        tuple(stages),False,require_coolprop(),
        "Source-library isentropic model only; no leakage, cooling electricity, equipment, power map or installed plant footprint")


def conservation_residual_kg(start_inventory_kg,produced_kg,delivered_kg,
                             end_inventory_kg,vented_kg,leaked_kg):
    """Physical identity, not a scenario generator or invented loss model."""
    xs=[finite_positive_or_zero(v,n) for n,v in [
        ("start_inventory",start_inventory_kg),("produced",produced_kg),
        ("delivered",delivered_kg),("end_inventory",end_inventory_kg),
        ("vented",vented_kg),("leaked",leaked_kg)]]
    start,prod,delivered,end,vented,leaked=xs
    return start+prod-delivered-end-vented-leaked


def finite_positive_or_zero(value,name):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
        raise HydrogenPropertyError(f"{name} must be finite and nonnegative")
    return float(value)
