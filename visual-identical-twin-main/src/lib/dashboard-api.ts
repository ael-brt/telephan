import type { DashboardFilters } from "@/lib/dashboard-filters";

export interface DashboardKpi {
  key: string;
  label: string;
  value: number | null;
  unit: string;
  type: string;
  format: string;
  target: number | null;
  better_when: "higher" | "lower";
  ratio: number | null;
  color: string;
}

export interface DashboardSummaryResponse {
  generated_at: string;
  window_minutes: number;
  data_source?: string;
  anchor_date?: string;
  kpis: Record<string, DashboardKpi | null>;
  details: {
    performance: {
      trs_evolution: Array<{ day: string; date?: string; trs: number }>;
      cycle_time_evolution: Array<{ day: string; date?: string; value: number }>;
    };
    quality: {
      non_conformity_evolution: Array<{ day: string; date?: string; taux: number }>;
      errors_by_machine: Array<{ machine: string; errors: number }>;
      critical_errors: Array<{ date: string; machine: string; cause: string }>;
    };
    stock: {
      stock_evolution: Array<{ date: string; value: number }>;
      zone_occupancy: Array<{ zone: string; stockage: number; encours: number }>;
    };
    delay: {
      otd_evolution: Array<{ day: string; date?: string; value: number }>;
      lead_time_by_product: Array<{ product: string; leadTime: number }>;
    };
    energy: {
      energy_evolution: Array<{ date: string; kwh: number }>;
      combined: Array<{ date: string; kwh: number; air: number }>;
    };
    maintenance: {
      error_evolution: Array<{ day: string; date?: string; critiques: number; total: number }>;
      stop_time_evolution: Array<{ day: string; date?: string; minutes: number }>;
      total_stop_time_minutes: number | null;
    };
  };
  sections: {
    overview: Record<
      string,
      {
        kpi_key: string;
        status: "success" | "warning" | "danger" | "unknown";
        data: DashboardKpi | null;
      }
    >;
    performance: Record<string, DashboardKpi | null>;
    quality: Record<string, DashboardKpi | null>;
    stock: Record<string, DashboardKpi | null>;
    delay: Record<string, DashboardKpi | null>;
    energy: Record<string, DashboardKpi | null>;
    maintenance: Record<string, DashboardKpi | null>;
  };
  filter_options?: {
    machines?: Array<{ value: string; label: string }>;
    products?: Array<{ value: string; label: string }>;
    orders?: Array<{ value: string; label: string }>;
    error_types?: Array<{ value: string; label: string }>;
  };
}

export async function fetchDashboardSummary(filters?: DashboardFilters): Promise<DashboardSummaryResponse> {
  const params = new URLSearchParams();
  if (filters) {
    params.set("temporal", filters.temporal);
    params.set("shift", filters.shift);
    params.set("machine", filters.machine);
    params.set("product", filters.product);
    params.set("of", filters.of);
    params.set("error_type", filters.errorType);
  }
  const query = params.toString();

  const response = await fetch(`/api/dashboard/summary/${query ? `?${query}` : ""}`, {
    headers: { Accept: "application/json" },
    credentials: "include",
  });

  if (response.status === 401) {
    let loginUrl = "/login?next=/";
    try {
      const body = (await response.json()) as { login_url?: string };
      if (body.login_url) {
        loginUrl = body.login_url;
      }
    } catch {
      // Ignore parse errors and use fallback login URL.
    }
    if (typeof window !== "undefined") {
      window.location.href = loginUrl;
    }
    throw new Error(`dashboard_summary_${response.status}:${loginUrl}`);
  }

  if (!response.ok) {
    throw new Error(`dashboard_summary_${response.status}`);
  }

  return response.json();
}
