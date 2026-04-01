from __future__ import annotations

import os
from io import StringIO
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

from dash_app import config as dash_config
from dash_app import data_access, kpis


_ENERGY_CSV_CACHE: dict[str, object] = {"path": None, "mtime": None, "data": None}


def _sql_schema() -> str:
    return dash_config.DWH_SCHEMA


def _weekday_fr(value) -> str:
    names = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    try:
        return names[pd.Timestamp(value).weekday()]
    except Exception:
        return str(value)


def _day_str(value) -> str:
    try:
        return pd.Timestamp(value).strftime("%d/%m")
    except Exception:
        return str(value)


def _to_date(value) -> Optional[date]:
    if value is None:
        return None
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return None
    return ts.date()


def _table_exists(schema: str, table: str) -> bool:
    q = """
        SELECT COUNT(*) AS cnt
        FROM information_schema.tables
        WHERE table_schema = %(schema)s AND table_name = %(table)s
    """
    df = data_access.run_sql(q, {"schema": schema, "table": table})
    if df.empty:
        return False
    try:
        return int(df.iloc[0]["cnt"]) > 0
    except Exception:
        return False


def _warehouse_ready(schema: str) -> bool:
    required = [
        "dim_time",
        "fact_machine_state",
        "fact_step_execution",
        "fact_stock_snapshot",
        "fact_order_delivery",
    ]
    return all(_table_exists(schema, t) for t in required)


def _anchor_date(schema: str) -> Optional[date]:
    q = f"SELECT MAX(date) AS max_date FROM {schema}.dim_time"
    df = data_access.run_sql(q)
    if df.empty:
        return None
    return _to_date(df.iloc[0].get("max_date"))


def _min_date(schema: str) -> Optional[date]:
    q = f"SELECT MIN(date) AS min_date FROM {schema}.dim_time"
    df = data_access.run_sql(q)
    if df.empty:
        return None
    return _to_date(df.iloc[0].get("min_date"))


def _time_reference_date(data_anchor: date) -> date:
    mode = str(getattr(dash_config, "TIME_REFERENCE_MODE", "system") or "system").lower()
    if mode == "data_anchor":
        return data_anchor
    return date.today()


def _fetch_machine_state(schema: str, since: date, until: date) -> pd.DataFrame:
    q = f"""
        SELECT
          t.date, t.hour,
          m.machine_id, m.mes_resource_id, m.name AS machine_name,
          ms.busy_seconds, ms.available_seconds, ms.error_seconds
        FROM {schema}.fact_machine_state ms
        JOIN {schema}.dim_time t ON t.time_id = ms.time_id
        JOIN {schema}.dim_machine m ON m.machine_id = ms.machine_id
        WHERE t.date BETWEEN %(since)s AND %(until)s
    """
    return data_access.run_sql(q, {"since": since, "until": until})


def _fetch_step_execution(schema: str, since: date, until: date) -> pd.DataFrame:
    q = f"""
        SELECT
          t.date, t.hour,
          f.machine_id, m.name AS machine_name,
          f.product_id, p.mes_pno, p.name AS product_name,
          f.order_id, o.mes_ono,
          f.cycle_time_seconds,
          f.quantity_input, f.quantity_output_ok, f.quantity_output_nok,
          f.energy_mws, f.air_mnl
        FROM {schema}.fact_step_execution f
        JOIN {schema}.dim_time t ON t.time_id = f.time_id
        JOIN {schema}.dim_machine m ON m.machine_id = f.machine_id
        LEFT JOIN {schema}.dim_product p ON p.product_id = f.product_id
        LEFT JOIN {schema}.dim_order o ON o.order_id = f.order_id
        WHERE t.date BETWEEN %(since)s AND %(until)s
    """
    return data_access.run_sql(q, {"since": since, "until": until})


def _fetch_quality_events(schema: str, since: date, until: date) -> pd.DataFrame:
    q = f"""
        SELECT
          t.date, t.hour,
          qe.machine_id, m.name AS machine_name,
          qe.product_id, p.mes_pno, p.name AS product_name,
          qe.order_id, o.mes_ono,
          qe.piece_count, qe.is_critical,
          de.code AS error_code, de.description AS error_description, de.severity
        FROM {schema}.fact_quality_event qe
        JOIN {schema}.dim_time t ON t.time_id = qe.time_id
        LEFT JOIN {schema}.dim_machine m ON m.machine_id = qe.machine_id
        LEFT JOIN {schema}.dim_product p ON p.product_id = qe.product_id
        LEFT JOIN {schema}.dim_order o ON o.order_id = qe.order_id
        LEFT JOIN {schema}.dim_error de ON de.error_id = qe.error_id
        WHERE t.date BETWEEN %(since)s AND %(until)s
    """
    return data_access.run_sql(q, {"since": since, "until": until})


