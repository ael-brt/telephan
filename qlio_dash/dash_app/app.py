from __future__ import annotations

import os
from typing import Dict, List

import dash
from dash import Dash, dcc, html, Input, Output, State, MATCH
import plotly.graph_objects as go

from . import config, data_access, kpis, styles


external_stylesheets = []

app = Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server  # pour déploiement éventuel


def _gauge_figure(kpi: Dict) -> go.Figure:
    """Construit un graphique de type gauge/indicator en fonction de la cible."""
    value = kpi.get("value")
    target = kpi.get("target")
    unit = kpi.get("unit", "")
    better = kpi.get("better_when", "higher")
    label = kpi.get("label", kpi.get("key", "KPI"))

    # borne max simple : max(value, target) * 1.2 avec fallback
    base = max([v for v in [value, target] if isinstance(v, (int, float))] or [1])
    axis_max = base * 1.2 if base > 0 else 1

    # seuils couleur
    if better == "higher":
        green_start = target or 0
        orange_start = (target or 0) * 0.8
        steps = [
            {"range": [0, orange_start], "color": styles.COLORS["alert"]},
            {"range": [orange_start, green_start], "color": styles.COLORS["warn"]},
            {"range": [green_start, axis_max], "color": styles.COLORS["ok"]},
        ]
    else:
        green_end = target or axis_max * 0.5
        orange_end = (target or axis_max * 0.5) * 1.2
        steps = [
            {"range": [0, green_end], "color": styles.COLORS["ok"]},
            {"range": [green_end, orange_end], "color": styles.COLORS["warn"]},
            {"range": [orange_end, axis_max], "color": styles.COLORS["alert"]},
        ]

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value if value is not None else 0,
            number={"suffix": f" {unit}"},
            title={"text": label},
            gauge={
                "axis": {"range": [0, axis_max]},
                "bar": {"color": kpi.get("color", styles.COLORS["ok"])},
                "steps": steps,
                "threshold": {
                    "line": {"color": styles.COLORS["text_blue"], "width": 3},
                    "value": target if target is not None else 0,
                },
            },
        )
    )
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=240, paper_bgcolor="rgba(0,0,0,0)")
    return fig


def kpi_card(kpi: Dict):
    label = kpi.get("label", kpi.get("key", "Indicateur"))
    if kpi.get("value") is None:
        return html.Div(
            className="kpi-card",
            children=[
                html.Div(label, className="kpi-title"),
                html.Div("--", className="kpi-value"),
                html.Div("Donnée indisponible", className="kpi-target"),
            ],
            style={"border": f"6px solid {styles.COLORS['border_orange_light']}"},
        )

    fig = _gauge_figure(kpi)
    return html.Div(
        className="kpi-card",
        children=dcc.Graph(figure=fig, config={"displayModeBar": False}),
        style={"border": f"6px solid {kpi.get('color', styles.COLORS['border_orange_light'])}"},
    )


def block_header(title: str, color: str):
    return html.Div(
        className="block-header",
        children=[
            html.Div("⬢", className="block-logo"),
            html.Div(title, className="block-title"),
            html.Div(className="block-light", style={"backgroundColor": color}),
        ],
    )


def block_layout(title: str, kpi_items: List[kpis.KpiResult]) -> html.Div:
    # Non utilisé dans la version actuelle (blocs custom avec toggle), conservé pour référence.
    color = styles.COLORS["ok"]
    return html.Div(
        className="block",
        children=[
            block_header(title, color),
            html.Div([kpi_card({"label": getattr(k, 'name', title), "value": getattr(k, 'value', None), "unit": getattr(k, 'unit', ''), "target": getattr(k, 'target', None), "color": getattr(k, 'color', styles.COLORS['border_orange_light'])}) for k in kpi_items], className="kpi-grid"),
        ],
        style={"border": f"6px solid {color}"},
    )


def kpi_card_from_data(kpi_dict: Dict):
    if not kpi_dict:
        return kpi_card({"label": "Indicateur indisponible", "value": None, "unit": "", "target": None, "color": styles.COLORS["border_orange_light"]})
    return kpi_card(kpi_dict)


def make_block(block_id: str, block_cfg: dict, kpi_data: Dict[str, Dict]) -> html.Div:
    main_key = block_cfg["main_kpi"]
    other_keys = block_cfg["other_kpis"]
    main_kpi = kpi_card_from_data(kpi_data.get(main_key))
    other_cards = [kpi_card_from_data(kpi_data.get(k)) for k in other_keys]

    return html.Div(
        className="block",
        children=[
            block_header(block_cfg["label"], styles.COLORS["ok"]),
            html.Div(main_kpi, className="kpi-main"),
            html.Button("Voir les autres indicateurs", id={"type": "toggle-btn", "block": block_id}, className="toggle-btn"),
            html.Div(
                other_cards,
                id={"type": "other-kpis", "block": block_id},
                className="kpi-grid",
                style={"display": "none"},
            ),
        ],
    )


def build_blocks(blocks_data: Dict[str, Dict[str, Dict]]):
    blocks = []
    for block_id, cfg in config.BLOCKS.items():
        blocks.append(make_block(block_id, cfg, blocks_data.get(block_id, {})))

    return html.Div(
        className="blocks-wrapper",
        children=[
            html.Div(blocks, className="blocks"),
            html.Div(config.LEGAL_BAND_TEXT, className="legal-band"),
        ],
    )


