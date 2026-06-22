"""
thermal_pacer/__init__.py

Public API surface for the IntelligentThermalPacer client library.
Exposes ThermalGuard as the sole user-facing symbol.
"""

from thermal_pacer.client import ThermalGuard

__all__ = ["ThermalGuard"]
__version__ = "1.0.0"
