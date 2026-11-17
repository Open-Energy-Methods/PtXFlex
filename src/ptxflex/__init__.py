"""Hypothetical e-methanol MILP with independent constraint checks."""
from .model import solve, audit_solution, H2_PER_KG_MEOH, CO2_PER_KG_MEOH
__all__ = ["solve", "audit_solution", "H2_PER_KG_MEOH", "CO2_PER_KG_MEOH"]