def fetch_and_compute() -> Dict[str, Dict]:
    """Charge les données et calcule tous les KPI (format dict par clé KPI)."""
    data = {
        "parts_report": data_access.fetch_parts_report(config.SHIFT_WINDOW),
        "machine_report": data_access.fetch_machine_report(config.SHIFT_WINDOW),
        "finorders": data_access.fetch_finorders(),
        "finstep": data_access.fetch_finstep(config.SHIFT_WINDOW),
        "buffer_positions": data_access.fetch_buffer_positions(),
    }
    return kpis.compute_all_kpis(data)


app.layout = html.Div(
    [
        dcc.Store(id="data-store", data={}),
        html.Div(
            className="page",
            style={
                "fontFamily": styles.FONTS["body"],
                "backgroundImage": f"url('{config.BACKGROUND_IMAGE}')" if config.BACKGROUND_IMAGE else "linear-gradient(135deg, #f8fbff, #dfe9f3)",
                "backgroundSize": "cover",
                "minHeight": "100vh",
            },
            children=[
                html.Div(
                    [
                        html.H1("TELEPHAN - Ligne Festo", className="page-title"),
                        html.A(
                            "Déconnexion",
                            href="http://localhost:8000/accounts/logout/?next=http://localhost:8000/accounts/login/?next=http://localhost:8050",
                            className="logout-btn",
                        ),
                        html.Button("Rafraîchir", id="refresh-btn", className="refresh-btn"),
                    ],
                    className="page-header",
                ),
                html.Div(id="page-container"),
            ],
        ),
        dcc.Interval(id="refresh", interval=config.REFRESH_INTERVAL_MS, n_intervals=0),
    ]
)


@app.callback(
    dash.Output("data-store", "data"),
    dash.Input("refresh", "n_intervals"),
    dash.Input("refresh-btn", "n_clicks"),
)
def refresh_data(_, __):
    return fetch_and_compute()


@app.callback(
    dash.Output("page-container", "children"),
    dash.Input("data-store", "data"),
)
def render_page(data):
    blocks_data = {}
    for block_id, cfg in config.BLOCKS.items():
        keys = [cfg["main_kpi"]] + cfg["other_kpis"]
        blocks_data[block_id] = {k: data.get(k) for k in keys}
    return build_blocks(blocks_data)


@app.callback(
    Output({"type": "other-kpis", "block": MATCH}, "style"),
    Input({"type": "toggle-btn", "block": MATCH}, "n_clicks"),
    State({"type": "other-kpis", "block": MATCH}, "style"),
)
def toggle_block(n_clicks, style):
    style = style or {"display": "none"}
    if not n_clicks:
        return style
    display = style.get("display", "none")
    style["display"] = "none" if display == "block" else "block"
    return style


# Styles internes (CSS minimal)
app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%%metas%%}
        <title>TELEPHAN Dashboard</title>
        {%%favicon%%}
        {%%css%%}
        <style>
            body { margin: 0; padding: 0; }
            .page { padding: 24px; color: %(text_primary)s; }
            .page-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
            .page-title { font-size: 32px; font-family: %(font)s; font-weight: 700; color: %(text_blue)s; margin: 0; }
            .refresh-btn { padding: 8px 14px; border-radius: 8px; border: 2px solid %(text_blue)s; background: #fdfdfd; color: %(text_blue)s; cursor: pointer; font-weight: 700; }
            .logout-btn { padding: 8px 14px; border-radius: 8px; border: 2px solid %(text_blue)s; background: #fff5f5; color: %(text_blue)s; text-decoration: none; font-weight: 700; }
            .blocks-wrapper { display: flex; flex-direction: column; gap: 16px; }
            .blocks { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); grid-gap: 16px; }
            .block { background: rgba(255, 255, 255, 0.85); border-radius: 12px; padding: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
            .block-header { display: grid; grid-template-columns: 32px 1fr 48px; align-items: center; grid-gap: 8px; margin-bottom: 8px; }
            .block-logo { font-size: 18px; }
            .block-title { font-size: 18px; font-weight: 700; }
            .block-light { height: 18px; border-radius: 12px; }
            .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); grid-gap: 8px; }
            .kpi-card { background: #fdfdfd; border-radius: 10px; padding: 10px 12px; box-shadow: inset 0 0 0 1px rgba(0,0,0,0.04); }
            .kpi-title { font-weight: 600; color: %(text_blue)s; font-size: 14px; }
            .kpi-value { font-size: 20px; font-weight: 700; color: %(text_primary)s; }
            .kpi-unit { font-size: 14px; color: %(text_secondary)s; }
            .kpi-target { font-size: 12px; color: %(text_secondary)s; }
            .toggle-btn { margin-top: 8px; padding: 8px 12px; border: 2px solid %(text_blue)s; background: #fff; color: %(text_blue)s; border-radius: 8px; cursor: pointer; font-weight: 700; }
            .kpi-main { margin-bottom: 8px; }
            .legal-band { margin-top: 20px; padding: 10px 12px; background: %(bg_light)s; color: %(text_secondary)s; border-radius: 8px; border: 2px solid %(text_blue)s; font-size: 11px; }
        </style>
    </head>
    <body>
        {%%app_entry%%}
        <footer>
            {%%config%%}
            {%%scripts%%}
            {%%renderer%%}
        </footer>
    </body>
</html>
""" % {
    "text_primary": styles.COLORS["text_primary"],
    "text_blue": styles.COLORS["text_blue"],
    "text_secondary": styles.COLORS["text_secondary"],
    "bg_light": styles.COLORS["bg_light"],
    "font": styles.FONTS["body"],
}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8050"))
    app.run_server(host="0.0.0.0", port=port, debug=False)
