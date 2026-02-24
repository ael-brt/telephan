"""
Module de calcul des KPI TELEPHAN.

Ce module centralise :
- La configuration des 14 KPI (bloc, libellé, unité, type, format, cible, etc.).
- Les fonctions de calcul individuelles.
- Une fonction utilitaire compute_all_kpis pour obtenir tous les résultats de KPI dans un format standard.

Les données attendues dans `data` sont fournies par la couche data_access (DataFrames).
Colonnes et hypothèses sont précisées dans chaque fonction ; ajouter/adapter si la structure réelle diffère.
"""

from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import pandas as pd

from . import config, styles

# Métadonnées des KPI
KPI_META: Dict[str, Dict] = {
    # PERFORMANCE
    "machine_utilization": {
        "block": "performance",
        "label": "Taux d’utilisation des machines",
        "unit": "%",
        "value_type": "percentage",
        "format": "gauge",
        "description": "Temps en production / temps disponible",
        "fields_needed": ["Busy", "TimeStamp"],  # tblmachinereport
        "better_when": "higher",
        "target_default": 85.0,
    },
    "trs": {
        "block": "performance",
        "label": "TRS (Taux de Rendement Synthétique)",
        "unit": "%",
        "value_type": "percentage",
        "format": "gauge",
        "description": "Disponibilité x Performance x Qualité",
        "fields_needed": ["Busy", "TimeStamp", "ErrorID"],  # Busy (machine), ErrorID (parts)
        "better_when": "higher",
        "target_default": 80.0,
    },
    "cycle_time": {
        "block": "performance",
        "label": "Temps de cycle",
        "unit": "s",
        "value_type": "duration",
        "format": "gauge",
        "description": "Temps moyen entre deux pièces produites",
        "fields_needed": ["TimeStamp"],  # tblpartsreport
        "better_when": "lower",
        "target_default": 60.0,
    },
    "operation_execution_rate": {
        "block": "performance",
        "label": "Taux d’exécution des opérations",
        "unit": "%",
        "value_type": "percentage",
        "format": "gauge",
        "description": "Opérations terminées / opérations planifiées",
        "fields_needed": ["Start", "End"],  # tblfinstep
        "better_when": "higher",
        "target_default": 95.0,
    },
    # QUALITÉ
    "non_conformity_rate": {
        "block": "quality",
        "label": "Taux de non-conformité",
        "unit": "%",
        "value_type": "percentage",
        "format": "bar_or_line",
        "description": "Pièces non conformes / pièces produites",
        "fields_needed": ["ErrorID"],  # tblpartsreport
        "better_when": "lower",
        "target_default": 2.0,
    },
    "error_count": {
        "block": "quality",
        "label": "Nombre total d’erreurs",
        "unit": "nb",
        "value_type": "integer",
        "format": "counter",
        "description": "Erreurs / anomalies sur la période",
        "fields_needed": ["ErrorID", "ErrorL0", "ErrorL1", "ErrorL2"],  # parts + machine
        "better_when": "lower",
        "target_default": 0,
    },
    "critical_error_count": {
        "block": "quality",
        "label": "Nombre d’erreurs critiques",
        "unit": "nb",
        "value_type": "integer",
        "format": "counter",
        "description": "Erreurs critiques (niveau 2)",
        "fields_needed": ["ErrorL2"],  # tblmachinereport
        "better_when": "lower",
        "target_default": 0,
    },
    # STOCK
    "average_stock_level": {
        "block": "stock",
        "label": "Niveau moyen de stock",
        "unit": "unités",
        "value_type": "number",
        "format": "line_or_bar",
        "description": "Stock moyen sur la période",
        "fields_needed": ["Quantity"],  # tblbufferpos
        "better_when": "lower",
        "target_default": 1000.0,
    },
    "storage_occupation_rate": {
        "block": "stock",
        "label": "Taux d’occupation du stockage",
        "unit": "%",
        "value_type": "percentage",
        "format": "gauge",
        "description": "Stock / capacité stockage",
        "fields_needed": ["Quantity", "QuantityMax"],  # tblbufferpos
        "better_when": "lower",
        "target_default": 85.0,
    },
    "wip_occupation_rate": {
        "block": "stock",
        "label": "Taux d’occupation des encours",
        "unit": "%",
        "value_type": "percentage",
        "format": "gauge",
        "description": "Encours / capacité encours (Zone > 0 considérée encours)",
        "fields_needed": ["Quantity", "QuantityMax", "Zone"],  # tblbufferpos
        "better_when": "lower",
        "target_default": 80.0,
    },
    # DÉLAI
    "global_lead_time": {
        "block": "delay",
        "label": "Lead Time global",
        "unit": "min",
        "value_type": "duration",
        "format": "gauge",
        "description": "Temps moyen Start -> End des ordres finis",
        "fields_needed": ["Start", "End"],  # tblfinorder
        "better_when": "lower",
        "target_default": 120.0,
    },
    "otd": {
        "block": "delay",
        "label": "OTD (On Time Delivery)",
        "unit": "%",
        "value_type": "percentage",
        "format": "gauge",
        "description": "Commandes livrées dans les temps / total",
        "fields_needed": ["End", "PlannedEnd"],  # tblfinorder
        "better_when": "higher",
        "target_default": 95.0,
    },
    # ÉNERGIE
    "energy_per_unit": {
        "block": "energy",
        "label": "Consommation énergétique",
        "unit": "kWh/unit",
        "value_type": "intensity",
        "format": "raw_or_bar",
        "description": "Énergie consommée par pièce (Real ou Calc)",
        "fields_needed": ["ElectricEnergyReal", "ElectricEnergyCalc", "End"],  # tblfinstep + nombre de pièces
        "better_when": "lower",
        "target_default": 0.5,
    },
    "air_per_unit": {
        "block": "energy",
        "label": "Air comprimé moyen",
        "unit": "L/unit",
        "value_type": "intensity",
        "format": "raw_or_bar",
        "description": "Air comprimé par pièce (Real ou Calc)",
        "fields_needed": ["CompressedAirReal", "CompressedAirCalc", "End"],  # tblfinstep + nombre de pièces
        "better_when": "lower",
        "target_default": 10.0,
    },
}


