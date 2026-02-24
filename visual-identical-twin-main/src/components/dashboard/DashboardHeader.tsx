import { Bell } from "lucide-react";

interface DashboardHeaderProps {
  title: string;
  subtitle?: string;
  lastUpdate?: string;
}

export const DashboardHeader = ({ title, subtitle, lastUpdate }: DashboardHeaderProps) => {
  return (
    <header className="dashboard-header px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary-foreground/20 rounded-md flex items-center justify-center font-bold text-lg">
            T
          </div>
          <span className="font-semibold text-lg">Téléphan</span>
        </div>
        <div className="h-6 w-px bg-primary-foreground/30" />
        <div>
          <h1 className="font-semibold">{title}</h1>
          {subtitle && <p className="text-sm text-primary-foreground/70">{subtitle}</p>}
        </div>
      </div>
      
      <div className="flex items-center gap-4">
        {lastUpdate && (
          <span className="text-sm text-primary-foreground/70">
            Dernière mise à jour : {lastUpdate}
          </span>
        )}
        <button className="p-2 rounded-md hover:bg-primary-foreground/10 transition-colors">
          <Bell className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
};
