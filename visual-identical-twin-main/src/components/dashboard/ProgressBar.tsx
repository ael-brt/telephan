import { cn } from "@/lib/utils";

interface ProgressBarProps {
  value: number;
  max?: number;
  label?: string;
  showValue?: boolean;
  color?: "primary" | "success" | "warning" | "danger";
  size?: "sm" | "md" | "lg";
  className?: string;
}

export const ProgressBar = ({
  value,
  max = 100,
  label,
  showValue = true,
  color = "primary",
  size = "md",
  className,
}: ProgressBarProps) => {
  const percentage = Math.min((value / max) * 100, 100);
  
  const colorClasses = {
    primary: "bg-primary",
    success: "bg-success",
    warning: "bg-warning",
    danger: "bg-destructive",
  };
  
  const sizeClasses = {
    sm: "h-1.5",
    md: "h-2",
    lg: "h-3",
  };

  return (
    <div className={cn("space-y-1", className)}>
      {(label || showValue) && (
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>{label}</span>
          {showValue && <span>{percentage.toFixed(0)}%</span>}
        </div>
      )}
      <div className={cn("progress-bar", sizeClasses[size])}>
        <div
          className={cn("progress-bar-fill", colorClasses[color])}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};
