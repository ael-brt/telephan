import { Zap, Wind, TrendingUp } from "lucide-react";
import { GaugeChart } from "../GaugeChart";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, ReferenceLine, AreaChart, Area } from "recharts";
import { useDashboardSummary } from "@/hooks/use-dashboard-summary";
import { compareToTargetText, formatKpiValue, kpiTarget, kpiValue } from "@/lib/kpi-format";

// Données pour les graphiques
const energyEvolution = [
  { date: "Lun", kwh: 1.18 },
  { date: "Mar", kwh: 1.25 },
  { date: "Mer", kwh: 1.32 },
  { date: "Jeu", kwh: 1.28 },
  { date: "Ven", kwh: 1.22 },
  { date: "Sam", kwh: 1.15 },
  { date: "Dim", kwh: 1.24 },
];

const combinedData = [
  { date: "Lun", kwh: 1.18, air: 2.75 },
  { date: "Mar", kwh: 1.25, air: 2.92 },
  { date: "Mer", kwh: 1.32, air: 3.05 },
  { date: "Jeu", kwh: 1.28, air: 2.98 },
  { date: "Ven", kwh: 1.22, air: 2.85 },
  { date: "Sam", kwh: 1.15, air: 2.68 },
  { date: "Dim", kwh: 1.24, air: 2.89 },
];

export const EnergyTab = () => {
  const { data } = useDashboardSummary();
  const energyKpi = data?.sections.energy.energy_per_unit;
  const airKpi = data?.sections.energy.air_per_unit;

  const energyPerPiece = kpiValue(energyKpi);
  const energyObjective = kpiTarget(energyKpi, 1.2);

  // Calcul du % par rapport à l'objectif (inversé car moins = mieux)
  const energyPercentage =
    energyPerPiece > 0 ? Math.min((energyObjective / energyPerPiece) * 100, 100) : 0;
  const energyEvolutionData =
    data?.details.energy.energy_evolution?.length ? data.details.energy.energy_evolution : energyEvolution;
  const combinedEnergyData = data?.details.energy.combined?.length ? data.details.energy.combined : combinedData;

  return (
    <div className="p-6 space-y-6">
      {/* KPIs - 2 indicateurs */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* KPI 1: Consommation énergétique moyenne par pièce (KPI clé) */}
        <div className="bg-card rounded-xl border border-l-4 border-l-kpi-energy p-5">
          <div className="flex items-center gap-2 mb-3">
            <Zap className="w-5 h-5 text-kpi-energy" />
            <span className="text-xs text-muted-foreground font-medium uppercase tracking-wide">KPI Clé</span>
          </div>
          <p className="text-4xl font-bold text-warning">{formatKpiValue(energyKpi)}</p>
          <p className="text-sm text-muted-foreground mt-1">Consommation énergétique / pièce</p>
          <div className="flex items-center gap-1 mt-3 text-xs text-destructive">
            <TrendingUp className="w-3 h-3" />
            <span>{compareToTargetText(energyKpi)}</span>
          </div>
        </div>

        {/* KPI 2: Air comprimé moyen par pièce */}
        <div className="bg-card rounded-xl border p-5">
          <div className="flex items-center gap-2 mb-3">
            <Wind className="w-5 h-5 text-primary" />
            <span className="text-xs text-muted-foreground font-medium uppercase tracking-wide">Air comprimé</span>
          </div>
          <p className="text-4xl font-bold text-warning">{formatKpiValue(airKpi)}</p>
          <p className="text-sm text-muted-foreground mt-1">Air comprimé moyen / pièce</p>
          <div className="flex items-center gap-1 mt-3 text-xs text-destructive">
            <TrendingUp className="w-3 h-3" />
            <span>{compareToTargetText(airKpi)}</span>
          </div>
        </div>
      </div>

      {/* Graphiques */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Énergie - Jauge + Évolution */}
        <div className="bg-card rounded-xl border p-5">
          <h3 className="text-sm font-medium mb-4">Consommation énergétique</h3>
          <div className="flex items-center gap-6">
            <GaugeChart 
              value={energyPercentage} 
              size={140}
              thresholds={{ warning: 90, danger: 80 }}
            />
            <div className="flex-1 h-32">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={energyEvolutionData}>
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis hide domain={[1, 1.5]} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'hsl(var(--card))', 
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                      fontSize: '12px'
                    }} 
                  />
                  <ReferenceLine y={energyObjective} stroke="hsl(var(--muted-foreground))" strokeDasharray="3 3" />
                  <Line 
                    type="monotone" 
                    dataKey="kwh" 
                    stroke="hsl(var(--kpi-energy))" 
                    strokeWidth={2}
                    dot={{ fill: "hsl(var(--kpi-energy))", r: 3 }}
                    name="kWh/pièce"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
          <p className="text-xs text-muted-foreground text-center mt-2">Évolution hebdomadaire</p>
        </div>

        {/* Énergie & Air combinés */}
        <div className="bg-card rounded-xl border p-5">
          <h3 className="text-sm font-medium mb-4">Énergie & Air comprimé</h3>
          <div className="h-44">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={combinedEnergyData}>
                <XAxis dataKey="date" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis yAxisId="left" tick={{ fontSize: 10 }} domain={[1, 1.5]} axisLine={false} tickLine={false} />
                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10 }} domain={[2, 3.5]} axisLine={false} tickLine={false} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--card))', 
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                    fontSize: '12px'
                  }} 
                />
                <Area 
                  yAxisId="left"
                  type="monotone" 
                  dataKey="kwh" 
                  stroke="hsl(var(--kpi-energy))"
                  fill="hsl(var(--kpi-energy) / 0.2)"
                  strokeWidth={2}
                  name="Énergie (kWh)"
                />
                <Line 
                  yAxisId="right"
                  type="monotone" 
                  dataKey="air" 
                  stroke="hsl(var(--primary))" 
                  strokeWidth={2}
                  dot={{ r: 2 }}
                  name="Air (m³)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center justify-center gap-6 mt-2 text-xs">
            <span className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-kpi-energy" />
              Énergie (kWh)
            </span>
            <span className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-primary" />
              Air (m³)
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
