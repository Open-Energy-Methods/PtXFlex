"""Published-vessel reference bank, NOT an engineered/certified H2 installation.

Source: "Comparative techno-economic assessment of stationary hydrogen
storage technologies", Int. J. Hydrogen Energy, DOI
10.1016/j.ijhydene.2025.152849, Table 2, with representative per-vessel
empty equipment mass, internal free volume and reference pressure.

Two DIFFERENT interpretations are kept separate:
  max_inventory: original PyNEXUS 20/40 t refers to upper storage-state kg;
  usable_service: hypothetical requested withdrawable hydrogen mass.

Published kg H2 per vessel is at reference rated pressure, not the
withdrawable pressure-swing inventory. Reference source pressure basis
(gauge vs absolute) is unresolved: absolute is a research screening
assumption only, never a pressure vessel specification.

The original numerical model configuration sets PEM outlet to 30bar
and pipeline minimum delivery pressure to 20bar. No claim that either
corresponds to a physically installed vessel or compressor.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
import math
from .hydrogen_physics import hydrogen_density_kg_m3, HydrogenPropertyError

REFERENCE_DOI="10.1016/j.ijhydene.2025.152849"
REFERENCE_URL="https://doi.org/10.1016/j.ijhydene.2025.152849"
REFERENCE_LOCATOR="Table 2: Reference parameters for CGH2 storage"
ISO_STATUS="ISO/FDIS 19884-1 under development at 2026-11-13"


@dataclass(frozen=True)
class SourceVessel:
    id: str
    technology: str
    max_reference_pressure_bar: float
    internal_volume_m3: float
    empty_vessel_mass_kg: float
    publication_h2_at_rated_kg: float
    original_source_doi: str=REFERENCE_DOI
    source_locator: str=REFERENCE_LOCATOR


# Direct published per-vessel reference values, NOT H2-to-steel mass factors.
PUBLISHED_VESSELS={
 "I_30bar":SourceVessel("I_30bar","Type I steel",30.,2.1,2300.,5.),
 "I_200bar":SourceVessel("I_200bar","Type I steel",200.,1.8,2400.,26.),
 "II_350bar":SourceVessel("II_350bar","Type II steel+composite",350.,1.3,2150.,31.),
 "III_350bar":SourceVessel("III_350bar","Type III metallic liner+composite",350.,1.8,1300.,43.),
 "IV_350bar":SourceVessel("IV_350bar","Type IV polymer liner+composite",350.,1.8,1200.,43.),
}

@dataclass(frozen=True)
class VesselBankScreen:
    original_scenario_capacity_kg:float
    source_capacity_semantics:str
    vessel_reference_id:str
    source_technology:str
    source_doi:str
    source_reference_table:str
    screening_pressure_basis:str
    upper_pressure_bar_absolute:float
    lower_pressure_bar_absolute:float
    screening_gas_temperature_k:float
    number_of_reference_vessels:int
    gross_hydrogen_at_max_pressure_kg:float
    residual_heel_hydrogen_at_min_pressure_kg:float
    withdrawable_hydrogen_between_pressures_kg:float
    empty_reference_vessels_total_kg:float
    representative_internal_free_volume_total_m3:float
    published_reference_nominal_kg_h2_per_vessel:float
    actual_usable_below_model_nominal_capacity:bool
    supports_and_compressor_mass_known:bool
    vessels_are_certified_for_this_duty:bool
    native_manufacturing_lca_calculated:bool
    technical_restrictions:tuple[str,...]


def screen_vessel_bank(vessel_id,original_model_capacity_kg,lower_pressure_bar_absolute,
                       temperature_k,*,capacity_semantics="max_inventory"):
    if vessel_id not in PUBLISHED_VESSELS:
        raise HydrogenPropertyError("unknown published vessel reference")
    if capacity_semantics not in ("max_inventory","usable_service"):
        raise HydrogenPropertyError("capacity semantics must be explicit")
    if isinstance(original_model_capacity_kg,bool) or not isinstance(original_model_capacity_kg,(int,float)):
        raise HydrogenPropertyError("capacity requires numerical kg H2")
    amount=float(original_model_capacity_kg)
    if not math.isfinite(amount) or amount<=0:
        raise HydrogenPropertyError("capacity must be finite, positive")
    source=PUBLISHED_VESSELS[vessel_id]
    if isinstance(lower_pressure_bar_absolute,bool) or not isinstance(lower_pressure_bar_absolute,(int,float)):
        raise HydrogenPropertyError("minimum absolute pressure must be numerical")
    pmin=float(lower_pressure_bar_absolute)
    if not math.isfinite(pmin) or not 1<=pmin<source.max_reference_pressure_bar:
        raise HydrogenPropertyError("minimum delivery pressure outside screened storage range")
    dmax=hydrogen_density_kg_m3(source.max_reference_pressure_bar,temperature_k)
    dmin=hydrogen_density_kg_m3(pmin,temperature_k)
    max_mass=source.internal_volume_m3*dmax
    heel_mass=source.internal_volume_m3*dmin
    usable_mass=max_mass-heel_mass
    if usable_mass<=0:
        raise HydrogenPropertyError("nonphysical real-gas density pressure swing")
    n=math.ceil(amount/(max_mass if capacity_semantics=="max_inventory" else usable_mass))
    if not 1<=n<=10_000_000:
        raise HydrogenPropertyError("invalid bank vessel count")
    gross=n*max_mass
    heel=n*heel_mass
    working=gross-heel
    return VesselBankScreen(
       original_scenario_capacity_kg=amount,source_capacity_semantics=capacity_semantics,
       vessel_reference_id=source.id,source_technology=source.technology,
       source_doi=source.original_source_doi,source_reference_table=source.source_locator,
       screening_pressure_basis="ABSOLUTE screening assumption; paper reference bar pressure basis needs confirmation",
       upper_pressure_bar_absolute=source.max_reference_pressure_bar,
       lower_pressure_bar_absolute=pmin,screening_gas_temperature_k=float(temperature_k),
       number_of_reference_vessels=n,
       gross_hydrogen_at_max_pressure_kg=gross,
       residual_heel_hydrogen_at_min_pressure_kg=heel,
       withdrawable_hydrogen_between_pressures_kg=working,
       empty_reference_vessels_total_kg=n*source.empty_vessel_mass_kg,
       representative_internal_free_volume_total_m3=n*source.internal_volume_m3,
       published_reference_nominal_kg_h2_per_vessel=source.publication_h2_at_rated_kg,
       actual_usable_below_model_nominal_capacity=(working<amount),
       supports_and_compressor_mass_known=False,
       vessels_are_certified_for_this_duty=False,
       native_manufacturing_lca_calculated=False,
       technical_restrictions=(
         "Source Table 2 vessel dimensions/mass are reference examples, not vendor design drawings.",
         "Original model capacity is upper storage-state kg, not recoverable H2 or equipment mass.",
         "Published pressure basis (gauge or absolute) not explicitly reconciled; absolute assumed for screening.",
         "No support/manifold/valve/piping, compressor/cooling hardware mass, plant transport or fabrication inventory.",
         "No ASME/EN/ISO vessel conformity, fatigue, rupture, H2 embrittlement or site approval.",
         "No pressure transient, temperature swing, measured leakage or variable-efficiency motor map."),
    )


def make_source_based_sensitivity(*,temperature_k=298.15,withdrawal_pressure_bar_absolute=20.0):
    """Two 2023 original H2 capacities times five authentic reference vessels."""
    rows=[]
    for case,amount in (("E",20_000.0),("E_plus_S",40_000.0)):
        for v in PUBLISHED_VESSELS:
            for interpretation in ("max_inventory","usable_service"):
                result=screen_vessel_bank(v,amount,withdrawal_pressure_bar_absolute,
                     temperature_k,capacity_semantics=interpretation)
                rows.append({"original_model_case":case,**asdict(result)})
    return {
      "schema_version":"ptxflex.hydrogen_published_vessel_bank_source_sensitivity.v0.1",
      "source_paper_doi":REFERENCE_DOI,
      "source_table":REFERENCE_LOCATOR,
      "upstream_original_model":"Frozen PyNEXUS E=20,000 / E+S=40,000 kg upper-state-bound",
      "iso_standard_status":ISO_STATUS,
      "screening_conditions_not_vessel_specification":True,
      "source_library":"CoolProp 8.0.0 pure hydrogen EOS",
      "any_physical_BOM_complete":False,
      "any_native_tank_equipment_LCIA_executed":False,
      "comparative_environmental_superiority_claim":False,
      "cases":rows
    }
