import type { DashboardKpi } from "@/lib/dashboard-api";

export type KpiStatus = "success" | "warning" | "danger" | "unknown";

export function kpiStatus(kpi?: DashboardKpi | null): KpiStatus {
  if (!kpi || kpi.value == null || kpi.ratio == null) return "unknown";
  if (kpi.ratio >= 1) return "success";
  if (kpi.ratio >= 0.8) return "warning";
  return "danger";
}

export function kpiValue(kpi?: DashboardKpi | null, fallback: number | null = null): number | null {
  return typeof kpi?.value === "number" ? kpi.value : fallback;
}

export function kpiTarget(kpi?: DashboardKpi | null, fallback: number | null = null): number | null {
  return typeof kpi?.target === "number" ? kpi.target : fallback;
}

export function formatKpiValue(
  kpi?: DashboardKpi | null,
  options?: { decimals?: number; unitOverride?: string; hideUnit?: boolean },
): string {
  if (!kpi || kpi.value == null) return "--";

  const decimals =
    options?.decimals ??
    (Math.abs(kpi.value) >= 100 ? 0 : kpi.unit === "%" ? 1 : 2);
  const unit = options?.unitOverride ?? kpi.unit;
  const formatted = new Intl.NumberFormat("fr-FR", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(kpi.value);

  if (options?.hideUnit || !unit) return formatted;
  return `${formatted} ${unit}`;
}

export function formatPercentRaw(value: number, decimals = 1): string {
  return `${new Intl.NumberFormat("fr-FR", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)}%`;
}

export function formatMinutesAsHuman(minutes?: number | null): string {
  if (minutes == null || Number.isNaN(minutes)) return "--";
  const rounded = Math.round(minutes);
  const h = Math.floor(rounded / 60);
  const m = rounded % 60;
  if (h <= 0) return `${m} min`;
  return `${h}h ${String(m).padStart(2, "0")}min`;
}

export function compareToTargetText(kpi?: DashboardKpi | null): string {
  if (!kpi || kpi.value == null || kpi.target == null) return "Objectif indisponible";
  const delta = kpi.value - kpi.target;
  if (Math.abs(delta) < 0.05) return "Au niveau de l'objectif";

  const better = kpi.better_when === "higher" ? delta > 0 : delta < 0;
  const abs = Math.abs(delta);
  const suffix = kpi.unit ? ` ${kpi.unit}` : "";
  return `${better ? "Meilleur" : "Écart"} vs objectif: ${new Intl.NumberFormat("fr-FR", {
    maximumFractionDigits: 2,
  }).format(abs)}${suffix}`;
}