def compute_color(value: Optional[float], target: Optional[float], better_when: str) -> str:
    """
    Retourne une couleur hex selon la performance.
    - higher: ratio = value/target
    - lower: ratio = target/value
    Seuils: vert >=100%, orange >=80%, rouge sinon.
    """
    if value is None or target in (None, 0):
        return styles.COLORS["border_orange_light"]

    ratio = (value / target) if better_when == "higher" else (target / value if value else 0)
    if ratio >= 1.0:
        return styles.COLORS["ok"]
    if ratio >= 0.8:
        return styles.COLORS["warn"]
    return styles.COLORS["alert"]


def _result(key: str, value: Optional[float], target: Optional[float], ratio: Optional[float]) -> Dict:
    meta = KPI_META[key]
    return {
        "key": key,
        "label": meta["label"],
        "value": None if value is None else (round(value, 4) if isinstance(value, float) else value),
        "unit": meta["unit"],
        "type": meta["value_type"],
        "format": meta["format"],
        "target": target,
        "better_when": meta["better_when"],
        "ratio": ratio,
        "color": compute_color(value, target, meta["better_when"]),
    }


def compute_machine_utilization(data: Dict[str, pd.DataFrame], target: Optional[float] = None) -> Dict:
    """
    Attendu dans data:
      data["machine_report"]: DataFrame tblmachinereport avec colonnes Busy (0/1), TimeStamp.
    """
    df = data.get("machine_report", pd.DataFrame())
    meta = KPI_META["machine_utilization"]
    target = target if target is not None else meta["target_default"]
    if df.empty:
        return _result("machine_utilization", None, target, None)
    busy_ratio = df["Busy"].fillna(0).mean()
    value_pct = busy_ratio * 100
    ratio = (value_pct / target) if target else None
    return _result("machine_utilization", value_pct, target, ratio)


