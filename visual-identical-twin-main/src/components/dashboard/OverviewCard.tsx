import { ReactNode } from "react";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface OverviewCardProps {
  title: string;
  icon: LucideIcon;
  status: "success" | "warning" | "danger";
  mainValue: string;
  mainLabel: string;
  indicators: {
    label: string;
    value: string;
    status?: "success" | "warning" | "danger";
  }[];
  onClick: () => void;
  children?: ReactNode;
}

export const OverviewCard = ({
  title,
  icon: Icon,
  status,
  mainValue,
  mainLabel,
  indicators,
  onClick,
  children,
}: OverviewCardProps) => {
  const statusColors = {
    success: "bg-success",
    warning: "bg-warning",
    danger: "bg-destructive",
  };

  const statusBorderColors = {
    success: "border-l-success",
    warning: "border-l-warning",
    danger: "border-l-destructive",
  };

  const statusTextColors = {
    success: "text-success",
    warning: "text-warning",
    danger: "text-destructive",
  };

  return (
    <div
      onClick={onClick}
      className={cn(
        "bg-card rounded-lg border border-l-4 p-4 cursor-pointer transition-all duration-200",
        "hover:shadow-lg hover:scale-[1.02] hover:border-primary/50",
        statusBorderColors[status]
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

      {/* Main KPI */}
      <div className="text-center mb-4 py-3 bg-muted/50 rounded-lg">
        <p className={cn("text-3xl font-bold", statusTextColors[status])}>{mainValue}</p>
        <p className="text-sm text-muted-foreground mt-1">{mainLabel}</p>
      </div>

      {/* Secondary Indicators */}
      <div className="space-y-2">
        {indicators.map((indicator, idx) => (
          <div key={idx} className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">{indicator.label}</span>
            <span className={cn(
              "font-medium",
              indicator.status ? statusTextColors[indicator.status] : "text-foreground"
            )}>
              {indicator.value}
            </span>
          </div>
        ))}
      </div>

      {children}

      {/* Click hint */}
      <div className="mt-4 pt-3 border-t border-border text-center">
        <span className="text-xs text-muted-foreground">Cliquer pour plus de détails →</span>
      </div>
    </div>
  );
};
