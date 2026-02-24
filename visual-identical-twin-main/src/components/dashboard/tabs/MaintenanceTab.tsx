import { Wrench, AlertTriangle, Clock, TrendingDown } from "lucide-react";
import { GaugeChart } from "../GaugeChart";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, LineChart, Line, ReferenceLine } from "recharts";
import { useDashboardSummary } from "@/hooks/use-dashboard-summary";
import { compareToTargetText, formatKpiValue, formatMinutesAsHuman, kpiValue } from "@/lib/kpi-format";

// Données pour les graphiques
const errorEvolution = [
  { day: "Lun", critiques: 1, total: 5 },
  { day: "Mar", critiques: 2, total: 8 },
  { day: "Mer", critiques: 1, total: 6 },
  { day: "Jeu", critiques: 0, total: 4 },
  { day: "Ven", critiques: 1, total: 5 },
  { day: "Sam", critiques: 0, total: 3 },
  { day: "Dim", critiques: 0, total: 2 },
];

const stopTimeEvolution = [
  { day: "Lun", minutes: 45 },
  { day: "Mar", minutes: 68 },
  { day: "Mer", minutes: 52 },
  { day: "Jeu", minutes: 35 },
  { day: "Ven", minutes: 42 },
  { day: "Sam", minutes: 28 },
  { day: "Dim", minutes: 18 },
];

export const MaintenanceTab = () => {
  const { data } = useDashboardSummary();
  const criticalErrorKpi = data?.sections.maintenance.critical_error_count;
  const totalErrorKpi = data?.sections.maintenance.error_count;

  const criticalErrors = Math.round(kpiValue(criticalErrorKpi));
  const totalMachineErrors = Math.max(Math.round(kpiValue(totalErrorKpi)), 1);
  const errorEvolutionData =
    data?.details.maintenance.error_evolution?.length ? data.details.maintenance.error_evolution : errorEvolution;
  const stopTimeEvolutionData =
    data?.details.maintenance.stop_time_evolution?.length ? data.details.maintenance.stop_time_evolution : stopTimeEvolution;
  const hasRealStopTime = data?.details.maintenance.total_stop_time_minutes != null;
  const totalStopTimeMinutes = data?.details.maintenance.total_stop_time_minutes ?? 135; // fallback demo until backend computes it
  const stopTimeObjective = 210; // 30min * 7 jours

  // Pourcentage inversé (moins = mieux)
  const stopTimePercentage = Math.min((1 - totalStopTimeMinutes / stopTimeObjective) * 100 + 50, 100);

  return (
    <div className="p-6 space-y-6">
      {/* KPIs - 3 indicateurs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* KPI 1: Nombre d'erreurs critiques (KPI clé) */}
        <div className="bg-card rounded-xl border border-l-4 border-l-kpi-maintenance p-5">
          <div className="flex items-center gap-2 mb-3">
            <Wrench className="w-5 h-5 text-kpi-maintenance" />
            <span className="text-xs text-muted-foreground font-medium uppercase tracking-wide">KPI Clé</span>
          </div>
          <div className="flex items-center gap-3">
            <p className="text-4xl font-bold text-warning">{formatKpiValue(criticalErrorKpi, { hideUnit: true, decimals: 0 })}</p>
            <div className="flex items-center gap-1 text-warning">
              <AlertTriangle className="w-4 h-4" />
              <span className="text-sm font-medium">Attention</span>
            </div>
          </div>
          <p className="text-sm text-muted-foreground mt-1">{criticalErrorKpi?.label ?? "Nombre d'erreurs critiques"}</p>
          <p className="text-xs text-muted-foreground mt-1">Suivi des alertes critiques machines</p>
        </div>

        {/* KPI 2: Nombre total d'erreurs machines */}
        <div className="bg-card rounded-xl border p-5">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-5 h-5 text-muted-foreground" />
            <span className="text-xs text-muted-foreground font-medium uppercase tracking-wide">Erreurs</span>
          </div>
          <p className="text-4xl font-bold text-foreground">{formatKpiValue(totalErrorKpi, { hideUnit: true, decimals: 0 })}</p>
          <p className="text-sm text-muted-foreground mt-1">Nombre total d'erreurs machines</p>
          <div className="mt-3">
            <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
              <div className="h-full bg-warning rounded-full transition-all" style={{ width: `${(criticalErrors / totalMachineErrors) * 100}%` }} />
            </div>
            <p className="text-xs text-muted-foreground mt-1">{compareToTargetText(totalErrorKpi)}</p>
          </div>
        </div>

        {/* KPI 3: Temps d'arrêt lié aux erreurs */}
        <div className="bg-card rounded-xl border p-5">
          <div className="flex items-center gap-2 mb-3">
            <Clock className="w-5 h-5 text-success" />
            <span className="text-xs text-muted-foreground font-medium uppercase tracking-wide">Arrêts</span>
          </div>
          <p className="text-4xl font-bold text-warning">{hasRealStopTime ? formatMinutesAsHuman(totalStopTimeMinutes) : "--"}</p>
          <p className="text-sm text-muted-foreground mt-1">Temps d'arrêt lié aux erreurs</p>
          <div className="flex items-center gap-1 mt-3 text-xs text-success">
            <TrendingDown className="w-3 h-3" />
            <span>{hasRealStopTime ? "Estimation à partir des rapports machine" : "Donnée non branchée (historique arrêts)"}</span>
          </div>
        </div>
      </div>

      {/* Graphiques */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Évolution des erreurs */}
        <div className="bg-card rounded-xl border p-5">
          <h3 className="text-sm font-medium mb-4">Évolution des erreurs</h3>
          <div className="h-44">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={errorEvolutionData}>
                <XAxis dataKey="day" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--card))', 
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                    fontSize: '12px'
                  }} 
                />
                <Bar dataKey="total" fill="hsl(var(--muted-foreground))" name="Total" radius={[4, 4, 0, 0]} />
                <Bar dataKey="critiques" fill="hsl(var(--destructive))" name="Critiques" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center justify-center gap-6 mt-2 text-xs">
            <span className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-muted-foreground" />
              Total
            </span>
            <span className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-destructive" />
              Critiques
            </span>
          </div>
        </div>

        {/* Temps d'arrêt - Jauge + Évolution */}
        <div className="bg-card rounded-xl border p-5">
          <h3 className="text-sm font-medium mb-4">Temps d'arrêt</h3>
          <div className="flex items-center gap-6">
            <GaugeChart 
              value={stopTimePercentage} 
              size={140}
              thresholds={{ warning: 60, danger: 40 }}
            />
            <div className="flex-1 h-32">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={stopTimeEvolutionData}>
                  <XAxis dataKey="day" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis hide domain={[0, 80]} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'hsl(var(--card))', 
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                      fontSize: '12px'
                    }} 
                  />
                  <ReferenceLine y={30} stroke="hsl(var(--muted-foreground))" strokeDasharray="3 3" />
                  <Line 
                    type="monotone" 
                    dataKey="minutes" 
                    stroke="hsl(var(--kpi-maintenance))" 
                    strokeWidth={2}
                    dot={{ fill: "hsl(var(--kpi-maintenance))", r: 3 }}
                    name="Minutes"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
          <p className="text-xs text-muted-foreground text-center mt-2">Objectif: 30 min/jour max</p>
        </div>
      </div>
    </div>
  );
};