def compute_trs(data: Dict[str, pd.DataFrame], target: Optional[float] = None) -> Dict:
    """
    Attendu:
      machine_report (Busy),
      parts_report (ErrorID, TimeStamp).
    Hypothèse: performance calculée vs cadence cible (config.KPI_TARGETS['cycle_time']).
    """
    meta = KPI_META["trs"]
    target = target if target is not None else meta["target_default"]
    machine = data.get("machine_report", pd.DataFrame())
    parts = data.get("parts_report", pd.DataFrame())
    if machine.empty or parts.empty:
        return _result("trs", None, target, None)

    availability = machine["Busy"].fillna(0).mean()
    cycle_target = config.KPI_TARGETS.get("cycle_time", 60.0)  # secondes
    shift_seconds = config.SHIFT_WINDOW.total_seconds()
    theoretical_output = shift_seconds / cycle_target if cycle_target else 0
    performance = len(parts) / theoretical_output if theoretical_output else 0
    non_conf_rate = (parts["ErrorID"].fillna(0) > 0).mean()
    quality = 1 - non_conf_rate

    trs_value = availability * performance * quality * 100  # en %
    ratio = (trs_value / target) if target else None
    return _result("trs", trs_value, target, ratio)


def compute_cycle_time(data: Dict[str, pd.DataFrame], target: Optional[float] = None) -> Dict:
    """
    Attendu:
      parts_report avec TimeStamp (datetime).
    """
    meta = KPI_META["cycle_time"]
    target = target if target is not None else meta["target_default"]
    parts = data.get("parts_report", pd.DataFrame())
    if parts.empty or len(parts) < 2:
        return _result("cycle_time", None, target, None)
    ts = pd.to_datetime(parts["TimeStamp"]).sort_values()
    deltas = ts.diff().dt.total_seconds().dropna()
    avg = deltas.mean() if not deltas.empty else None
    ratio = (target / avg) if (avg and target) else None  # lower is better
    return _result("cycle_time", avg, target, ratio)


def compute_operation_execution_rate(data: Dict[str, pd.DataFrame], target: Optional[float] = None) -> Dict:
    """
    Attendu:
      finstep avec colonnes Start/End (datetime).
    """
    meta = KPI_META["operation_execution_rate"]
    target = target if target is not None else meta["target_default"]
    finstep = data.get("finstep", pd.DataFrame())
    if finstep.empty:
        return _result("operation_execution_rate", None, target, None)
    total = len(finstep)
    done = finstep["End"].notna().sum()
    rate = (done / total) * 100 if total else 0
    ratio = (rate / target) if target else None
    return _result("operation_execution_rate", rate, target, ratio)


def compute_non_conformity_rate(data: Dict[str, pd.DataFrame], target: Optional[float] = None) -> Dict:
    """
    Attendu:
      parts_report avec ErrorID (>0 = non conforme).
    """
    meta = KPI_META["non_conformity_rate"]
    target = target if target is not None else meta["target_default"]
    parts = data.get("parts_report", pd.DataFrame())
    if parts.empty:
        return _result("non_conformity_rate", None, target, None)
    total = len(parts)
    non_conf = (parts["ErrorID"].fillna(0) > 0).sum()
    rate = (non_conf / total) * 100 if total else 0
    ratio = (target / rate) if (rate and target) else None  # lower is better
    return _result("non_conformity_rate", rate, target, ratio)


def compute_error_count(data: Dict[str, pd.DataFrame], target: Optional[float] = None) -> Dict:
    """
    Attendu:
      parts_report (ErrorID), machine_report (ErrorL0/1/2).
    """
    meta = KPI_META["error_count"]
    target = target if target is not None else meta["target_default"]
    parts = data.get("parts_report", pd.DataFrame())
    machine = data.get("machine_report", pd.DataFrame())
    errors_parts = (parts["ErrorID"].fillna(0) > 0).sum() if not parts.empty else 0
    errors_machine = 0
    if not machine.empty:
        errors_machine = machine[["ErrorL0", "ErrorL1", "ErrorL2"]].fillna(0).sum().sum()
    total_errors = int(errors_parts + errors_machine)
    ratio = (target / total_errors) if (total_errors and target) else None
    return _result("error_count", total_errors, target, ratio)


