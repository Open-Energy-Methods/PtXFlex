"""F2→F3 bridge: source-parameterized, pressure-limited vessel bank duty.

A pressure *screen* is not a certified buildable installation. Vessel
internal free volume and empty mass are from published IJHE Table 2.
Hydrogen density and conservative compressor enthalpy are from CoolProp 8.
Compressor performance assumptions are sourced in the Netherlands RVO/LBST
2023 RFNBO report: compressor efficiency 80%, motor efficiency 90%.
The paper's vessel reference pressures are taken as absolute for this
screening only. Suction/interstage 313 K is from the same RVO model.
No cooler power or site-specific motor/part-load map is included.

Max-inventory vs withdrawable-H2 cases have different physical meaning:
 max_inventory: old 20/40t upper gross stored-H2 bound; S>=EOS heel;
 usable_service: 20/40t recoverable H2 from physical bank; S models
    withdrawable mass, gross mass = S + real-gas residual heel.
The original source initial/terminal 10t is not changed in either model,
but its physical meaning is explicitly different in each sensitivity.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math

from .hydrogen_physics import (
    HydrogenPropertyError, compression_work, require_coolprop
)
from .storage_reference_vessels import screen_vessel_bank

RVO_SOURCE="https://www.rvo.nl/sites/default/files/2023-12/GHG_EF_including_conversion_efficiencies_for_RFNBO_GHG_calculations_LBST.pdf"
RVO_SOURCE_LOCATOR="LBST, RFNBO Greenhouse Gas Emissions, compression energy method and Table 28, 2023"
STORAGE_SOURCE="https://doi.org/10.1016/j.ijhydene.2025.152849"
SCREENING_TEMPERATURE_K=313.0
COMPRESSOR_EFFICIENCY=0.80
MOTOR_EFFICIENCY=0.90
COMPRESSOR_STAGES=2


@dataclass(frozen=True)
class ScreenedPhysicalDuty:
    vessel_id:str
    scenario_capacity_kg:float
    capacity_semantics:str
    vessel_count:int
    bank_free_volume_m3:float
    bank_empty_vessel_mass_kg:float
    gas_heel_kg:float
    bank_gas_at_reference_max_kg:float
    gas_minimum_absolute_bar:float
    gas_maximum_absolute_bar:float
    temperature_k:float
    source_PEM_outlet_absolute_bar:float
    compressor_electrical_kwh_per_kg_charged:float
    compressor_stages:int
    compressor_eta_isentropic:float
    motor_eta:float
    is_conservative_fixed_upper_pressure_work_screen:bool
    includes_cooling_electricity:bool
    includes_compressor_equipment_manufacture:bool
    includes_vessel_material_fabrication_lca:bool
    source_vessel_doi:str
    source_compressor_assumptions_uri:str
    source_property_library:str

    def min_model_inventory_kg(self):
        return self.gas_heel_kg if self.capacity_semantics=="max_inventory" else 0.0

    def stored_total_gas_kg(self,model_stock_kg):
        return float(model_stock_kg)+(self.gas_heel_kg if self.capacity_semantics=="usable_service" else 0.)

    def compressor_mw_per_kg_h(self):
        # (kg per hour)*(kWh per kg) / 1000 = MW average over 1 hour.
        return self.compressor_electrical_kwh_per_kg_charged/1000.0

    def inventory_equation_fixed_heel_leak_kg_h(self,loss_per_hour):
        return loss_per_hour*self.gas_heel_kg if self.capacity_semantics=="usable_service" else 0.0


def build_screened_pressure_duty(vessel_id,original_capacity_kg,
        *,capacity_semantics="max_inventory",
        source_PEM_outlet_bar_absolute=30.0,
        delivery_min_bar_absolute=20.0,
        temperature_k=SCREENING_TEMPERATURE_K,
        eta_isentropic=COMPRESSOR_EFFICIENCY,
        motor_eta=MOTOR_EFFICIENCY,
        stages=COMPRESSOR_STAGES):
    """Actual source equations plus *explicitly selected* engineering scenario.

    80% / 90% are RVO/LBST literature assumptions, not equipment measurements.
    Compressor charges every kg as if all charging were 30→rated pressure,
    an upper-pressure work screen, not pressure-varying mechanical efficiency.
    The screen assumes the same T in bank across entire year.
    """
    source=screen_vessel_bank(vessel_id,float(original_capacity_kg),
        float(delivery_min_bar_absolute),float(temperature_k),
        capacity_semantics=capacity_semantics)
    if not math.isclose(source.pressure_maximum_bar_absolute if hasattr(source,"pressure_maximum_bar_absolute")
                        else source.upper_pressure_bar_absolute,
                        source.upper_pressure_bar_absolute):
        raise HydrogenPropertyError("published vessel maximum pressure inconsistent")
    if source_PEM_outlet_bar_absolute<delivery_min_bar_absolute:
        raise HydrogenPropertyError("PEM source pressure below gate; upstream delivery compression not modelled")
    if source_PEM_outlet_bar_absolute>source.upper_pressure_bar_absolute:
        raise HydrogenPropertyError("PEM source exceeds vessel pressure rating")
    compression=compression_work(float(source_PEM_outlet_bar_absolute),
        source.upper_pressure_bar_absolute,float(temperature_k),
        float(eta_isentropic),float(motor_eta),int(stages))
    # Both physical storage interpretations must have enough gas volume for
    # the original 10t *model initial/terminal*, never hidden free gas.
    return ScreenedPhysicalDuty(
        vessel_id=source.vessel_reference_id,
        scenario_capacity_kg=float(original_capacity_kg),
        capacity_semantics=capacity_semantics,
        vessel_count=source.number_of_reference_vessels,
        bank_free_volume_m3=source.representative_internal_free_volume_total_m3,
        bank_empty_vessel_mass_kg=source.empty_reference_vessels_total_kg,
        gas_heel_kg=source.residual_heel_hydrogen_at_min_pressure_kg,
        bank_gas_at_reference_max_kg=source.gross_hydrogen_at_max_pressure_kg,
        gas_minimum_absolute_bar=source.lower_pressure_bar_absolute,
        gas_maximum_absolute_bar=source.upper_pressure_bar_absolute,
        temperature_k=source.screening_gas_temperature_k,
        source_PEM_outlet_absolute_bar=float(source_PEM_outlet_bar_absolute),
        compressor_electrical_kwh_per_kg_charged=compression.total_electrical_kwh_per_kg_hydrogen,
        compressor_stages=int(stages),
        compressor_eta_isentropic=float(eta_isentropic),
        motor_eta=float(motor_eta),
        is_conservative_fixed_upper_pressure_work_screen=True,
        includes_cooling_electricity=False,
        includes_compressor_equipment_manufacture=False,
        includes_vessel_material_fabrication_lca=False,
        source_vessel_doi=STORAGE_SOURCE,
        source_compressor_assumptions_uri=RVO_SOURCE,
        source_property_library="CoolProp==8.0.0 Hydrogen; real-gas density and actual source enthalpy")

def validate_screened_duty(duty,source_params):
    if not isinstance(duty,ScreenedPhysicalDuty):
        raise HydrogenPropertyError("screened duty must be a source-built immutable object")
    if abs(duty.scenario_capacity_kg-source_params["capacity_kg"])>1e-7:
        raise HydrogenPropertyError("vessel bank scenario capacity != original source case")
    if not duty.min_model_inventory_kg()<=source_params["initial_kg"]<=duty.scenario_capacity_kg:
        raise HydrogenPropertyError("original source initial stock below residual EOS heel or above model bank")
    if not duty.min_model_inventory_kg()<=source_params["terminal_kg"]<=duty.scenario_capacity_kg:
        raise HydrogenPropertyError("original terminal source stock below residual EOS heel")
    if not math.isclose(duty.source_PEM_outlet_absolute_bar,
        source_params["source_bafu_PEM_pressure_bar"],rel_tol=0,abs_tol=1e-9):
        raise HydrogenPropertyError("original PEM pressure incompatible with compressor suction pressure")
    if duty.gas_minimum_absolute_bar<source_params["source_pipeline_min_delivery_pressure_bar"]-1e-9:
        raise HydrogenPropertyError("physical withdrawal pressure below source delivery gate")
    max_total=duty.stored_total_gas_kg(source_params["capacity_kg"])
    if max_total>duty.bank_gas_at_reference_max_kg+1e-6:
        raise HydrogenPropertyError("physical bank capacity exceeded after adding residual heel")
    if any([duty.includes_cooling_electricity,duty.includes_compressor_equipment_manufacture,
            duty.includes_vessel_material_fabrication_lca]):
        raise HydrogenPropertyError("unsupported claimed physical plant completeness")
    require_coolprop()
    return True


def audit_gas_pressure_boundaries(duty,model_stock_vector):
    """Check all hourly gas masses via EOS monotonicity, evaluate extrema.

    At constant T density is monotonically related to pressure. Therefore
    checking min/max gas states exactly via EOS is enough to prove each
    intermediate state meets bank pressure range without approximate
    polynomial fitting or expensive per-hour properties.
    """
    from CoolProp.CoolProp import PropsSI
    import numpy as np
    s=np.asarray(model_stock_vector,dtype=float)
    if s.ndim!=1 or s.size<1 or not np.isfinite(s).all():
        raise HydrogenPropertyError("invalid solved H2 stock time-series")
    total=s+(duty.gas_heel_kg if duty.capacity_semantics=="usable_service" else 0)
    physical_min=float(np.min(total))
    physical_max=float(np.max(total))
    if physical_min<=0:
        raise HydrogenPropertyError("zero gas in pressurized storage or invalid source state")
    def pressure(mass):
        return float(PropsSI("P","Dmass",mass/duty.bank_free_volume_m3,
            "T",duty.temperature_k,"Hydrogen"))/1e5
    min_bar=pressure(physical_min)
    max_bar=pressure(physical_max)
    if min_bar<duty.gas_minimum_absolute_bar-1e-5 or max_bar>duty.gas_maximum_absolute_bar+1e-5:
        raise HydrogenPropertyError(f"solved storage pressure out of bounds {min_bar=} {max_bar=}")
    return {
      "real_gas_minimum_dispatched_pressure_bar_absolute":min_bar,
      "real_gas_maximum_dispatched_pressure_bar_absolute":max_bar,
      "min_total_gas_mass_kg":physical_min,
      "max_total_gas_mass_kg":physical_max,
      "EOS_hourly_mass_bounds_imply_pressure_limits":True,
      "temperature_k_is_fixed_screening_assumption":True
    }
