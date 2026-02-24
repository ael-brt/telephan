import { cn } from "@/lib/utils";
import { LucideIcon, LayoutDashboard, Factory, ClipboardCheck, Package, Truck, Zap, Wrench } from "lucide-react";

interface Tab {
  id: string;
  label: string;
  icon: LucideIcon;
}

const tabs: Tab[] = [
  { id: "overview", label: "VUE GÉNÉRALE", icon: LayoutDashboard },
  { id: "performance", label: "PERFORMANCE", icon: Factory },
  { id: "quality", label: "QUALITÉ", icon: ClipboardCheck },
  { id: "stock", label: "STOCK", icon: Package },
  { id: "delay", label: "DÉLAI", icon: Truck },
  { id: "energy", label: "ÉNERGIE", icon: Zap },
  { id: "maintenance", label: "MAINTENANCE", icon: Wrench },
];

interface TabNavigationProps {
  activeTab: string;
  onTabChange: (tabId: string) => void;
}

export const TabNavigation = ({ activeTab, onTabChange }: TabNavigationProps) => {
  const getTabColor = (tabId: string) => {
    const colors: Record<string, string> = {
      overview: "text-primary border-primary",
      performance: "text-kpi-performance border-kpi-performance",
      quality: "text-kpi-quality border-kpi-quality",
      stock: "text-kpi-stock border-kpi-stock",
      delay: "text-kpi-delay border-kpi-delay",
      energy: "text-kpi-energy border-kpi-energy",
      maintenance: "text-kpi-maintenance border-kpi-maintenance",
    };
    return colors[tabId] || "text-primary border-primary";
  };

  return (
    <div className="bg-card border-b px-6">
      <div className="flex items-center gap-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={cn(
                "flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2 border-transparent",
                isActive
                  ? getTabColor(tab.id)
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>
    </div>
  );
};
