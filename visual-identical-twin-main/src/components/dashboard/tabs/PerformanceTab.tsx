import { Factory, Clock, TrendingUp, Activity } from "lucide-react";
import { GaugeChart } from "../GaugeChart";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, ReferenceLine, Tooltip } from "recharts";
import { useDashboardSummary } from "@/hooks/use-dashboard-summary";
import { compareToTargetText, formatKpiValue, kpiTarget, kpiValue } from "@/lib/kpi-format";

// Données pour les graphiques
const trsEvolution = [
  { day: "Lun", trs: 82 },
  { day: "Mar", trs: 78 },
  { day: "Mer", trs: 85 },
  { day: "Jeu", trs: 80 },
  { day: "Ven", trs: 83 },
  { day: "Sam", trs: 79 },
  { day: "Dim", trs: 81 },
];

const cycleTimeData = [
  { day: "Lun", value: 10.5 },
  { day: "Mar", value: 11.2 },
  { day: "Mer", value: 10.8 },
  { day: "Jeu", value: 12.1 },
  { day: "Ven", value: 11.5 },
  { day: "Sam", value: 10.2 },
  { day: "Dim", value: 9.8 },
];

export const PerformanceTab = () => {
  const { data } = useDashboardSummary();
  const machineUtilization = data?.sections.performance.machine_utilization;
  const trs = data?.sections.performance.trs;
  const cycleTime = data?.sections.performance.cycle_time;
  const operationExecutionRate = data?.sections.performance.operation_execution_rate;

  const trsPct = kpiValue(trs);
  const cycleTimeSeconds = kpiValue(cycleTime);
  const operationExecutionPct = kpiValue(operationExecutionRate);
  const trsTarget = kpiTarget(trs, 80);
  const cycleTimeTarget = kpiTarget(cycleTime, 10.5);
  const trsEvolutionData = data?.details.performance.trs_evolution?.length ? data.details.performance.trs_evolution : trsEvolution;
  const cycleTimeEvolutionData = data?.details.performance.cycle_time_evolution?.length ? data.details.performance.cycle_time_evolution : cycleTimeData;

  return (
    <div className="p-6 space-y-6">
      {/* 4 KPIs principaux */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: Taux d'utilisation des machines (KPI clé) */}
        <div className="bg-card rounded-xl border border-l-4 border-l-kpi-performance p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-2 rounded-lg bg-kpi-performance/10">
              <Factory className="w-5 h-5 text-kpi-performance" />
            </div>
            <span className="text-xs font-semibold text-kpi-performance uppercase tracking-wide">KPI Clé</span>
          </div>
          <p className="text-4xl font-bold text-success">{formatKpiValue(machineUtilization)}</p>
          <p className="text-sm text-muted-foreground mt-1">Taux d'utilisation machines</p>
          <div className="flex items-center gap-1 mt-3 text-xs text-success">
            <TrendingUp className="w-3 h-3" />
            <span>{compareToTargetText(machineUtilization)}</span>
          </div>
        </div>

        {/* KPI 2: TRS */}
        <div className="bg-card rounded-xl border p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-2 rounded-lg bg-muted">
              <Activity className="w-5 h-5 text-muted-foreground" />
            </div>
            <span className="text-xs font-medium text-muted-foreground">TRS</span>
          </div>
          <p className="text-4xl font-bold text-warning">{formatKpiValue(trs)}</p>
          <p className="text-sm text-muted-foreground mt-1">Taux de Rendement Synthétique</p>
          <p className="text-xs text-muted-foreground mt-3">Objectif TRS: {trsTarget.toFixed(1)}%</p>
        </div>

        {/* KPI 3: Temps de cycle */}
        <div className="bg-card rounded-xl border p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-2 rounded-lg bg-muted">
              <Clock className="w-5 h-5 text-muted-foreground" />
            </div>
            <span className="text-xs font-medium text-muted-foreground">Temps de cycle</span>
          </div>
          <p className="text-4xl font-bold text-foreground">
            {cycleTimeSeconds ? cycleTimeSeconds.toFixed(1) : "--"}
            <span className="text-lg font-normal text-muted-foreground">s</span>
          </p>
          <p className="text-sm text-muted-foreground mt-1">Temps de cycle moyen</p>
          <div className="mt-3 text-xs">
            <div className="flex justify-between text-muted-foreground">
              <span>Objectif</span>
              <span className="text-success font-medium">{cycleTimeTarget.toFixed(1)}s</span>
            </div>
          </div>
        </div>

        {/* KPI 4: Taux d'exécution */}
        <div className="bg-card rounded-xl border p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-2 rounded-lg bg-muted">
              <TrendingUp className="w-5 h-5 text-muted-foreground" />
            </div>
            <span className="text-xs font-medium text-muted-foreground">Exécution</span>
          </div>
          <p className="text-4xl font-bold text-warning">{formatKpiValue(operationExecutionRate)}</p>
          <p className="text-sm text-muted-foreground mt-1">Taux d'exécution opérations</p>
          <div className="mt-3">
            <div className="flex justify-between text-xs mb-1.5">
              <span className="text-muted-foreground">{compareToTargetText(operationExecutionRate)}</span>
            </div>
            <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
              <div className="h-full bg-warning rounded-full transition-all" style={{ width: `${Math.max(0, Math.min(operationExecutionPct, 100))}%` }} />
            </div>
          </div>
        </div>
      </div>

      {/* Graphiques simplifiés */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* TRS avec jauge */}
        <div className="bg-card rounded-xl border p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-foreground mb-4">TRS - Évolution hebdomadaire</h3>
          <div className="flex items-center gap-6">
            <GaugeChart value={trsPct} size={120} thresholds={{ warning: 80, danger: 60 }} />
            <div className="flex-1 h-28">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trsEvolutionData}>
                  <XAxis dataKey="day" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10 }} domain={[60, 100]} axisLine={false} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'hsl(var(--card))', 
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                      fontSize: '12px'
                    }} 
                  />
                  <ReferenceLine y={trsTarget} stroke="hsl(var(--muted-foreground))" strokeDasharray="3 3" />
                  <Line 
                    type="monotone" 
                    dataKey="trs" 
                    stroke="hsl(var(--kpi-performance))" 
                    strokeWidth={2} 
                    dot={{ r: 3, fill: "hsl(var(--kpi-performance))" }} 
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="flex items-center gap-4 text-xs mt-3 text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <div className="w-3 h-0.5 bg-kpi-performance rounded" />TRS
            </span>
            <span className="flex items-center gap-1.5">
              <div className="w-3 h-0.5 bg-muted-foreground rounded" style={{ backgroundImage: 'repeating-linear-gradient(90deg, transparent, transparent 2px, hsl(var(--muted-foreground)) 2px, hsl(var(--muted-foreground)) 4px)' }} />
              Objectif {trsTarget.toFixed(0)}%
            </span>
          </div>
        </div>

        {/* Temps de cycle */}
        <div className="bg-card rounded-xl border p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-foreground mb-4">Temps de cycle - Évolution</h3>
          <div className="h-36">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={cycleTimeEvolutionData}>
                <XAxis dataKey="day" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10 }} domain={[8, 14]} axisLine={false} tickLine={false} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--card))', 
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                    fontSize: '12px'
                  }} 
                />
                <ReferenceLine 
                  y={cycleTimeTarget} 
                  stroke="hsl(var(--muted-foreground))" 
                  strokeDasharray="3 3" 
                  label={{ value: 'Obj.', position: 'right', fontSize: 10, fill: 'hsl(var(--muted-foreground))' }} 
                />
                <Line 
                  type="monotone" 
                  dataKey="value" 
                  stroke="hsl(var(--primary))" 
                  strokeWidth={2}
                  dot={{ fill: "hsl(var(--primary))", r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center justify-between text-xs mt-3">
            <span className="text-muted-foreground">Moyenne: <span className="font-medium text-foreground">{cycleTimeSeconds ? `${cycleTimeSeconds.toFixed(1)}s` : "--"}</span></span>
            <span className="text-success font-medium">{compareToTargetText(cycleTime)}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
