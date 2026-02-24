import os
from datetime import timedelta

# Base de données
DB_NAME = os.environ.get("DB_NAME", "mes4")
DB_USER = os.environ.get("DB_USER", "example_user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "example_password")
DB_HOST = os.environ.get("DB_HOST", "mariadb")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DWH_SCHEMA = os.environ.get("DWH_SCHEMA", "mes_kpi")
TIME_REFERENCE_MODE = os.environ.get("TIME_REFERENCE_MODE", "system").lower()

# Fenêtre d'analyse "shift" (8h par défaut)
SHIFT_WINDOW = timedelta(minutes=int(os.environ.get("SHIFT_MINUTES", "480")))

# Rafraîchissement Dash (ms) - 15 secondes par défaut
REFRESH_INTERVAL_MS = int(os.environ.get("REFRESH_INTERVAL_MS", "15000"))

# Objectifs par KPI (valeurs cibles)
KPI_TARGETS = {
    "machine_utilization": 85.0,
    "trs": 80.0,
    "cycle_time": 60.0,  # secondes par pièce (objectif max)
    "operation_execution_rate": 90.0,
    "non_conformity_rate": 2.0,
    "error_count": 0,  # objectif : aucune erreur
    "critical_error_count": 0,
    "average_stock_level": 100.0,  # valeur arbitraire à ajuster selon métier
    "storage_occupation_rate": 80.0,
    "wip_occupation_rate": 80.0,
    "global_lead_time": 30.0,  # minutes - ajuster selon CDC métier
    "otd": 95.0,
    "energy_per_unit": 0.15,  # kWh/unit hypothétique
    "air_per_unit": 5.0,      # L/unit hypothétique
}

# Seuils couleur pour objectifs (bordures KPIs)
COLOR_THRESHOLDS = {
    "good": 1.0,    # >= 100 % de l'objectif
    "warn": 0.8,    # >= 80 % de l'objectif
}

# Seuils couleur pour blocs (feu tricolore)
BLOCK_THRESHOLDS = {
    "green": 1.0,    # 100 % des KPIs atteints
    "orange": 0.8,   # entre 80 % et 100 %
}

# Charte graphique (couleurs et ressources)
BACKGROUND_IMAGE = os.environ.get("BACKGROUND_IMAGE", None)  # chemin relatif ou URL
LEGAL_BAND_TEXT = (
    "Tous droits réservés, y compris ceux en relations avec toutes utilisation, "
    "modification, exploitation, transmission, et dans le cas d’un dépôt de propriété."
)

# Configuration des blocs et des KPI (clé -> fonction kpis)
BLOCKS = {
    "performance": {
        "label": "Performance",
        "main_kpi": "trs",
        "other_kpis": ["machine_utilization", "cycle_time", "operation_execution_rate"],
    },
    "quality": {
        "label": "Qualité",
        "main_kpi": "non_conformity_rate",
        "other_kpis": ["error_count", "critical_error_count"],
    },
    "stock": {
        "label": "Stock",
        "main_kpi": "storage_occupation_rate",
        "other_kpis": ["average_stock_level", "wip_occupation_rate"],
    },
    "delay": {
        "label": "Délai",
        "main_kpi": "otd",
        "other_kpis": ["global_lead_time"],
    },
    "energy": {
        "label": "Énergie",
        "main_kpi": "energy_per_unit",
        "other_kpis": ["air_per_unit"],
    },
}
