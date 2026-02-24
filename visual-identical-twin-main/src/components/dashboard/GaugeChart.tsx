import { useMemo } from "react";

interface GaugeChartProps {
  value: number;
  max?: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
  showPercentage?: boolean;
  color?: "primary" | "success" | "warning" | "danger";
  thresholds?: { warning: number; danger: number };
}

export const GaugeChart = ({
  value,
  max = 100,
  size = 120,
  strokeWidth = 10,
  label,
  showPercentage = true,
  color,
  thresholds = { warning: 70, danger: 40 },
}: GaugeChartProps) => {
  const percentage = Math.min((value / max) * 100, 100);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  
  // Calculate arc (270 degrees = 3/4 of circle)
  const arcLength = circumference * 0.75;
  const offset = arcLength - (arcLength * percentage) / 100;
  
  const gaugeColor = useMemo(() => {
    if (color) {
      switch (color) {
        case "primary": return "hsl(var(--primary))";
        case "success": return "hsl(var(--success))";
        case "warning": return "hsl(var(--warning))";
        case "danger": return "hsl(var(--destructive))";
      }
    }
    // Auto-color based on thresholds
    if (percentage < thresholds.danger) return "hsl(var(--destructive))";
    if (percentage < thresholds.warning) return "hsl(var(--warning))";
    return "hsl(var(--success))";
  }, [color, percentage, thresholds]);

  return (
    <div className="gauge-container" style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="transform -rotate-[135deg]"
      >
        {/* Background arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="hsl(var(--gauge-background))"
          strokeWidth={strokeWidth}
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeLinecap="round"
        />
        {/* Value arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={gaugeColor}
          strokeWidth={strokeWidth}
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center pt-2">
        <span className="text-2xl font-bold text-foreground">
          {showPercentage ? `${value.toFixed(1)}%` : value}
        </span>
        {label && (
          <span className="text-xs text-muted-foreground mt-1">{label}</span>
        )}
      </div>
    </div>
  );
};
