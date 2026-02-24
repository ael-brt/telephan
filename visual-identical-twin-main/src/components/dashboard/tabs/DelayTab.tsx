import { Truck, TrendingDown, CheckCircle } from "lucide-react";
import { GaugeChart } from "../GaugeChart";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, BarChart, Bar, Tooltip, ReferenceLine } from "recharts";
import { useDashboardSummary } from "@/hooks/use-dashboard-summary";
import { compareToTargetText, formatKpiValue, kpiTarget, kpiValue } from "@/lib/kpi-format";

// Données pour les graphiques
const otdEvolution = [
  { day: "Lun", value: 94.5 },
  { day: "Mar", value: 89.2 },
  { day: "Mer", value: 91.8 },
  { day: "Jeu", value: 88.5 },
  { day: "Ven", value: 93.1 },
  { day: "Sam", value: 95.2 },
  { day: "Dim", value: 92.1 },
];

const leadTimeByProduct = [
  { product: "PH-203N", leadTime: 3.8 },
  { product: "PH-104N", leadTime: 4.2 },
  { product: "PH-402T", leadTime: 5.1 },
  { product: "PH-301S", leadTime: 3.5 },
];

export const DelayTab = () => {
  const { data } = useDashboardSummary();
  const leadTime = data?.sections.delay.global_lead_time;
  const otd = data?.sections.delay.otd;
  const otdRate = kpiValue(otd);
  const otdTarget = kpiTarget(otd, 95);
  const otdEvolutionData = data?.details.delay.otd_evolution?.length ? data.details.delay.otd_evolution : otdEvolution;
  const leadTimeByOrderData =
    data?.details.delay.lead_time_by_product?.length ? data.details.delay.lead_time_by_product : leadTimeByProduct;

  return (
    <div className="p-6 space-y-6">
      {/* KPIs - 2 indicateurs */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* KPI 1: Lead Time global par produit (KPI clé) */}
        <div className="bg-card rounded-xl border border-l-4 border-l-kpi-delay p-5">
          <div className="flex items-center gap-2 mb-3">
            <Truck className="w-5 h-5 text-kpi-delay" />
            <span className="text-xs text-muted-foreground font-medium uppercase tracking-wide">KPI Clé</span>
          </div>
          <p className="text-4xl font-bold text-success">{formatKpiValue(leadTime)}</p>
          <p className="text-sm text-muted-foreground mt-1">Lead Time global</p>
          <div className="flex items-center gap-1 mt-3 text-xs text-success">
            <TrendingDown className="w-3 h-3" />
            <span>{compareToTargetText(leadTime)}</span>
          </div>
        </div>

        {/* KPI 2: OTD */}
        <div className="bg-card rounded-xl border p-5">
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle className="w-5 h-5 text-warning" />
            <span className="text-xs text-muted-foreground font-medium uppercase tracking-wide">Livraison</span>
          </div>
          <p className="text-4xl font-bold text-warning">{formatKpiValue(otd)}</p>
          <p className="text-sm text-muted-foreground mt-1">OTD (Livraison dans les temps)</p>
          <div className="mt-3">
            <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
              <div className="h-full bg-warning rounded-full transition-all" style={{ width: `${otdRate}%` }} />
            </div>
            <p className="text-xs text-muted-foreground mt-1">Objectif: {otdTarget}%</p>
          </div>
        </div>
      </div>

      {/* Graphiques */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* OTD Jauge + Évolution */}
        <div className="bg-card rounded-xl border p-5">
          <h3 className="text-sm font-medium mb-4">OTD - On Time Delivery</h3>
          <div className="flex items-center gap-6">
            <GaugeChart 
              value={otdRate} 
              size={140}
              thresholds={{ warning: 90, danger: 80 }}
            />
            <div className="flex-1 h-32">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={otdEvolutionData}>
                  <XAxis dataKey="day" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis hide domain={[80, 100]} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'hsl(var(--card))', 
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                      fontSize: '12px'
                    }} 
                  />
                  <ReferenceLine y={otdTarget} stroke="hsl(var(--muted-foreground))" strokeDasharray="3 3" />
                  <Line 
                    type="monotone" 
                    dataKey="value" 
                    stroke="hsl(var(--kpi-delay))" 
                    strokeWidth={2}
                    dot={{ fill: "hsl(var(--kpi-delay))", r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
          <p className="text-xs text-muted-foreground text-center mt-2">Évolution hebdomadaire</p>
        </div>

        {/* Lead Time par produit */}
        <div className="bg-card rounded-xl border p-5">
          <h3 className="text-sm font-medium mb-4">Lead Time par ordre</h3>
          <div className="h-44">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={leadTimeByOrderData}>
                <XAxis dataKey="product" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--card))', 
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                    fontSize: '12px'
                  }} 
                />
                <ReferenceLine y={4.5} stroke="hsl(var(--muted-foreground))" strokeDasharray="3 3" />
                <Bar 
                  dataKey="leadTime" 
                  fill="hsl(var(--kpi-delay))" 
                  radius={[4, 4, 0, 0]}
                  name="Lead Time"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center justify-center gap-6 mt-2 text-xs">
            <span className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-kpi-delay" />
              Lead Time
            </span>
            <span className="text-muted-foreground">{compareToTargetText(leadTime)}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
