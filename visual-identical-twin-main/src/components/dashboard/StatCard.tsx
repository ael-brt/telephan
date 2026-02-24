import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  children: ReactNode;
  className?: string;
  footer?: ReactNode;
  headerAction?: ReactNode;
}

export const StatCard = ({ title, children, className, footer, headerAction }: StatCardProps) => {
  return (
    <div className={cn("bg-card rounded-lg border shadow-card p-4 animate-slide-up", className)}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
        {headerAction}
      </div>
      <div className="space-y-3">
        {children}
      </div>
      {footer && (
        <div className="mt-3 pt-3 border-t text-xs text-muted-foreground">
          {footer}
        </div>
      )}
    </div>
  );
};
