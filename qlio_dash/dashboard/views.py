from __future__ import annotations

import logging
import math
from datetime import date, datetime, timedelta, timezone

from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

try:
    import pandas as pd
except Exception:  # pragma: no cover - optional for UI-only startup
    pd = None  # type: ignore[assignment]

_api_runtime_import_error = None
try:
    from dash_app import config as dash_config
    from dash_app import data_access, kpis
    from . import warehouse_metrics
except Exception as exc:  # pragma: no cover - optional for UI-only startup
    dash_config = None  # type: ignore[assignment]
    data_access = None  # type: ignore[assignment]
    kpis = None  # type: ignore[assignment]
    warehouse_metrics = None  # type: ignore[assignment]
    _api_runtime_import_error = exc

logger = logging.getLogger(__name__)


@login_required
def index(request):
    return render(request, "dashboard/index.html")


def _compute_status(kpi: dict | None) -> str:
    if not kpi or kpi.get("value") is None:
        return "unknown"
    ratio = kpi.get("ratio")
    if ratio is None:
        return "unknown"
    if ratio >= 1:
        return "success"
    if ratio >= 0.8:
        return "warning"
    return "danger"


def _request_filters(request) -> dict[str, str]:
    def _get(name: str, default: str = "all") -> str:
        value = (request.GET.get(name) or "").strip()
        return value or default

    return {
        "temporal": _get("temporal", "all-time"),
        "shift": _get("shift", "all"),
        "machine": _get("machine", "all"),
        "product": _get("product", "all"),
        "of": _get("of", "all"),
        "error_type": _get("error_type", "all"),
    }


def _alias_kpis(results: dict[str, dict]) -> dict[str, dict]:
    aliases = {
        "total_errors": "error_count",
        "critical_errors": "critical_error_count",
        "avg_stock_level": "average_stock_level",
        "storage_occupancy": "storage_occupation_rate",
        "wip_occupancy": "wip_occupation_rate",
        "lead_time": "global_lead_time",
    }
    merged = dict(results)
    for alias, key in aliases.items():
        if key in results:
            merged[alias] = results[key]
    return merged


def _build_overview(results: dict[str, dict]) -> dict[str, dict]:
    overview_map = {
        "performance": "machine_utilization",
        "quality": "non_conformity_rate",
        "stock": "storage_occupation_rate",
        "delay": "global_lead_time",
        "energy": "energy_per_unit",
        "maintenance": "critical_error_count",
    }
    payload: dict[str, dict] = {}
    for section, kpi_key in overview_map.items():
        item = results.get(kpi_key)
        payload[section] = {
            "kpi_key": kpi_key,
            "status": _compute_status(item),
            "data": item,
        }
    return payload


def _build_sections(results: dict[str, dict]) -> dict[str, dict]:
    return {
        "overview": _build_overview(results),
        "performance": {
            "machine_utilization": results.get("machine_utilization"),
            "trs": results.get("trs"),
            "cycle_time": results.get("cycle_time"),
            "operation_execution_rate": results.get("operation_execution_rate"),
        },
        "quality": {
            "non_conformity_rate": results.get("non_conformity_rate"),
            "error_count": results.get("error_count"),
            "critical_error_count": results.get("critical_error_count"),
        },
        "stock": {
            "average_stock_level": results.get("average_stock_level"),
            "storage_occupation_rate": results.get("storage_occupation_rate"),
            "wip_occupation_rate": results.get("wip_occupation_rate"),
        },
        "delay": {
            "global_lead_time": results.get("global_lead_time"),
            "otd": results.get("otd"),
        },
        "energy": {
            "energy_per_unit": results.get("energy_per_unit"),
            "air_per_unit": results.get("air_per_unit"),
        },
        "maintenance": {
            "critical_error_count": results.get("critical_error_count"),
            "error_count": results.get("error_count"),
        },
    }


