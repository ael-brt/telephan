import { createContext, PropsWithChildren, useContext, useState } from "react";

export interface DashboardFilters {
  temporal: string;
  shift: string;
  machine: string;
  product: string;
  of: string;
  errorType: string;
}

export const DEFAULT_DASHBOARD_FILTERS: DashboardFilters = {
  temporal: "all-time",
  shift: "all",
  machine: "all",
  product: "all",
  of: "all",
  errorType: "all",
};

interface DashboardFiltersContextValue {
  filters: DashboardFilters;
  setFilter: <K extends keyof DashboardFilters>(key: K, value: DashboardFilters[K]) => void;
  resetFilters: () => void;
}

const DashboardFiltersContext = createContext<DashboardFiltersContextValue | null>(null);

export function DashboardFiltersProvider({ children }: PropsWithChildren) {
  const [filters, setFilters] = useState<DashboardFilters>(DEFAULT_DASHBOARD_FILTERS);

  const setFilter: DashboardFiltersContextValue["setFilter"] = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const resetFilters = () => setFilters(DEFAULT_DASHBOARD_FILTERS);

  return (
    <DashboardFiltersContext.Provider value={{ filters, setFilter, resetFilters }}>
      {children}
    </DashboardFiltersContext.Provider>
  );
}

export function useDashboardFilters() {
  const ctx = useContext(DashboardFiltersContext);
  if (!ctx) {
    throw new Error("useDashboardFilters must be used within DashboardFiltersProvider");
  }
  return ctx;
}
