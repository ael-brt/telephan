import { Package, TrendingUp, Warehouse, Settings } from "lucide-react";
import { GaugeChart } from "../GaugeChart";
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip, BarChart, Bar } from "recharts";
import { useDashboardSummary } from "@/hooks/use-dashboard-summary";
import { compareToTargetText, formatKpiValue, kpiValue } from "@/lib/kpi-format";

// Données pour les graphiques
const stockEvolution = [
  { date: "Lun", value: 82 },
  { date: "Mar", value: 85 },
  { date: "Mer", value: 87 },
  { date: "Jeu", value: 84 },
  { date: "Ven", value: 89 },
  { date: "Sam", value: 87 },
  { date: "Dim", value: 87 },
];

const zoneOccupancy = [
  { zone: "Zone A", stockage: 92, encours: 45 },
  { zone: "Zone B", stockage: 78, encours: 65 },
  { zone: "Zone C", stockage: 65, encours: 56 },
  { zone: "Zone D", stockage: 56, encours: 72 },
  { zone: "Zone E", stockage: 45, encours: 38 },
];

export const StockTab = () => {
  const { data } = useDashboardSummary();
  const averageStockLevel = data?.sections.stock.average_stock_level;
  const storageOccupancyKpi = data?.sections.stock.storage_occupation_rate;
  const wipOccupancyKpi = data?.sections.stock.wip_occupation_rate;

  const stockLevel = kpiValue(averageStockLevel);
  const storageOccupancy = kpiValue(storageOccupancyKpi);
  const encoursOccupancy = kpiValue(wipOccupancyKpi);
  const stockEvolutionData =
    data?.details.stock.stock_evolution?.length ? data.details.stock.stock_evolution : stockEvolution;
  const zoneOccupancyData =
    data?.details.stock.zone_occupancy?.length ? data.details.stock.zone_occupancy : zoneOccupancy;

  return (
    <div className="p-6 space-y-6">
      {/* KPIs - 3 indicateurs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* KPI 1: Niveau moyen de stock (KPI clé) */}
        <div className="bg-card rounded-xl border border-l-4 border-l-kpi-stock p-5">
          <div className="flex items-center gap-2 mb-3">
            <Package className="w-5 h-5 text-kpi-stock" />
            <span className="text-xs text-muted-foreground font-medium uppercase tracking-wide">KPI Clé</span>
          </div>
          <p className="text-4xl font-bold text-success">{formatKpiValue(averageStockLevel)}</p>
          <p className="text-sm text-muted-foreground mt-1">Niveau moyen de stock</p>
          <div className="flex items-center gap-1 mt-3 text-xs text-success">
            <TrendingUp className="w-3 h-3" />
            <span>{compareToTargetText(averageStockLevel)}</span>
          </div>
        </div>

        {/* KPI 2: Taux d'occupation du stockage */}
        <div className="bg-card rounded-xl border p-5">
          <div className="flex items-center gap-2 mb-3">
            <Warehouse className="w-5 h-5 text-warning" />
            <span className="text-xs text-muted-foreground font-medium uppercase tracking-wide">Stockage</span>
          </div>
          <p className="text-4xl font-bold text-warning">{formatKpiValue(storageOccupancyKpi)}</p>
          <p className="text-sm text-muted-foreground mt-1">Taux d'occupation du stockage</p>
          <div className="mt-3">
            <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
              <div className="h-full bg-warning rounded-full transition-all" style={{ width: `${storageOccupancy}%` }} />
            </div>
            <p className="text-xs text-muted-foreground mt-1">{compareToTargetText(storageOccupancyKpi)}</p>
          </div>
        </div>

        {/* KPI 3: Taux d'occupation des encours */}
        <div className="bg-card rounded-xl border p-5">
          <div className="flex items-center gap-2 mb-3">
            <Settings className="w-5 h-5 text-success" />
            <span className="text-xs text-muted-foreground font-medium uppercase tracking-wide">Encours</span>
          </div>
          <p className="text-4xl font-bold text-success">{formatKpiValue(wipOccupancyKpi)}</p>
          <p className="text-sm text-muted-foreground mt-1">Taux d'occupation des encours</p>
          <div className="mt-3">
            <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
              <div className="h-full bg-success rounded-full transition-all" style={{ width: `${encoursOccupancy}%` }} />
            </div>
            <p className="text-xs text-muted-foreground mt-1">{compareToTargetText(wipOccupancyKpi)}</p>
          </div>
        </div>
      </div>

      {/* Graphiques */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Jauge niveau de stock + évolution */}
        <div className="bg-card rounded-xl border p-5">
          <h3 className="text-sm font-medium mb-4">Niveau de stock</h3>
          <div className="flex items-center gap-6">
            <GaugeChart 
              value={Math.min(stockLevel, 100)} 
              size={140}
              thresholds={{ warning: 70, danger: 50 }}
            />
            <div className="flex-1 h-32">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={stockEvolutionData}>
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis hide domain={[70, 100]} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'hsl(var(--card))', 
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                      fontSize: '12px'
                    }} 
                  />
                  <Area 
                    type="monotone" 
                    dataKey="value" 
                    stroke="hsl(var(--kpi-stock))"
                    fill="hsl(var(--kpi-stock) / 0.2)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
          <p className="text-xs text-muted-foreground text-center mt-2">Évolution hebdomadaire</p>
        </div>

        {/* Occupation par zone */}
        <div className="bg-card rounded-xl border p-5">
          <h3 className="text-sm font-medium mb-4">Occupation par zone</h3>
          <div className="h-44">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={zoneOccupancyData} layout="vertical">
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="zone" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} width={60} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--card))', 
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                    fontSize: '12px'
                  }} 
                />
                <Bar dataKey="stockage" fill="hsl(var(--kpi-stock))" name="Stockage" radius={[0, 4, 4, 0]} />
                <Bar dataKey="encours" fill="hsl(var(--chart-3))" name="Encours" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center justify-center gap-6 mt-2 text-xs">
            <span className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-kpi-stock" />
              Stockage
            </span>
            <span className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-chart-3" />
              Encours
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