def _fetch_stock_snapshot(schema: str, since: date, until: date) -> pd.DataFrame:
    q = f"""
        SELECT
          t.date, t.hour,
          b.buffer_id, b.mes_resource_id, b.mes_bufno, b.buffer_type,
          b.capacity_positions, b.area,
          s.product_id, p.mes_pno, p.name AS product_name,
          s.quantity, s.positions_used
        FROM {schema}.fact_stock_snapshot s
        JOIN {schema}.dim_time t ON t.time_id = s.time_id
        JOIN {schema}.dim_buffer b ON b.buffer_id = s.buffer_id
        LEFT JOIN {schema}.dim_product p ON p.product_id = s.product_id
        WHERE t.date BETWEEN %(since)s AND %(until)s
    """
    return data_access.run_sql(q, {"since": since, "until": until})


def _fetch_order_delivery(schema: str, since: date, until: date) -> pd.DataFrame:
    q = f"""
        SELECT
          te.date AS end_date,
          te.hour AS end_hour,
          ts.date AS start_date,
          ts.hour AS start_hour,
          tpe.date AS planned_end_date,
          tpe.hour AS planned_end_hour,
          od.order_id,
          o.mes_ono,
          p.mes_pno,
          p.name AS product_name,
          od.real_lead_time_seconds,
          od.planned_lead_time_seconds,
          od.delivered_on_time
        FROM {schema}.fact_order_delivery od
        JOIN {schema}.dim_time te ON te.time_id = od.time_end_id
        JOIN {schema}.dim_time ts ON ts.time_id = od.time_start_id
        LEFT JOIN {schema}.dim_time tpe ON tpe.time_id = od.time_planned_end_id
        LEFT JOIN {schema}.dim_order o ON o.order_id = od.order_id
        LEFT JOIN {schema}.dim_product p ON p.product_id = od.product_id
        WHERE te.date BETWEEN %(since)s AND %(until)s
    """
    return data_access.run_sql(q, {"since": since, "until": until})


def _num(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series([0] * len(df), index=df.index, dtype="float64")
    return pd.to_numeric(df[col], errors="coerce").fillna(0)


def _energy_csv_file() -> Optional[Path]:
    candidates: list[Path] = []
    env_path = os.environ.get("ENERGY_CSV_PATH")
    if env_path:
        candidates.append(Path(env_path))

    root = Path(__file__).resolve().parents[2]
    candidates.extend(
        [
            root / "dataEnergy.csv",
            root / "data" / "dataEnergy.csv",
        ]
    )

    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _load_energy_csv() -> pd.DataFrame:
    csv_path = _energy_csv_file()
    if csv_path is None:
        return pd.DataFrame()

    mtime = csv_path.stat().st_mtime
    if (
        _ENERGY_CSV_CACHE["path"] == str(csv_path)
        and _ENERGY_CSV_CACHE["mtime"] == mtime
        and isinstance(_ENERGY_CSV_CACHE["data"], pd.DataFrame)
    ):
        return _ENERGY_CSV_CACHE["data"]  # type: ignore[return-value]

    raw_text = csv_path.read_text(encoding="utf-8", errors="ignore").replace("\x00", "")
    frame = pd.read_csv(StringIO(raw_text), sep=";", engine="python")
    frame.columns = [str(c).strip() for c in frame.columns]
    frame = frame[[c for c in frame.columns if not c.startswith("Unnamed")]]
    if frame.empty:
        return pd.DataFrame()

    lookup = {c.lower(): c for c in frame.columns}
    time_col = next((c for c in frame.columns if c.lower().startswith("time")), None)
    flow_col = next((c for c in frame.columns if "flow rate" in c.lower()), None)
    power_cols = [lookup[k] for k in lookup if "active power" in k]
    if time_col is None or not power_cols:
        return pd.DataFrame()

    out = pd.DataFrame()
    out["time_s"] = pd.to_numeric(frame[time_col], errors="coerce")
    out["flow_l_min"] = pd.to_numeric(frame[flow_col], errors="coerce").fillna(0) if flow_col else 0
    out["power_w"] = (
        frame[power_cols]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0)
        .sum(axis=1)
    )
    out = out.dropna(subset=["time_s"]).sort_values("time_s").reset_index(drop=True)
    out = out[out["time_s"].diff().fillna(1) >= 0].copy()

    _ENERGY_CSV_CACHE["path"] = str(csv_path)
    _ENERGY_CSV_CACHE["mtime"] = mtime
    _ENERGY_CSV_CACHE["data"] = out
    return out


def _integrate_energy_air(samples: pd.DataFrame) -> tuple[float, float]:
    if samples.empty:
        return 0.0, 0.0
    tmp = samples.sort_values("time_s").copy()
    dt = tmp["time_s"].shift(-1) - tmp["time_s"]
    positive_dt = dt[dt > 0]
    default_dt = float(positive_dt.median()) if not positive_dt.empty else 1.0
    max_dt = max(default_dt * 10, 1.0)
    dt = dt.fillna(default_dt).clip(lower=0, upper=max_dt)

    energy_kwh = float((tmp["power_w"] * dt).sum() / 3_600_000)
    air_l = float((tmp["flow_l_min"] * dt).sum() / 60)
    return energy_kwh, air_l


