import { 
  Factory, 
  ClipboardCheck, 
  Package, 
  Truck, 
  Zap, 
  Wrench,
  AlertTriangle
} from "lucide-react";
import { useDashboardSummary } from "@/hooks/use-dashboard-summary";
import { formatKpiValue } from "@/lib/kpi-format";
import { cn } from "@/lib/utils";

interface OverviewTabProps {
  onNavigateToTab: (tab: string) => void;
}

// Simple card component for overview - only shows KPI clé
interface KPIKeyCardProps {
  title: string;
  icon: React.ElementType;
  status: "success" | "warning" | "danger" | "unknown";
  kpiValue: string;
  kpiLabel: string;
  colorClass: string;
  onClick: () => void;
}

const KPIKeyCard = ({ title, icon: Icon, status, kpiValue, kpiLabel, colorClass, onClick }: KPIKeyCardProps) => {
  const statusColors = {
    success: "bg-success",
    warning: "bg-warning",
    danger: "bg-destructive",
    unknown: "bg-muted-foreground",
  };

  const statusTextColors = {
    success: "text-success",
    warning: "text-warning",
    danger: "text-destructive",
    unknown: "text-muted-foreground",
  };

  return (
    <div
      onClick={onClick}
      className={cn(
        "bg-card rounded-lg border border-l-4 p-6 cursor-pointer transition-all duration-200",
        "hover:shadow-lg hover:scale-[1.02] hover:border-primary/50",
        colorClass
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-muted">
            <Icon className="w-5 h-5 text-foreground" />
          </div>
          <h3 className="font-semibold text-foreground">{title}</h3>
        </div>
        <div className={cn("w-4 h-4 rounded-full animate-pulse", statusColors[status])} />
      </div>

      {/* Main KPI clé */}
      <div className="text-center py-6 bg-muted/50 rounded-lg">
        <p className={cn("text-4xl font-bold", statusTextColors[status])}>{kpiValue}</p>
        <p className="text-sm text-muted-foreground mt-2">{kpiLabel}</p>
      </div>

      {/* Click hint */}
      <div className="mt-4 text-center">
        <span className="text-xs text-muted-foreground">Cliquer pour plus de détails →</span>
      </div>
    </div>
  );
};

export const OverviewTab = ({ onNavigateToTab }: OverviewTabProps) => {
  const { data, isError } = useDashboardSummary();
  const overview = data?.sections.overview;

  const kpiData = {
    performance: {
      status: overview?.performance?.status ?? "unknown",
      kpiValue: formatKpiValue(overview?.performance?.data),
      kpiLabel: overview?.performance?.data?.label ?? "Taux d'utilisation des machines",
      colorClass: "border-l-kpi-performance",
    },
    quality: {
      status: overview?.quality?.status ?? "unknown",
      kpiValue: formatKpiValue(overview?.quality?.data),
      kpiLabel: overview?.quality?.data?.label ?? "Taux de non-conformité",
      colorClass: "border-l-kpi-quality",
    },
    stock: {
      status: overview?.stock?.status ?? "unknown",
      kpiValue: formatKpiValue(overview?.stock?.data),
      kpiLabel: overview?.stock?.data?.label ?? "Niveau moyen de stock",
      colorClass: "border-l-kpi-stock",
    },
    delay: {
      status: overview?.delay?.status ?? "unknown",
      kpiValue: formatKpiValue(overview?.delay?.data, { unitOverride: "min" }),
      kpiLabel: overview?.delay?.data?.label ?? "Lead Time global",
      colorClass: "border-l-kpi-delay",
    },
    energy: {
      status: overview?.energy?.status ?? "unknown",
      kpiValue: formatKpiValue(overview?.energy?.data),
      kpiLabel: overview?.energy?.data?.label ?? "Consommation énergétique moyenne",
      colorClass: "border-l-kpi-energy",
    },
    maintenance: {
      status: overview?.maintenance?.status ?? "unknown",
      kpiValue: formatKpiValue(overview?.maintenance?.data),
      kpiLabel: overview?.maintenance?.data?.label ?? "Nombre d'erreurs critiques",
      colorClass: "border-l-kpi-maintenance",
    },
  };

  const getAlertCount = () => {
    let count = 0;
    Object.values(kpiData).forEach((section) => {
      if (section.status === "danger") count += 2;
      if (section.status === "warning") count += 1;
    });
    return count;
  };

  const alertCount = getAlertCount();

  return (
    <div className="p-6 space-y-6">
      {isError && (
        <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
          <p className="text-sm text-destructive">
            Impossible de charger les KPI temps réel depuis le backend.
          </p>
        </div>
      )}

      {/* Alert Banner */}
      {alertCount > 0 && (
        <div className="bg-warning/10 border border-warning/30 rounded-lg p-4 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-warning" />
          <div>
            <p className="font-medium text-foreground">
              {alertCount} alerte{alertCount > 1 ? "s" : ""} nécessitant votre attention
            </p>
            <p className="text-sm text-muted-foreground">
              Cliquez sur les sections concernées pour plus de détails
            </p>
          </div>
        </div>
      )}

      {/* Status Legend */}
      <div className="flex items-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-success" />
          <span className="text-muted-foreground">Conforme</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-warning" />
          <span className="text-muted-foreground">Attention requise</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-destructive" />
          <span className="text-muted-foreground">Critique</span>
        </div>
      </div>

      {/* 6 KPI Cards Grid - One per bloc */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <KPIKeyCard
          title="PERFORMANCE"
          icon={Factory}
          status={kpiData.performance.status}
          kpiValue={kpiData.performance.kpiValue}
          kpiLabel={kpiData.performance.kpiLabel}
          colorClass={kpiData.performance.colorClass}
          onClick={() => onNavigateToTab("performance")}
        />

        <KPIKeyCard
          title="QUALITÉ"
          icon={ClipboardCheck}
          status={kpiData.quality.status}
          kpiValue={kpiData.quality.kpiValue}
          kpiLabel={kpiData.quality.kpiLabel}
          colorClass={kpiData.quality.colorClass}
          onClick={() => onNavigateToTab("quality")}
        />

        <KPIKeyCard
          title="STOCK"
          icon={Package}
          status={kpiData.stock.status}
          kpiValue={kpiData.stock.kpiValue}
          kpiLabel={kpiData.stock.kpiLabel}
          colorClass={kpiData.stock.colorClass}
          onClick={() => onNavigateToTab("stock")}
        />

        <KPIKeyCard
          title="DÉLAI"
          icon={Truck}
          status={kpiData.delay.status}
          kpiValue={kpiData.delay.kpiValue}
          kpiLabel={kpiData.delay.kpiLabel}
          colorClass={kpiData.delay.colorClass}
          onClick={() => onNavigateToTab("delay")}
        />

        <KPIKeyCard
          title="ÉNERGIE"
          icon={Zap}
          status={kpiData.energy.status}
          kpiValue={kpiData.energy.kpiValue}
          kpiLabel={kpiData.energy.kpiLabel}
          colorClass={kpiData.energy.colorClass}
          onClick={() => onNavigateToTab("energy")}
        />

        <KPIKeyCard
          title="MAINTENANCE"
          icon={Wrench}
          status={kpiData.maintenance.status}
          kpiValue={kpiData.maintenance.kpiValue}
          kpiLabel={kpiData.maintenance.kpiLabel}
          colorClass={kpiData.maintenance.colorClass}
          onClick={() => onNavigateToTab("maintenance")}
        />
      </div>

      {data?.generated_at && (
        <p className="text-xs text-muted-foreground">
          Source: {data.data_source === "telephan_warehouse" ? "Schéma TELEPHAN (facts/dimensions)" : "Backend Django/MES"}{" "}
          {data.anchor_date ? `• ancre ${data.anchor_date}` : ""} • mise à jour {new Date(data.generated_at).toLocaleString("fr-FR")}
        </p>
      )}
    </div>
  );
};
