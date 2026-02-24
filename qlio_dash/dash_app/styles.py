COLORS = {
    "text_primary": "#000000",
    "text_secondary": "#7F7F7F",
    "text_blue": "#0E2841",
    "bg_light": "#D1D1D1",
    "border_green_light": "#ABFF91",
    "border_salmon": "#FF7C80",
    "border_orange_light": "#FBE3D6",
    "ok": "#00B050",
    "warn": "#FFC000",
    "alert": "#FF0000",
    "panel_dark": "#1D5655",
    "panel_mid": "#107869",
}

FONTS = {
    "title": "Courier New, monospace",
    "body": "Courier New, monospace",
}

def kpi_color_from_ratio(ratio: float) -> str:
    if ratio is None:
        return COLORS["border_orange_light"]
    if ratio >= 1.0:
        return COLORS["border_green_light"]
    if ratio >= 0.8:
        return COLORS["border_salmon"]
    return COLORS["border_orange_light"]


def block_color_from_share(share: float) -> str:
    if share >= 1.0:
        return COLORS["ok"]
    if share >= 0.8:
        return COLORS["warn"]
    return COLORS["alert"]