def _energy_from_csv(
    produced_count: float,
    since: date,
    until: date,
    points: int = 7,
) -> Optional[dict]:
    samples = _load_energy_csv()
    if samples.empty:
        return None

    n_points = max(1, min(points, len(samples)))
    total_energy_kwh, total_air_l = _integrate_energy_air(samples)
    duration_s = max(float(samples["time_s"].max() - samples["time_s"].min()), 1.0)
    duration_h = duration_s / 3600
    duration_min = duration_s / 60

    per_unit_denom = produced_count if produced_count > 0 else None
    per_piece_energy = (total_energy_kwh / per_unit_denom) if per_unit_denom else None
    per_piece_air = (total_air_l / per_unit_denom) if per_unit_denom else None

    # If the computed per-piece values are too tiny to be readable, switch to a rate
    # representation derived only from the energy CSV (still real measurements).
    use_rate_mode = (
        per_piece_energy is None
        or per_piece_energy < 1e-3
    )
    if use_rate_mode:
        energy_per_unit = total_energy_kwh / duration_h  # ~kW average
        air_per_unit = total_air_l / duration_min  # L/min average
    else:
        energy_per_unit = per_piece_energy
        air_per_unit = per_piece_air

    total_days = max((until - since).days, 0)
    labels = [since + timedelta(days=round(i * total_days / max(n_points - 1, 1))) for i in range(n_points)]
    energy_evolution: list[dict] = []
    combined: list[dict] = []

    n_rows = len(samples)
    for idx in range(n_points):
        start_i = int(idx * n_rows / n_points)
        end_i = int((idx + 1) * n_rows / n_points)
        chunk = samples.iloc[start_i:end_i]
        chunk_energy_kwh, chunk_air_l = _integrate_energy_air(chunk)
        if use_rate_mode:
            if len(chunk) > 1:
                chunk_duration_s = max(float(chunk["time_s"].iloc[-1] - chunk["time_s"].iloc[0]), 1.0)
            else:
                chunk_duration_s = max(duration_s / n_points, 1.0)
            chunk_energy = chunk_energy_kwh / (chunk_duration_s / 3600)  # ~kW average
            chunk_air = chunk_air_l / (chunk_duration_s / 60)  # L/min average
        else:
            chunk_energy = (chunk_energy_kwh / per_unit_denom) if per_unit_denom else chunk_energy_kwh
            chunk_air = (chunk_air_l / per_unit_denom) if per_unit_denom else chunk_air_l
        label_date = labels[idx]
        energy_evolution.append(
            {
                "date": _day_str(label_date),
                "kwh": round(float(chunk_energy), 6),
            }
        )
        combined.append(
            {
                "date": _day_str(label_date),
                "kwh": round(float(chunk_energy), 6),
                "air": round(float(chunk_air), 4),
            }
        )

    return {
        "energy_per_unit": energy_per_unit,
        "air_per_unit": air_per_unit,
        "energy_evolution": energy_evolution,
        "combined": combined,
    }


def _is_global_energy_context(filters: Optional[dict]) -> bool:
    filters = filters or {}
    for key in ("machine", "product", "of", "error_type"):
        if str(filters.get(key, "all")).strip() not in ("", "all"):
            return False
    return True


def _energy_missing(results: dict[str, dict], details: dict) -> bool:
    energy_value = results.get("energy_per_unit", {}).get("value")
    air_value = results.get("air_per_unit", {}).get("value")
    return (
        (energy_value is None or float(energy_value) <= 0)
        and (air_value is None or float(air_value) <= 0)
    )


def _apply_energy_csv_fallback(
    results: dict[str, dict],
    details: dict,
    fse_summary: pd.DataFrame,
    since: date,
    until: date,
    filters: Optional[dict],
) -> None:
    if not _energy_missing(results, details):
        return

    produced_ok = _num(fse_summary, "quantity_output_ok").sum()
    produced_nok = _num(fse_summary, "quantity_output_nok").sum()
    produced_total = float(produced_ok + produced_nok)
    csv_energy = _energy_from_csv(
        produced_count=produced_total,
        since=since,
        until=until,
        points=7,
    )
    if not csv_energy:
        return

    results["energy_per_unit"] = _result("energy_per_unit", csv_energy["energy_per_unit"])
    results["air_per_unit"] = _result("air_per_unit", csv_energy["air_per_unit"])
    details.setdefault("energy", {})
    details["energy"]["energy_evolution"] = csv_energy["energy_evolution"]
    details["energy"]["combined"] = csv_energy["combined"]


