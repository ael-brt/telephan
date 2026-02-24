import pandas as pd

from dash_app import kpis


def test_machine_utilization():
    data = {"machine_report": pd.DataFrame({"Busy": [1, 1, 0, 1]})}
    res = kpis.compute_machine_utilization(data)
    assert res["value"] == 75.0
    assert res["unit"] == "%"


def test_non_conformity_rate():
    data = {"parts_report": pd.DataFrame({"ErrorID": [0, 1, 0, 2]})}
    res = kpis.compute_non_conformity_rate(data)
    assert res["value"] == 50.0
    assert res["unit"] == "%"
