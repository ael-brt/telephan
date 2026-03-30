import { useQuery } from "@tanstack/react-query";

import { useDashboardFilters } from "@/lib/dashboard-filters";
import { fetchDashboardSummary } from "@/lib/dashboard-api";

export function useDashboardSummary() {
  const { filters } = useDashboardFilters();

  return useQuery({
    queryKey: ["dashboard-summary", filters],
    queryFn: () => fetchDashboardSummary(filters),
    refetchInterval: 120000,
    staleTime: 60000,
  });
}