def _normalize_dates(df: pd.DataFrame, *cols: str) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], errors="coerce").dt.date
    return out


def _target(key: str) -> Optional[float]:
    return dash_config.KPI_TARGETS.get(key, kpis.KPI_META.get(key, {}).get("target_default"))


def _result(key: str, value: Optional[float]) -> dict:
    meta = kpis.KPI_META[key]
    target = _target(key)
    better_when = meta["better_when"]
    ratio = None
    if value is not None and target not in (None, 0):
        if better_when == "higher":
            ratio = value / target if target else None
        else:
            ratio = (target / value) if value else 0
    rounded_value = None
    if value is not None:
        v = float(value)
        av = abs(v)
        if av < 0.001:
            rounded_value = round(v, 8)
        elif av < 0.01:
            rounded_value = round(v, 6)
        elif av < 1:
            rounded_value = round(v, 5)
        elif av < 100:
            rounded_value = round(v, 4)
        else:
            rounded_value = round(v, 2)
    return {
        "key": key,
        "label": meta["label"],
        "value": rounded_value,
        "unit": meta["unit"],
        "type": meta["value_type"],
        "format": meta["format"],
        "target": target,
        "better_when": better_when,
        "ratio": ratio,
        "color": kpis.compute_color(value, target, better_when),
    }


def _slice_since(df: pd.DataFrame, date_col: str, since: date) -> pd.DataFrame:
    if df.empty or date_col not in df.columns:
        return df
    out = _normalize_dates(df, date_col)
    return out[out[date_col] >= since].copy()


def _safe_div(n: float, d: float) -> Optional[float]:
    return (n / d) if d else None


def _shift_bucket(hour_value) -> Optional[str]:
    try:
        hour = int(hour_value)
    except Exception:
        return None
    if 6 <= hour <= 13:
        return "shift-a"
    if 14 <= hour <= 21:
        return "shift-b"
    return "shift-c"


def _shift_mask(df: pd.DataFrame, shift_value: str, hour_col: str) -> pd.Series:
    if df.empty or shift_value in ("", "all") or hour_col not in df.columns:
        return pd.Series([True] * len(df), index=df.index)
    return df[hour_col].apply(_shift_bucket).eq(shift_value)


def _norm_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def _temporal_bounds(anchor: date, temporal: Optional[str], default_days: int = 7, data_start: Optional[date] = None) -> tuple[date, date]:
    t = (temporal or "").strip()
    if t == "all-time":
        return (data_start or anchor), anchor
    if t == "today":
        return anchor, anchor
    if t == "yesterday":
        d = anchor - timedelta(days=1)
        return d, d
    if t == "this-week":
        return anchor - timedelta(days=anchor.weekday()), anchor
    if t == "last-week":
        end = anchor - timedelta(days=anchor.weekday() + 1)
        return end - timedelta(days=6), end
    if t == "this-month":
        return anchor.replace(day=1), anchor
    days = max(int(default_days or 7), 1)
    return anchor - timedelta(days=days - 1), anchor