def compute_critical_error_count(data: Dict[str, pd.DataFrame], target: Optional[float] = None) -> Dict:
    """
    Attendu:
      machine_report avec ErrorL2 (critique).
    """
    meta = KPI_META["critical_error_count"]
    target = target if target is not None else meta["target_default"]
    machine = data.get("machine_report", pd.DataFrame())
    count = int((machine["ErrorL2"].fillna(0) > 0).sum()) if not machine.empty else 0
    ratio = (target / count) if (count and target) else None
    return _result("critical_error_count", count, target, ratio)


def compute_average_stock_level(data: Dict[str, pd.DataFrame], target: Optional[float] = None) -> Dict:
    """
    Attendu:
      buffer_positions avec Quantity.
    """
    meta = KPI_META["average_stock_level"]
    target = target if target is not None else meta["target_default"]
    buf = data.get("buffer_positions", pd.DataFrame())
    if buf.empty:
        return _result("average_stock_level", None, target, None)
    avg_stock = buf["Quantity"].fillna(0).mean()
    ratio = (target / avg_stock) if (avg_stock and target) else None  # lower is better
    return _result("average_stock_level", avg_stock, target, ratio)


def compute_storage_occupation_rate(data: Dict[str, pd.DataFrame], target: Optional[float] = None) -> Dict:
    """
    Attendu:
      buffer_positions avec Quantity, QuantityMax.
    """
    meta = KPI_META["storage_occupation_rate"]
    target = target if target is not None else meta["target_default"]
    buf = data.get("buffer_positions", pd.DataFrame())
    if buf.empty:
        return _result("storage_occupation_rate", None, target, None)
    qty = buf["Quantity"].fillna(0).sum()
    cap = buf["QuantityMax"].replace(0, np.nan).sum()
    occ = (qty / cap) * 100 if cap else None
    ratio = (target / occ) if (occ and target) else None  # lower is better
    return _result("storage_occupation_rate", occ, target, ratio)


def compute_wip_occupation_rate(data: Dict[str, pd.DataFrame], target: Optional[float] = None) -> Dict:
    """
    Attendu:
      buffer_positions avec Zone (>0 considéré encours), Quantity, QuantityMax.
    """
    meta = KPI_META["wip_occupation_rate"]
    target = target if target is not None else meta["target_default"]
    buf = data.get("buffer_positions", pd.DataFrame())
    if buf.empty:
        return _result("wip_occupation_rate", None, target, None)
    wip = buf[buf["Zone"].fillna(0) > 0]
    qty = wip["Quantity"].fillna(0).sum()
    cap = wip["QuantityMax"].replace(0, np.nan).sum()
    occ = (qty / cap) * 100 if cap else None
    ratio = (target / occ) if (occ and target) else None  # lower is better
    return _result("wip_occupation_rate", occ, target, ratio)


def compute_global_lead_time(data: Dict[str, pd.DataFrame], target: Optional[float] = None) -> Dict:
    """
    Attendu:
      finorders avec Start et End (datetime).
    """
    meta = KPI_META["global_lead_time"]
    target = target if target is not None else meta["target_default"]
    orders = data.get("finorders", pd.DataFrame())
    if orders.empty:
        return _result("global_lead_time", None, target, None)
    df = orders.copy()
    df = df[df["Start"].notna() & df["End"].notna()]
    if df.empty:
        return _result("global_lead_time", None, target, None)
    df["Start"] = pd.to_datetime(df["Start"])
    df["End"] = pd.to_datetime(df["End"])
    lead_seconds = (df["End"] - df["Start"]).dt.total_seconds()
    avg_min = lead_seconds.mean() / 60 if not lead_seconds.empty else None
    ratio = (target / avg_min) if (avg_min and target) else None  # lower is better
    return _result("global_lead_time", avg_min, target, ratio)


def compute_otd(data: Dict[str, pd.DataFrame], target: Optional[float] = None) -> Dict:
    """
    Attendu:
      finorders avec End et PlannedEnd (datetime).
    """
    meta = KPI_META["otd"]
    target = target if target is not None else meta["target_default"]
    orders = data.get("finorders", pd.DataFrame())
    if orders.empty:
        return _result("otd", None, target, None)
    df = orders.copy()
    df = df[df["End"].notna() & df["PlannedEnd"].notna()]
    if df.empty:
        return _result("otd", None, target, None)
    df["End"] = pd.to_datetime(df["End"])
    df["PlannedEnd"] = pd.to_datetime(df["PlannedEnd"])
    on_time = (df["End"] <= df["PlannedEnd"]).mean() * 100
    ratio = (on_time / target) if target else None
    return _result("otd", on_time, target, ratio)


