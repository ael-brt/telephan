import { AlertTriangle, TrendingUp, ClipboardCheck, XCircle } from "lucide-react";
import { GaugeChart } from "../GaugeChart";
import { DataTable } from "../DataTable";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, BarChart, Bar } from "recharts";
import { useDashboardSummary } from "@/hooks/use-dashboard-summary";
import { compareToTargetText, formatKpiValue } from "@/lib/kpi-format";

export const QualityTab = () => {
  const { data } = useDashboardSummary();
  const nonConformity = data?.sections.quality.non_conformity_rate;
  const errorCount = data?.sections.quality.error_count;
  const criticalErrorCount = data?.sections.quality.critical_error_count;

  const totalErrors = errorCount?.value != null ? Math.round(errorCount.value) : null;
  const criticalErrors = criticalErrorCount?.value != null ? Math.round(criticalErrorCount.value) : null;
  const nonConformityRate = nonConformity?.value ?? null;
  const nonConformityChartData = data?.details.quality.non_conformity_evolution ?? [];
  const errorsByMachineData = data?.details.quality.errors_by_machine ?? [];
  const criticalErrorsRows = data?.details.quality.critical_errors ?? [];

  return (
    <div className="p-6 space-y-6">
      {/* Bannière d'alerte si erreurs critiques */}
      {criticalErrors != null && criticalErrors > 0 && (
        <div className="bg-destructive/10 border border-destructive/20 rounded-xl p-4 flex items-center gap-3">
          <div className="p-2 rounded-lg bg-destructive/20">
            <AlertTriangle className="w-5 h-5 text-destructive" />
          </div>
          <div>
            <p className="font-semibold text-foreground">{criticalErrors} erreurs critiques détectées</p>
            <p className="text-sm text-muted-foreground">Consultez le détail des anomalies pour prioriser les interventions</p>
          </div>
        </div>
      )}

      {/* 3 KPIs principaux */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* KPI 1: Taux de non-conformité (KPI clé) */}
        <div className="bg-card rounded-xl border border-l-4 border-l-kpi-quality p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-2 rounded-lg bg-kpi-quality/10">
              <ClipboardCheck className="w-5 h-5 text-kpi-quality" />
            </div>
            <span className="text-xs font-semibold text-kpi-quality uppercase tracking-wide">KPI Clé</span>
          </div>
          <p className="text-4xl font-bold text-destructive">{formatKpiValue(nonConformity)}</p>
          <p className="text-sm text-muted-foreground mt-1">Taux de non-conformité</p>
          <div className="flex items-center gap-1 mt-3 text-xs text-destructive">
            <TrendingUp className="w-3 h-3" />
            <span>{compareToTargetText(nonConformity)}</span>
          </div>
        </div>

        {/* KPI 2: Nombre total d'erreurs/anomalies */}
        <div className="bg-card rounded-xl border p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-2 rounded-lg bg-muted">
              <XCircle className="w-5 h-5 text-muted-foreground" />
            </div>
            <span className="text-xs font-medium text-muted-foreground">Erreurs totales</span>
          </div>
          <p className="text-4xl font-bold text-warning">{formatKpiValue(errorCount, { hideUnit: true, decimals: 0 })}</p>
          <p className="text-sm text-muted-foreground mt-1">Nombre total d'erreurs / anomalies</p>
          <div className="mt-3">
            <div className="flex justify-between text-xs mb-1.5">
              <span className="text-muted-foreground">{compareToTargetText(errorCount)}</span>
              <span className="text-destructive font-medium">Objectif backend</span>
            </div>
            <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-warning rounded-full" style={{ width: `${Math.min(totalErrors ?? 0, 100)}%` }} />
                </div>
              </div>
            </div>

        {/* KPI 3: Nombre d'erreurs critiques */}
        <div className="bg-card rounded-xl border p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <div className="p-2 rounded-lg bg-destructive/10">
              <AlertTriangle className="w-5 h-5 text-destructive" />
            </div>
            <span className="text-xs font-medium text-destructive">Critique</span>
          </div>
          <p className="text-4xl font-bold text-destructive">{formatKpiValue(criticalErrorCount, { hideUnit: true, decimals: 0 })}</p>
          <p className="text-sm text-muted-foreground mt-1">Erreurs critiques</p>
          <p className="text-xs text-muted-foreground mt-3">CNC, robots, capteurs, etc.</p>
        </div>
      </div>

      {/* Graphiques */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Jauge + Évolution taux non-conformité */}
        <div className="bg-card rounded-xl border p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-foreground mb-4">Taux de non-conformité - Évolution</h3>
          {nonConformityRate != null && nonConformityChartData.length > 0 ? (
            <div className="flex items-center gap-6">
              <GaugeChart
                value={nonConformityRate}
                max={10}
                size={120}
                thresholds={{ warning: 3, danger: 5 }}
              />
              <div className="flex-1 h-28">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={nonConformityChartData}>
                    <XAxis dataKey="day" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 10 }} domain={[0, 10]} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                        fontSize: "12px",
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="taux"
                      stroke="hsl(var(--kpi-quality))"
                      strokeWidth={2}
                      dot={{ r: 3, fill: "hsl(var(--kpi-quality))" }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          ) : (
            <div className="h-28 flex items-center justify-center text-xs text-muted-foreground">Aucune donnée disponible</div>
          )}
          <div className="flex items-center gap-4 text-xs mt-3">
            <span className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-success" />
              <span className="text-muted-foreground">&lt;3% OK</span>
            </span>
            <span className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-warning" />
              <span className="text-muted-foreground">3-5% Attention</span>
            </span>
            <span className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-destructive" />
              <span className="text-muted-foreground">&gt;5% Critique</span>
            </span>
          </div>
        </div>

        {/* Erreurs par machine */}
        <div className="bg-card rounded-xl border p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-foreground mb-4">Erreurs par machine</h3>
          {errorsByMachineData.length > 0 ? (
            <div className="h-36">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={errorsByMachineData} layout="vertical">
                  <XAxis type="number" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="machine" tick={{ fontSize: 10 }} width={80} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                      fontSize: "12px",
                    }}
                  />
                  <Bar
                    dataKey="errors"
                    fill="hsl(var(--kpi-quality))"
                    radius={[0, 4, 4, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-36 flex items-center justify-center text-xs text-muted-foreground">Aucune donnée disponible</div>
          )}
          <p className="text-xs text-muted-foreground mt-3">Total période chargée: {totalErrors != null ? `${totalErrors} erreurs` : "--"}</p>
        </div>
      </div>

      {/* Table erreurs critiques */}
      <div className="bg-card rounded-xl border p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-foreground">Détail des erreurs critiques</h3>
          <span className="text-xs font-medium text-destructive bg-destructive/10 px-2 py-1 rounded-full">
            {criticalErrors != null ? `${criticalErrors} erreurs` : "--"}
          </span>
        </div>
        <DataTable
          columns={[
            { key: "date", header: "Date" },
            { key: "machine", header: "Machine" },
            { key: "cause", header: "Cause" },
          ]}
          data={criticalErrorsRows}
        />
      </div>
    </div>
  );
};
