from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine

from . import config

logger = logging.getLogger(__name__)


def _engine():
    url = (
        f"mysql+pymysql://{config.DB_USER}:{config.DB_PASSWORD}"
        f"@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
    )
    return create_engine(url, pool_pre_ping=True)


def _safe_read_sql(query: str, params: Optional[dict] = None) -> pd.DataFrame:
    try:
        with _engine().connect() as conn:
            return pd.read_sql(query, conn, params=params)
    except Exception as exc:  # pragma: no cover - log and return empty
        logger.warning("SQL read failed for %s: %s", query.split()[0], exc)
        return pd.DataFrame()


def run_sql(query: str, params: Optional[dict] = None) -> pd.DataFrame:
    """Public helper for ad-hoc SQL reads (warehouse/facts, diagnostics, etc.)."""
    return _safe_read_sql(query, params)


def fetch_parts_report(window: timedelta) -> pd.DataFrame:
    since = datetime.utcnow() - window
    query = """
        SELECT ResourceID, TimeStamp, PNo, ErrorID, ID
        FROM tblpartsreport
        WHERE TimeStamp >= %(since)s
        ORDER BY TimeStamp DESC
    """
    return _safe_read_sql(query, {"since": since})


def fetch_machine_report(window: timedelta) -> pd.DataFrame:
    since = datetime.utcnow() - window
    query = """
        SELECT ResourceID, TimeStamp, Busy, ErrorL0, ErrorL1, ErrorL2, ID
        FROM tblmachinereport
        WHERE TimeStamp >= %(since)s
        ORDER BY TimeStamp DESC
    """
    return _safe_read_sql(query, {"since": since})


def fetch_finorders() -> pd.DataFrame:
    query = """
        SELECT ONo, PlannedStart, PlannedEnd, Start, End, State
        FROM tblfinorder
    """
    return _safe_read_sql(query)


def fetch_finstep(window: Optional[timedelta] = None) -> pd.DataFrame:
    params = {}
    where_clause = ""
    if window:
        since = datetime.utcnow() - window
        where_clause = "WHERE Start >= %(since)s"
        params["since"] = since
    query = f"""
        SELECT ONo, OPos, StepNo, ResourceID, Start, End,
               ElectricEnergyReal, ElectricEnergyCalc,
               CompressedAirReal, CompressedAirCalc,
               ErrorStep
        FROM tblfinstep
        {where_clause}
    """
    return _safe_read_sql(query, params or None)


def fetch_buffer_positions() -> pd.DataFrame:
    query = """
        SELECT ResourceId, BufNo, BufPos, Quantity, QuantityMax, Zone, Type
        FROM tblbufferpos
    """
    return _safe_read_sql(query)


def fetch_resources() -> pd.DataFrame:
    query = """
        SELECT ResourceID, ResourceName, Description
        FROM tblresource
    """
    return _safe_read_sql(query)
