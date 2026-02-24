import { ReactNode } from "react";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  trend?: {
    value: string;
    direction: "up" | "down" | "neutral";
  };
  variant?: "performance" | "quality" | "stock" | "delay" | "energy" | "maintenance";
  children?: ReactNode;
  className?: string;
}

export const KPICard = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  variant = "performance",
  children,
  className,
}: KPICardProps) => {
  const variantClasses = {
    performance: "kpi-card-performance",
    quality: "kpi-card-quality",
    stock: "kpi-card-stock",
    delay: "kpi-card-delay",
    energy: "kpi-card-energy",
    maintenance: "border-l-4 border-l-kpi-maintenance",
  };

  const trendColors = {
    up: "text-success",
    down: "text-destructive",
    neutral: "text-muted-foreground",
  };

  return (
    <div className={cn("kpi-card animate-fade-in", variantClasses[variant], className)}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          {Icon && (
            <div className="p-1.5 rounded-md bg-muted">
              <Icon className="w-4 h-4 text-muted-foreground" />
            </div>
          )}
          <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
        </div>
        {trend && (
          <span className={cn("text-xs font-medium", trendColors[trend.direction])}>
            {trend.direction === "up" ? "↑" : trend.direction === "down" ? "↓" : "→"} {trend.value}
          </span>
        )}
      </div>
      
      <div className="flex items-end justify-between">
        <div>
          <p className="text-2xl font-bold text-foreground">{value}</p>
          {subtitle && (
            <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
          )}
        </div>
        {children}
      </div>
    </div>
  );
};
