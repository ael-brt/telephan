import { cn } from "@/lib/utils";

interface MiniBarChartProps {
  data: number[];
  labels?: string[];
  max?: number;
  color?: "primary" | "success" | "warning";
  className?: string;
}

export const MiniBarChart = ({
  data,
  labels = [],
  max,
  color = "primary",
  className,
}: MiniBarChartProps) => {
  const maxValue = max || Math.max(...data);
  
  const colorClasses = {
    primary: "bg-primary",
    success: "bg-success",
    warning: "bg-warning",
  };

  return (
    <div className={cn("flex items-end gap-1 h-16", className)}>
      {data.map((value, idx) => {
        const height = (value / maxValue) * 100;
        return (
          <div key={idx} className="flex flex-col items-center gap-1 flex-1">
            <div
              className={cn(
                "w-full rounded-t transition-all duration-500",
                colorClasses[color]
              )}
              style={{ height: `${height}%`, minHeight: 4 }}
            />
            {labels[idx] && (
              <span className="text-[10px] text-muted-foreground truncate w-full text-center">
                {labels[idx]}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
};