def _apply_filters(
    ms: pd.DataFrame,
    fse: pd.DataFrame,
    fqe: pd.DataFrame,
    fss: pd.DataFrame,
    fod: pd.DataFrame,
    filters: Optional[dict] = None,
    *,
    include_dimension_filters: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    filters = filters or {}
    shift_value = _norm_text(filters.get("shift")) or "all"

    ms2 = _normalize_dates(ms, "date")
    fse2 = _normalize_dates(fse, "date")
    fqe2 = _normalize_dates(fqe, "date")
    fss2 = _normalize_dates(fss, "date")
    fod2 = _normalize_dates(fod, "end_date", "start_date", "planned_end_date")

    if not ms2.empty:
        ms2 = ms2[_shift_mask(ms2, shift_value, "hour")].copy()
    if not fse2.empty:
        fse2 = fse2[_shift_mask(fse2, shift_value, "hour")].copy()
    if not fqe2.empty:
        fqe2 = fqe2[_shift_mask(fqe2, shift_value, "hour")].copy()
    if not fss2.empty:
        fss2 = fss2[_shift_mask(fss2, shift_value, "hour")].copy()
    if not fod2.empty:
        fod2 = fod2[_shift_mask(fod2, shift_value, "end_hour")].copy()

    if not include_dimension_filters:
        return ms2, fse2, fqe2, fss2, fod2

    machine_value = _norm_text(filters.get("machine"))
    product_value = _norm_text(filters.get("product"))
    order_value = _norm_text(filters.get("of"))
    error_value = _norm_text(filters.get("error_type"))

    def _filter_machine(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or machine_value in ("", "all") or "machine_name" not in df.columns:
            return df
        return df[df["machine_name"].astype(str) == machine_value].copy()

    def _filter_product(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or product_value in ("", "all"):
            return df
        mask = pd.Series([False] * len(df), index=df.index)
        if "product_name" in df.columns:
            mask = mask | df["product_name"].astype(str).eq(product_value)
        if "mes_pno" in df.columns:
            mask = mask | df["mes_pno"].astype(str).eq(product_value)
        return df[mask].copy()

    def _filter_order(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or order_value in ("", "all") or "mes_ono" not in df.columns:
            return df
        return df[df["mes_ono"].astype(str) == order_value].copy()

    def _filter_error(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or error_value in ("", "all"):
            return df
        if error_value.startswith("severity:"):
            sev = error_value.split(":", 1)[1]
            if "severity" in df.columns:
                return df[df["severity"].astype(str) == sev].copy()
            return df
        if error_value.startswith("code:"):
            code = error_value.split(":", 1)[1]
            if "error_code" in df.columns:
                return df[df["error_code"].astype(str) == code].copy()
            return df
        if {"error_code", "error_description"} & set(df.columns):
            code_series = df["error_code"].astype(str) if "error_code" in df.columns else pd.Series("", index=df.index)
            desc_series = df["error_description"].astype(str) if "error_description" in df.columns else pd.Series("", index=df.index)
            return df[code_series.eq(error_value) | desc_series.eq(error_value)].copy()
        return df

    ms2 = _filter_machine(ms2)
    fse2 = _filter_order(_filter_product(_filter_machine(fse2)))
    fqe2 = _filter_error(_filter_order(_filter_product(_filter_machine(fqe2))))
    fss2 = _filter_product(fss2)
    fod2 = _filter_order(_filter_product(fod2))
    return ms2, fse2, fqe2, fss2, fod2


def _build_filter_options(ms: pd.DataFrame, fse: pd.DataFrame, fqe: pd.DataFrame, fss: pd.DataFrame, fod: pd.DataFrame) -> dict:
    machines = sorted({str(v) for v in pd.concat(
        [
            ms.get("machine_name", pd.Series(dtype="object")),
            fse.get("machine_name", pd.Series(dtype="object")),
            fqe.get("machine_name", pd.Series(dtype="object")),
        ],
        ignore_index=True,
    ).dropna() if _norm_text(v)})

    products = sorted({str(v) for v in pd.concat(
        [
            fse.get("product_name", pd.Series(dtype="object")),
            fss.get("product_name", pd.Series(dtype="object")),
            fod.get("product_name", pd.Series(dtype="object")),
        ],
        ignore_index=True,
    ).dropna() if _norm_text(v)})

    product_pnos = sorted({str(int(v)) for v in pd.concat(
        [
            fse.get("mes_pno", pd.Series(dtype="float64")),
            fss.get("mes_pno", pd.Series(dtype="float64")),
            fod.get("mes_pno", pd.Series(dtype="float64")),
        ],
        ignore_index=True,
    ).dropna() if str(v) not in {"0", "0.0"}})
    for pno in product_pnos:
        if pno not in products:
            products.append(pno)

    orders = sorted({str(int(v)) for v in pd.concat(
        [
            fse.get("mes_ono", pd.Series(dtype="float64")),
            fod.get("mes_ono", pd.Series(dtype="float64")),
        ],
        ignore_index=True,
    ).dropna()})

    error_types = [{"value": "all", "label": "Tous types"}]
    severities = [s for s in ["critical", "major", "minor"] if not fqe.empty and "severity" in fqe.columns and (fqe["severity"] == s).any()]
    severity_labels = {"critical": "Erreurs critiques", "major": "Erreurs majeures", "minor": "Erreurs mineures"}
    error_types.extend({"value": f"severity:{s}", "label": severity_labels[s]} for s in severities)
    if not fqe.empty and "error_code" in fqe.columns:
        codes = [c for c in sorted({_norm_text(c) for c in fqe["error_code"].dropna()}) if c]
        for code in codes[:20]:
            error_types.append({"value": f"code:{code}", "label": code})

    return {
        "machines": [{"value": "all", "label": "Toutes machines"}] + [{"value": m, "label": m} for m in machines],
        "products": [{"value": "all", "label": "Tous produits"}] + [{"value": p, "label": p} for p in products[:30]],
        "orders": [{"value": "all", "label": "Tous les OF"}] + [{"value": o, "label": f"OF-{o}"} for o in orders[:30]],
        "error_types": error_types,
    }


def _compute_summary(ms: pd.DataFrame, fse: pd.DataFrame, fqe: pd.DataFrame, fss: pd.DataFrame, fod: pd.DataFrame) -> dict[str, dict]:
    results: dict[str, dict] = {}

    ms = ms.copy()
    fse = fse.copy()
    fqe = fqe.copy()
    fss = fss.copy()
    fod = fod.copy()

    busy = _num(ms, "busy_seconds").sum()
    avail = _num(ms, "available_seconds").sum()
    machine_util = (_safe_div(busy, avail) * 100) if avail else None
    results["machine_utilization"] = _result("machine_utilization", machine_util)

    out_ok = _num(fse, "quantity_output_ok").sum()
    out_nok = _num(fse, "quantity_output_nok").sum()
    out_total = out_ok + out_nok
    in_total = _num(fse, "quantity_input").sum()
    quality = (out_ok / out_total) if out_total else None
    performance = (out_total / in_total) if in_total else None
    availability = (busy / avail) if avail else None
    trs = None
    if availability is not None and quality is not None:
        perf_factor = max(min(performance, 1.2), 0) if performance is not None else 1.0
        trs = availability * perf_factor * quality * 100
    results["trs"] = _result("trs", trs)

    cycle = _num(fse, "cycle_time_seconds")
    cycle = cycle[cycle > 0]
    results["cycle_time"] = _result("cycle_time", cycle.mean() if not cycle.empty else None)

    done_steps = _num(fse, "cycle_time_seconds")
    total_steps = len(fse)
    exec_rate = ((done_steps > 0).sum() / total_steps * 100) if total_steps else None
    results["operation_execution_rate"] = _result("operation_execution_rate", exec_rate)

    non_conf = (out_nok / out_total * 100) if out_total else None
    results["non_conformity_rate"] = _result("non_conformity_rate", non_conf)

    piece_count = _num(fqe, "piece_count")
    results["error_count"] = _result("error_count", float(piece_count.sum()) if not fqe.empty else 0.0)

    crit = _num(fqe, "is_critical")
    crit_count = (piece_count * (crit > 0).astype(int)).sum() if not fqe.empty else 0
    results["critical_error_count"] = _result("critical_error_count", float(crit_count))

    qty = _num(fss, "quantity")
    results["average_stock_level"] = _result("average_stock_level", qty.mean() if not fss.empty else None)

    pos_used = _num(fss, "positions_used").sum()
    cap = _num(fss, "capacity_positions").sum()
    storage_occ = (_safe_div(pos_used, cap) * 100) if cap else None
    results["storage_occupation_rate"] = _result("storage_occupation_rate", storage_occ)

    is_wip = (_num(fss, "buffer_type") != 1) if not fss.empty else pd.Series(dtype="bool")
    fss_wip = fss[is_wip] if not fss.empty and len(is_wip) == len(fss) else pd.DataFrame()
    if not fss_wip.empty:
        wip_occ = (_safe_div(_num(fss_wip, "positions_used").sum(), _num(fss_wip, "capacity_positions").sum()) * 100)
        if wip_occ is None:
            wip_occ = float((_num(fss_wip, "positions_used") > 0).mean() * 100)
    else:
        wip_occ = storage_occ
    results["wip_occupation_rate"] = _result("wip_occupation_rate", wip_occ)

    lead_sec = _num(fod, "real_lead_time_seconds")
    lead_sec = lead_sec[lead_sec > 0]
    lead_min = (lead_sec.mean() / 60) if not lead_sec.empty else None
    results["global_lead_time"] = _result("global_lead_time", lead_min)

    otd = _num(fod, "delivered_on_time")
    otd_rate = (otd.mean() * 100) if not fod.empty else None
    results["otd"] = _result("otd", otd_rate)

    energy = _num(fse, "energy_mws").sum()
    energy_per_unit = None
    if out_total > 0:
        energy_per_unit = energy / out_total / 3_600_000_000  # mWs -> kWh
    results["energy_per_unit"] = _result("energy_per_unit", energy_per_unit)

    air = _num(fse, "air_mnl").sum()
    air_per_unit = None
    if out_total > 0:
        air_per_unit = air / out_total / 1000  # mNl -> L
    results["air_per_unit"] = _result("air_per_unit", air_per_unit)

    return results


def _daily_summary_rows(ms: pd.DataFrame, fse: pd.DataFrame, fqe: pd.DataFrame, fss: pd.DataFrame, fod: pd.DataFrame, day_col_map: dict[str, str]) -> list[date]:
    days = set()
    for df, col in [(ms, day_col_map["ms"]), (fse, day_col_map["fse"]), (fqe, day_col_map["fqe"]), (fss, day_col_map["fss"]), (fod, day_col_map["fod"])]:
        if not df.empty and col in df.columns:
            days.update(_normalize_dates(df, col)[col].dropna().tolist())
    return sorted(days)


def _compute_details(ms: pd.DataFrame, fse: pd.DataFrame, fqe: pd.DataFrame, fss: pd.DataFrame, fod: pd.DataFrame) -> dict:
    ms = _normalize_dates(ms, "date")
    fse = _normalize_dates(fse, "date")
    fqe = _normalize_dates(fqe, "date")
    fss = _normalize_dates(fss, "date")
    fod = _normalize_dates(fod, "end_date", "start_date", "planned_end_date")

    details = {
        "performance": {"trs_evolution": [], "cycle_time_evolution": []},
        "quality": {"non_conformity_evolution": [], "errors_by_machine": [], "critical_errors": []},
        "stock": {"stock_evolution": [], "zone_occupancy": []},
        "delay": {"otd_evolution": [], "lead_time_by_product": []},
        "energy": {"energy_evolution": [], "combined": []},
        "maintenance": {"error_evolution": [], "stop_time_evolution": [], "total_stop_time_minutes": None},
    }

    days = _daily_summary_rows(ms, fse, fqe, fss, fod, {"ms": "date", "fse": "date", "fqe": "date", "fss": "date", "fod": "end_date"})
    for day in days[-7:]:
        ms_d = ms[ms["date"] == day] if not ms.empty else ms
        fse_d = fse[fse["date"] == day] if not fse.empty else fse
        fqe_d = fqe[fqe["date"] == day] if not fqe.empty else fqe
        fss_d = fss[fss["date"] == day] if not fss.empty else fss
        fod_d = fod[fod["end_date"] == day] if not fod.empty else fod
        s = _compute_summary(ms_d, fse_d, fqe_d, fss_d, fod_d)
        details["performance"]["trs_evolution"].append({"day": _weekday_fr(day), "date": _day_str(day), "trs": s["trs"]["value"] or 0})
        details["performance"]["cycle_time_evolution"].append({"day": _weekday_fr(day), "date": _day_str(day), "value": s["cycle_time"]["value"] or 0})
        details["quality"]["non_conformity_evolution"].append({"day": _weekday_fr(day), "date": _day_str(day), "taux": s["non_conformity_rate"]["value"] or 0})
        details["delay"]["otd_evolution"].append({"day": _weekday_fr(day), "date": _day_str(day), "value": s["otd"]["value"] or 0})
        details["energy"]["energy_evolution"].append({"date": _day_str(day), "kwh": round(float(s["energy_per_unit"]["value"] or 0), 4)})
        details["energy"]["combined"].append(
            {
                "date": _day_str(day),
                "kwh": round(float(s["energy_per_unit"]["value"] or 0), 4),
                "air": round(float(s["air_per_unit"]["value"] or 0), 2),
            }
        )

    if not fqe.empty:
        tmp = fqe.copy()
        tmp["piece_count"] = _num(tmp, "piece_count")
        if "machine_name" in tmp.columns:
            agg = (
                tmp.groupby(tmp["machine_name"].fillna("Machine"))["piece_count"]
                .sum()
                .sort_values(ascending=False)
                .head(8)
            )
            details["quality"]["errors_by_machine"] = [{"machine": str(idx), "errors": int(val)} for idx, val in agg.items()]

        crit = tmp[_num(tmp, "is_critical") > 0].copy()
        if not crit.empty:
            crit = crit.sort_values(["date", "hour"], ascending=False).head(10)
            details["quality"]["critical_errors"] = [
                {
                    "date": f"{_day_str(row['date'])}{f' {int(row['hour']):02d}:00' if pd.notna(row.get('hour')) else ''}",
                    "machine": str(row.get("machine_name") or "Machine"),
                    "cause": str(row.get("error_description") or row.get("error_code") or "Défaut"),
                }
                for _, row in crit.iterrows()
            ]

        agg_err = tmp.groupby("date").agg(
            critiques=("is_critical", lambda s: int((_num(pd.DataFrame({"v": s}), "v") > 0).sum())),
            total=("piece_count", "sum"),
        ).reset_index()
        details["maintenance"]["error_evolution"] = [
            {
                "day": _weekday_fr(row["date"]),
                "date": _day_str(row["date"]),
                "critiques": int(row["critiques"]),
                "total": int(row["total"]),
            }
            for _, row in agg_err.tail(7).iterrows()
        ]

    if not fss.empty:
        tmp = fss.copy()
        tmp["positions_used"] = _num(tmp, "positions_used")
        tmp["capacity_positions"] = _num(tmp, "capacity_positions")
        by_day = tmp.groupby("date").agg(used=("positions_used", "sum"), cap=("capacity_positions", "sum")).reset_index()
        details["stock"]["stock_evolution"] = [
            {
                "date": _day_str(row["date"]),
                "value": round((float(row["used"]) / float(row["cap"]) * 100) if row["cap"] else 0, 2),
            }
            for _, row in by_day.tail(7).iterrows()
        ]

        tmp["label"] = tmp.apply(
            lambda r: str(r.get("area") or f"B{int(r.get('mes_resource_id', 0))}-{int(r.get('mes_bufno', 0))}"),
            axis=1,
        )
        tmp["occ"] = tmp.apply(
            lambda r: (float(r["positions_used"]) / float(r["capacity_positions"]) * 100) if r["capacity_positions"] else 0,
            axis=1,
        )
        tmp["is_wip"] = _num(tmp, "buffer_type") != 1
        rows = []
        for label, g in tmp.groupby("label"):
            storage_vals = g.loc[~g["is_wip"], "occ"]
            wip_vals = g.loc[g["is_wip"], "occ"]
            rows.append(
                {
                    "zone": label[:24],
                    "stockage": round(float(storage_vals.mean()) if not storage_vals.empty else 0, 2),
                    "encours": round(float(wip_vals.mean()) if not wip_vals.empty else 0, 2),
                }
            )
        details["stock"]["zone_occupancy"] = sorted(rows, key=lambda r: max(r["stockage"], r["encours"]), reverse=True)[:10]

    if not fod.empty:
        tmp = fod.copy()
        tmp["delivered_on_time"] = _num(tmp, "delivered_on_time")
        agg = tmp.groupby("end_date")["delivered_on_time"].mean().mul(100).reset_index()
        details["delay"]["otd_evolution"] = [
            {"day": _weekday_fr(row["end_date"]), "date": _day_str(row["end_date"]), "value": round(float(row["delivered_on_time"]), 2)}
            for _, row in agg.tail(7).iterrows()
        ]

        tmp["real_lead_time_seconds"] = _num(tmp, "real_lead_time_seconds")
        tmp = tmp[tmp["real_lead_time_seconds"] > 0].copy()
        if not tmp.empty:
            tmp = tmp.sort_values("end_date", ascending=False).head(8)
            details["delay"]["lead_time_by_product"] = [
                {
                    "product": str(row.get("product_name") or (f"OF-{int(row['mes_ono'])}" if pd.notna(row.get("mes_ono")) else "Ordre")),
                    "leadTime": round(float(row["real_lead_time_seconds"]) / 3600, 2),
                }
                for _, row in tmp.iterrows()
            ][::-1]

    if not ms.empty:
        tmp = ms.copy()
        tmp["error_seconds"] = _num(tmp, "error_seconds")
        stop = tmp.groupby("date")["error_seconds"].sum().reset_index()
        details["maintenance"]["stop_time_evolution"] = [
            {
                "day": _weekday_fr(row["date"]),
                "date": _day_str(row["date"]),
                "minutes": round(float(row["error_seconds"]) / 60, 1),
            }
            for _, row in stop.tail(7).iterrows()
        ]
        details["maintenance"]["total_stop_time_minutes"] = round(float(stop.tail(7)["error_seconds"].sum()) / 60, 1)

    return details


def build_telephan_payload(detail_days: int = 7, filters: Optional[dict] = None) -> Optional[dict]:
    schema = _sql_schema()
    if not _warehouse_ready(schema):
        return None

    anchor = _anchor_date(schema)
    if anchor is None:
        return None
    data_start = _min_date(schema)
    reference_date = _time_reference_date(anchor)

    summary_days = max(1, int((dash_config.SHIFT_WINDOW.total_seconds() + 86399) // 86400))
    default_days = max(detail_days, summary_days, 7)
    summary_since, summary_until = _temporal_bounds(
        reference_date,
        (filters or {}).get("temporal"),
        default_days=default_days,
        data_start=data_start,
    )
    detail_since, detail_until = summary_since, summary_until

    ms = _fetch_machine_state(schema, detail_since, detail_until)
    fse = _fetch_step_execution(schema, detail_since, detail_until)
    fqe = _fetch_quality_events(schema, detail_since, detail_until)
    fss = _fetch_stock_snapshot(schema, detail_since, detail_until)
    fod = _fetch_order_delivery(schema, detail_since, detail_until)

    # Options de filtres dynamiques basées sur la plage temporelle/shift courante
    ms_base, fse_base, fqe_base, fss_base, fod_base = _apply_filters(ms, fse, fqe, fss, fod, filters, include_dimension_filters=False)
    filter_options = _build_filter_options(ms_base, fse_base, fqe_base, fss_base, fod_base)

    ms, fse, fqe, fss, fod = _apply_filters(ms, fse, fqe, fss, fod, filters, include_dimension_filters=True)

    ms_summary = _slice_since(ms, "date", summary_since)
    fse_summary = _slice_since(fse, "date", summary_since)
    fqe_summary = _slice_since(fqe, "date", summary_since)
    fss_summary = _slice_since(fss, "date", summary_since)
    fod_summary = _slice_since(fod, "end_date", summary_since)

    results = _compute_summary(ms_summary, fse_summary, fqe_summary, fss_summary, fod_summary)
    details = _compute_details(ms, fse, fqe, fss, fod)
    _apply_energy_csv_fallback(results, details, fse_summary, summary_since, summary_until, filters)

    return {
        "results": results,
        "details": details,
        "filter_options": filter_options,
        "data_start_date": data_start.isoformat() if data_start else None,
        "anchor_date": anchor.isoformat(),
        "time_reference_date": reference_date.isoformat(),
        "data_is_stale": anchor < reference_date,
        "source": "telephan_warehouse",
    }