def compute_energy_per_unit(data: Dict[str, pd.DataFrame], target: Optional[float] = None) -> Dict:
    """
    Attendu:
      finstep avec ElectricEnergyReal/Calc,
      parts_report pour nombre de pièces (len).
    Hypothèse: énergie en Wh -> conversion en kWh.
    """
    meta = KPI_META["energy_per_unit"]
    target = target if target is not None else meta["target_default"]
    finstep = data.get("finstep", pd.DataFrame())
    parts = data.get("parts_report", pd.DataFrame())
    produced = len(parts) if not parts.empty else 0
    if finstep.empty or produced == 0:
        return _result("energy_per_unit", None, target, None)
    energy_col = finstep["ElectricEnergyReal"].fillna(0)
    if (energy_col == 0).all():
        energy_col = finstep["ElectricEnergyCalc"].fillna(0)
    energy_wh = energy_col.sum()
    energy_per_unit = (energy_wh / produced) / 1000 if produced else None
    ratio = (target / energy_per_unit) if (energy_per_unit and target) else None  # lower is better
    return _result("energy_per_unit", energy_per_unit, target, ratio)


def compute_air_per_unit(data: Dict[str, pd.DataFrame], target: Optional[float] = None) -> Dict:
    """
    Attendu:
      finstep avec CompressedAirReal/Calc,
      parts_report pour nombre de pièces.
    """
    meta = KPI_META["air_per_unit"]
    target = target if target is not None else meta["target_default"]
    finstep = data.get("finstep", pd.DataFrame())
    parts = data.get("parts_report", pd.DataFrame())
    produced = len(parts) if not parts.empty else 0
    if finstep.empty or produced == 0:
        return _result("air_per_unit", None, target, None)
    air_col = finstep["CompressedAirReal"].fillna(0)
    if (air_col == 0).all():
        air_col = finstep["CompressedAirCalc"].fillna(0)
    air_per_unit = (air_col.sum() / produced) if produced else None
    ratio = (target / air_per_unit) if (air_per_unit and target) else None  # lower is better
    return _result("air_per_unit", air_per_unit, target, ratio)


def compute_all_kpis(data: Dict[str, pd.DataFrame], overrides: Optional[Dict[str, float]] = None) -> Dict[str, Dict]:
    """
    data : dict de DataFrames fourni par data_access.
      clés attendues: parts_report, machine_report, finorders, finstep, buffer_positions.
    overrides : dict optionnel pour surcharger certaines cibles par KPI.
    Retourne un dict {kpi_key: result_dict}.
    """
    overrides = overrides or {}
    results = {
        "machine_utilization": compute_machine_utilization(data, target=overrides.get("machine_utilization")),
        "trs": compute_trs(data, target=overrides.get("trs")),
        "cycle_time": compute_cycle_time(data, target=overrides.get("cycle_time")),
        "operation_execution_rate": compute_operation_execution_rate(data, target=overrides.get("operation_execution_rate")),
        "non_conformity_rate": compute_non_conformity_rate(data, target=overrides.get("non_conformity_rate")),
        "error_count": compute_error_count(data, target=overrides.get("error_count")),
        "critical_error_count": compute_critical_error_count(data, target=overrides.get("critical_error_count")),
        "average_stock_level": compute_average_stock_level(data, target=overrides.get("average_stock_level")),
        "storage_occupation_rate": compute_storage_occupation_rate(data, target=overrides.get("storage_occupation_rate")),
        "wip_occupation_rate": compute_wip_occupation_rate(data, target=overrides.get("wip_occupation_rate")),
        "global_lead_time": compute_global_lead_time(data, target=overrides.get("global_lead_time")),
        "otd": compute_otd(data, target=overrides.get("otd")),
        "energy_per_unit": compute_energy_per_unit(data, target=overrides.get("energy_per_unit")),
        "air_per_unit": compute_air_per_unit(data, target=overrides.get("air_per_unit")),
    }
    return results