def _safe_datetime(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if df.empty or col not in df.columns:
        return df
    out = df.copy()
    out[col] = pd.to_datetime(out[col], errors="coerce")
    return out.dropna(subset=[col])


def _day_str(ts) -> str:
    try:
        return pd.Timestamp(ts).strftime("%d/%m")
    except Exception:
        return str(ts)


def _resource_name_map(resources: pd.DataFrame) -> dict[int, str]:
    if resources.empty or "ResourceID" not in resources.columns:
        return {}
    df = resources.copy()
    name_col = "ResourceName" if "ResourceName" in df.columns else None
    if not name_col and "Description" in df.columns:
        name_col = "Description"
    if not name_col:
        return {}
    df = df.dropna(subset=["ResourceID"])
    mapping: dict[int, str] = {}
    for _, row in df.iterrows():
        try:
            rid = int(row["ResourceID"])
        except Exception:
            continue
        label = str(row.get(name_col) or row.get("Description") or f"R{rid}")
        mapping[rid] = label
    return mapping


def _num_series(df: pd.DataFrame, col: str, default: float = 0) -> pd.Series:
    if col not in df.columns:
        return pd.Series([default] * len(df), index=df.index, dtype="float64")
    return pd.to_numeric(df[col], errors="coerce").fillna(default)


def _performance_details(detail_data: dict[str, pd.DataFrame]) -> dict:
    parts = _safe_datetime(detail_data.get("parts_report", pd.DataFrame()), "TimeStamp")
    machine = _safe_datetime(detail_data.get("machine_report", pd.DataFrame()), "TimeStamp")
    trs_evolution: list[dict] = []
    cycle_evolution: list[dict] = []

    part_days = set(parts["TimeStamp"].dt.date) if not parts.empty else set()
    machine_days = set(machine["TimeStamp"].dt.date) if not machine.empty else set()
    for day in sorted(part_days | machine_days)[-7:]:
        p_day = parts[parts["TimeStamp"].dt.date == day] if not parts.empty else pd.DataFrame()
        m_day = machine[machine["TimeStamp"].dt.date == day] if not machine.empty else pd.DataFrame()
        trs = kpis.compute_trs({"parts_report": p_day, "machine_report": m_day}).get("value")
        cycle = kpis.compute_cycle_time({"parts_report": p_day}).get("value")
        trs_evolution.append({"day": pd.Timestamp(day).strftime("%a"), "date": _day_str(day), "trs": trs or 0})
        cycle_evolution.append({"day": pd.Timestamp(day).strftime("%a"), "date": _day_str(day), "value": cycle or 0})

    return {
        "trs_evolution": trs_evolution,
        "cycle_time_evolution": cycle_evolution,
    }


def _quality_details(detail_data: dict[str, pd.DataFrame]) -> dict:
    parts = _safe_datetime(detail_data.get("parts_report", pd.DataFrame()), "TimeStamp")
    machine = _safe_datetime(detail_data.get("machine_report", pd.DataFrame()), "TimeStamp")
    resources = detail_data.get("resources", pd.DataFrame())
    resource_names = _resource_name_map(resources)

    non_conf_evolution: list[dict] = []
    if not parts.empty and "ErrorID" in parts.columns:
        tmp = parts.copy()
        tmp["day"] = tmp["TimeStamp"].dt.date
        tmp["non_conf"] = (tmp["ErrorID"].fillna(0) > 0).astype(int)
        agg = tmp.groupby("day")["non_conf"].mean().mul(100).reset_index()
        non_conf_evolution = [
            {"day": pd.Timestamp(row["day"]).strftime("%a"), "date": _day_str(row["day"]), "taux": round(float(row["non_conf"]), 2)}
            for _, row in agg.tail(7).iterrows()
        ]

    errors_by_machine: list[dict] = []
    if not parts.empty and {"ResourceID", "ErrorID"}.issubset(parts.columns):
        tmp = parts.copy()
        tmp = tmp[tmp["ErrorID"].fillna(0) > 0]
        if not tmp.empty:
            agg = tmp.groupby("ResourceID").size().reset_index(name="errors").sort_values("errors", ascending=False).head(8)
            errors_by_machine = [
                {
                    "machine": resource_names.get(int(row["ResourceID"]), f"R{int(row['ResourceID'])}"),
                    "errors": int(row["errors"]),
                }
                for _, row in agg.iterrows()
            ]

    critical_errors: list[dict] = []
    if not machine.empty and "ErrorL2" in machine.columns:
        crit = machine[machine["ErrorL2"].fillna(0) > 0].copy()
        if not crit.empty:
            crit["machine"] = crit["ResourceID"].apply(
                lambda rid: resource_names.get(int(rid), f"R{int(rid)}") if pd.notna(rid) else "Machine"
            ) if "ResourceID" in crit.columns else "Machine"
            crit = crit.sort_values("TimeStamp", ascending=False).head(10)
            critical_errors = [
                {
                    "date": pd.Timestamp(row["TimeStamp"]).strftime("%d/%m %H:%M"),
                    "machine": row.get("machine", "Machine"),
                    "cause": "Erreur critique L2",
                }
                for _, row in crit.iterrows()
            ]

    return {
        "non_conformity_evolution": non_conf_evolution,
        "errors_by_machine": errors_by_machine,
        "critical_errors": critical_errors,
    }


def _stock_details(detail_data: dict[str, pd.DataFrame]) -> dict:
    buf = detail_data.get("buffer_positions", pd.DataFrame())
    stock_evolution: list[dict] = []
    zone_occupancy: list[dict] = []
    if not buf.empty:
        if "TimeStamp" in buf.columns:
            tmp = _safe_datetime(buf, "TimeStamp")
            if not tmp.empty:
                tmp["day"] = tmp["TimeStamp"].dt.date
                qty = _num_series(tmp, "Quantity")
                cap = _num_series(tmp, "QuantityMax")
                tmp["qty"] = qty
                tmp["cap"] = cap
                grp = tmp.groupby("day").agg(qty=("qty", "sum"), cap=("cap", "sum")).reset_index()
                grp["value"] = grp.apply(
                    lambda r: (r["qty"] / r["cap"] * 100) if r["cap"] and r["cap"] > 0 else 0,
                    axis=1,
                )
                stock_evolution = [
                    {"date": _day_str(row["day"]), "value": round(float(row["value"]), 2)}
                    for _, row in grp.tail(7).iterrows()
                ]

        if "Zone" in buf.columns:
            tmp = buf.copy()
            tmp["Zone"] = pd.to_numeric(tmp["Zone"], errors="coerce").fillna(-1).astype(int)
            tmp["Quantity"] = _num_series(tmp, "Quantity")
            tmp["QuantityMax"] = _num_series(tmp, "QuantityMax")
            tmp = tmp[tmp["Zone"] >= 0]
            if not tmp.empty:
                rows = []
                for zone, zdf in tmp.groupby("Zone"):
                    cap = float(zdf.loc[zdf["QuantityMax"] > 0, "QuantityMax"].sum())
                    qty = float(zdf["Quantity"].sum())
                    storage_pct = (qty / cap * 100) if cap > 0 else float((zdf["Quantity"] > 0).mean() * 100)
                    wip_pct = float((zdf["Quantity"] > 0).mean() * 100)
                    rows.append({"zone": f"Zone {zone}", "stockage": round(storage_pct, 2), "encours": round(wip_pct, 2)})
                zone_occupancy = sorted(rows, key=lambda r: r["zone"])[:10]

    return {
        "stock_evolution": stock_evolution,
        "zone_occupancy": zone_occupancy,
    }


def _delay_details(detail_data: dict[str, pd.DataFrame]) -> dict:
    finorders = detail_data.get("finorders", pd.DataFrame())
    otd_evolution: list[dict] = []
    lead_time_by_product: list[dict] = []
    if not finorders.empty:
        df = finorders.copy()
        for col in ["End", "PlannedEnd", "Start"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        ended = df.dropna(subset=["End"]) if "End" in df.columns else pd.DataFrame()
        if not ended.empty and "PlannedEnd" in ended.columns:
            tmp = ended.dropna(subset=["PlannedEnd"]).copy()
            if not tmp.empty:
                tmp["day"] = tmp["End"].dt.date
                tmp["on_time"] = (tmp["End"] <= tmp["PlannedEnd"]).astype(int)
                agg = tmp.groupby("day")["on_time"].mean().mul(100).reset_index()
                otd_evolution = [
                    {"day": pd.Timestamp(row["day"]).strftime("%a"), "date": _day_str(row["day"]), "value": round(float(row["on_time"]), 2)}
                    for _, row in agg.tail(7).iterrows()
                ]

        if not ended.empty and "Start" in ended.columns:
            tmp = ended.dropna(subset=["Start"]).copy()
            if not tmp.empty:
                tmp["lead_hours"] = (tmp["End"] - tmp["Start"]).dt.total_seconds() / 3600
                tmp = tmp.dropna(subset=["lead_hours"]).sort_values("End", ascending=False).head(8)
                lead_time_by_product = [
                    {
                        "product": f"OF-{int(row['ONo'])}" if "ONo" in tmp.columns and pd.notna(row["ONo"]) else "Ordre",
                        "leadTime": round(float(row["lead_hours"]), 2),
                    }
                    for _, row in tmp.iloc[::-1].iterrows()
                ]

    return {
        "otd_evolution": otd_evolution,
        "lead_time_by_product": lead_time_by_product,
    }


def _energy_details(detail_data: dict[str, pd.DataFrame]) -> dict:
    finstep = detail_data.get("finstep", pd.DataFrame())
    parts = detail_data.get("parts_report", pd.DataFrame())
    energy_evolution: list[dict] = []
    combined: list[dict] = []
    if not finstep.empty and not parts.empty:
        f = _safe_datetime(finstep, "End")
        p = _safe_datetime(parts, "TimeStamp")
        if not f.empty and not p.empty:
            f["day"] = f["End"].dt.date
            p["day"] = p["TimeStamp"].dt.date
            part_counts = p.groupby("day").size().reset_index(name="produced")

            f["energy"] = _num_series(f, "ElectricEnergyReal")
            if (f["energy"] == 0).all():
                f["energy"] = _num_series(f, "ElectricEnergyCalc")
            f["air"] = _num_series(f, "CompressedAirReal")
            if (f["air"] == 0).all():
                f["air"] = _num_series(f, "CompressedAirCalc")

            agg = f.groupby("day").agg(energy=("energy", "sum"), air=("air", "sum")).reset_index()
            merged = agg.merge(part_counts, on="day", how="left").fillna({"produced": 0})
            merged = merged[merged["produced"] > 0]
            if not merged.empty:
                merged["kwh"] = (merged["energy"] / merged["produced"]) / 1000
                merged["air_unit"] = merged["air"] / merged["produced"]
                merged = merged.tail(7)
                energy_evolution = [
                    {"date": _day_str(row["day"]), "kwh": round(float(row["kwh"]), 3)}
                    for _, row in merged.iterrows()
                ]
                combined = [
                    {"date": _day_str(row["day"]), "kwh": round(float(row["kwh"]), 3), "air": round(float(row["air_unit"]), 2)}
                    for _, row in merged.iterrows()
                ]

    return {
        "energy_evolution": energy_evolution,
        "combined": combined,
    }


def _maintenance_details(detail_data: dict[str, pd.DataFrame]) -> dict:
    machine = _safe_datetime(detail_data.get("machine_report", pd.DataFrame()), "TimeStamp")
    error_evolution: list[dict] = []
    stop_time_evolution: list[dict] = []
    total_stop_time_minutes: float | None = None
    if not machine.empty:
        tmp = machine.copy()
        for col in ["ErrorL0", "ErrorL1", "ErrorL2", "Busy"]:
            if col in tmp.columns:
                tmp[col] = pd.to_numeric(tmp[col], errors="coerce").fillna(0)
        tmp["day"] = tmp["TimeStamp"].dt.date
        e0 = _num_series(tmp, "ErrorL0")
        e1 = _num_series(tmp, "ErrorL1")
        e2 = _num_series(tmp, "ErrorL2")
        tmp["critiques"] = (e2 > 0).astype(int)
        tmp["total"] = (
            (e0 > 0).astype(int)
            + (e1 > 0).astype(int)
            + (e2 > 0).astype(int)
        )
        agg = tmp.groupby("day").agg(critiques=("critiques", "sum"), total=("total", "sum")).reset_index()
        error_evolution = [
            {
                "day": pd.Timestamp(row["day"]).strftime("%a"),
                "date": _day_str(row["day"]),
                "critiques": int(row["critiques"]),
                "total": int(row["total"]),
            }
            for _, row in agg.tail(7).iterrows()
        ]

        if "ResourceID" in tmp.columns:
            tmp = tmp.sort_values(["ResourceID", "TimeStamp"]).copy()
            tmp["next_ts"] = tmp.groupby("ResourceID")["TimeStamp"].shift(-1)
            tmp["delta_min"] = (tmp["next_ts"] - tmp["TimeStamp"]).dt.total_seconds() / 60
            tmp["delta_min"] = tmp["delta_min"].clip(lower=0, upper=5).fillna(0)
            tmp["is_error_stop"] = (tmp["Busy"] <= 0) & ((e0 > 0) | (e1 > 0) | (e2 > 0))
            stop = tmp[tmp["is_error_stop"]].copy()
            if not stop.empty:
                agg_stop = stop.groupby("day")["delta_min"].sum().reset_index()
                stop_time_evolution = [
                    {
                        "day": pd.Timestamp(row["day"]).strftime("%a"),
                        "date": _day_str(row["day"]),
                        "minutes": round(float(row["delta_min"]), 1),
                    }
                    for _, row in agg_stop.tail(7).iterrows()
                ]
                total_stop_time_minutes = round(float(agg_stop.tail(7)["delta_min"].sum()), 1)

    return {
        "error_evolution": error_evolution,
        "stop_time_evolution": stop_time_evolution,
        "total_stop_time_minutes": total_stop_time_minutes,
    }


def _build_details(detail_data: dict[str, pd.DataFrame]) -> dict:
    return {
        "performance": _performance_details(detail_data),
        "quality": _quality_details(detail_data),
        "stock": _stock_details(detail_data),
        "delay": _delay_details(detail_data),
        "energy": _energy_details(detail_data),
        "maintenance": _maintenance_details(detail_data),
    }


def _json_safe(value):
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if hasattr(value, "item"):
        try:
            value = value.item()
        except Exception:
            pass
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _apply_energy_csv_fallback_mes_raw(
    results: dict[str, dict],
    details: dict,
    detail_data: dict[str, pd.DataFrame],
    filters: dict[str, str],
) -> None:
    if warehouse_metrics is None:
        return
    if not hasattr(warehouse_metrics, "_energy_from_csv"):
        return

    try:
        if hasattr(warehouse_metrics, "_energy_missing"):
            if not warehouse_metrics._energy_missing(results, details):
                return

        produced_count = 0.0
        parts = detail_data.get("parts_report", pd.DataFrame())
        if not parts.empty:
            produced_count = float(len(parts.index))

        if produced_count <= 0:
            finstep = detail_data.get("finstep", pd.DataFrame())
            if not finstep.empty:
                produced_count = float(len(finstep.index))

        since = date.today() - timedelta(days=6)
        until = date.today()
        if not parts.empty and "TimeStamp" in parts.columns:
            ts = pd.to_datetime(parts["TimeStamp"], errors="coerce").dropna()
            if not ts.empty:
                since = ts.dt.date.min()
                until = ts.dt.date.max()

        csv_energy = warehouse_metrics._energy_from_csv(
            produced_count=produced_count,
            since=since,
            until=until,
            points=7,
        )
        if not csv_energy:
            return

        for key, csv_value in (
            ("energy_per_unit", csv_energy.get("energy_per_unit")),
            ("air_per_unit", csv_energy.get("air_per_unit")),
        ):
            item = dict(results.get(key) or {})
            target = item.get("target")
            better_when = item.get("better_when", "lower")
            value = None if csv_value is None else float(csv_value)
            ratio = None
            if value is not None and target not in (None, 0):
                if better_when == "lower":
                    ratio = (target / value) if value else 0
                else:
                    ratio = value / target
            item["value"] = value
            item["ratio"] = ratio
            if kpis is not None:
                item["color"] = kpis.compute_color(value, target, better_when)
            results[key] = item

        details.setdefault("energy", {})
        details["energy"]["energy_evolution"] = csv_energy.get("energy_evolution", [])
        details["energy"]["combined"] = csv_energy.get("combined", [])
    except Exception:
        logger.exception("Unable to apply CSV energy fallback on mes_raw payload")


@require_GET
def summary_api(request):
    try:
        request_filters = _request_filters(request)
        if not request.user.is_authenticated:
            return JsonResponse(
                {
                    "error": "auth_required",
                    "login_url": settings.FRONTEND_LOGIN_URL,
                },
                status=401,
            )

        if _api_runtime_import_error is not None or pd is None:
            return JsonResponse(
                {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "window_minutes": 0,
                    "kpis": {},
                    "sections": {
                        "overview": {},
                        "performance": {},
                        "quality": {},
                        "stock": {},
                        "delay": {},
                        "energy": {},
                        "maintenance": {},
                    },
                    "details": {
                        "performance": {"trs_evolution": [], "cycle_time_evolution": []},
                        "quality": {"non_conformity_evolution": [], "errors_by_machine": [], "critical_errors": []},
                        "stock": {"stock_evolution": [], "zone_occupancy": []},
                        "delay": {"otd_evolution": [], "lead_time_by_product": []},
                        "energy": {"energy_evolution": [], "combined": []},
                        "maintenance": {"error_evolution": [], "stop_time_evolution": [], "total_stop_time_minutes": None},
                    },
                    "data_source": "unavailable",
                    "warning": f"API runtime dependencies unavailable: {_api_runtime_import_error}",
                }
            )

        warehouse_payload = warehouse_metrics.build_telephan_payload(detail_days=31, filters=request_filters)
        if warehouse_payload:
            aliased_results = _alias_kpis(warehouse_payload["results"])
            return JsonResponse(
                {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "window_minutes": int(dash_config.SHIFT_WINDOW.total_seconds() // 60),
                    "kpis": _json_safe(aliased_results),
                    "sections": _json_safe(_build_sections(aliased_results)),
                    "details": _json_safe(warehouse_payload["details"]),
                    "filter_options": _json_safe(warehouse_payload.get("filter_options", {})),
                    "data_source": warehouse_payload.get("source"),
                    "anchor_date": warehouse_payload.get("anchor_date"),
                    "time_reference_date": warehouse_payload.get("time_reference_date"),
                    "data_is_stale": warehouse_payload.get("data_is_stale"),
                }
            )

        detail_window = timedelta(days=7)
        data = {
            "parts_report": data_access.fetch_parts_report(dash_config.SHIFT_WINDOW),
            "machine_report": data_access.fetch_machine_report(dash_config.SHIFT_WINDOW),
            "finorders": data_access.fetch_finorders(),
            "finstep": data_access.fetch_finstep(dash_config.SHIFT_WINDOW),
            "buffer_positions": data_access.fetch_buffer_positions(),
        }
        detail_data = {
            "parts_report": data_access.fetch_parts_report(detail_window),
            "machine_report": data_access.fetch_machine_report(detail_window),
            "finorders": data_access.fetch_finorders(),
            "finstep": data_access.fetch_finstep(detail_window),
            "buffer_positions": data_access.fetch_buffer_positions(),
            "resources": data_access.fetch_resources(),
        }
        results = kpis.compute_all_kpis(data)
        details = _build_details(detail_data)
        aliased_results = _alias_kpis(results)
        _apply_energy_csv_fallback_mes_raw(aliased_results, details, detail_data, request_filters)
        return JsonResponse(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "window_minutes": int(dash_config.SHIFT_WINDOW.total_seconds() // 60),
                "kpis": _json_safe(aliased_results),
                "sections": _json_safe(_build_sections(aliased_results)),
                "details": _json_safe(details),
                "filter_options": {},
                "data_source": "mes_raw",
            }
        )
    except Exception as exc:  # pragma: no cover - defensive API response
        logger.exception("Unable to build dashboard summary")
        return JsonResponse({"error": "dashboard_summary_unavailable", "detail": str(exc)}, status=503)
