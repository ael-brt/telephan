import { useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { TabNavigation } from "@/components/dashboard/TabNavigation";
import { OverviewTab } from "@/components/dashboard/tabs/OverviewTab";
import { PerformanceTab } from "@/components/dashboard/tabs/PerformanceTab";
import { QualityTab } from "@/components/dashboard/tabs/QualityTab";
import { StockTab } from "@/components/dashboard/tabs/StockTab";
import { DelayTab } from "@/components/dashboard/tabs/DelayTab";
import { EnergyTab } from "@/components/dashboard/tabs/EnergyTab";
import { MaintenanceTab } from "@/components/dashboard/tabs/MaintenanceTab";
import { submitLogout } from "@/lib/auth";
import { DashboardFiltersProvider } from "@/lib/dashboard-filters";

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState("overview");

  const renderTabContent = () => {
    switch (activeTab) {
      case "overview":
        return <OverviewTab onNavigateToTab={setActiveTab} />;
      case "performance":
        return <PerformanceTab />;
      case "quality":
        return <QualityTab />;
      case "stock":
        return <StockTab />;
      case "delay":
        return <DelayTab />;
      case "energy":
        return <EnergyTab />;
      case "maintenance":
        return <MaintenanceTab />;
      default:
        return <OverviewTab onNavigateToTab={setActiveTab} />;
    }
  };

  const getTitle = () => {
    const titles: Record<string, string> = {
      overview: "VUE GÉNÉRALE",
      performance: "PERFORMANCE",
      quality: "QUALITÉ",
      stock: "STOCK",
      delay: "DÉLAI",
      energy: "ÉNERGIE",
      maintenance: "MAINTENANCE",
    };
    return titles[activeTab] || "Production";
  };

  return (
    <DashboardFiltersProvider>
      <DashboardLayout onLogout={() => submitLogout("/")}>
        {/* Tab Title */}
        <div className="bg-card border-b px-6 py-4">
          <h1 className="text-xl font-bold text-foreground">
            Tableau de Bord - {getTitle()}
          </h1>
        </div>

        {/* Tab Navigation */}
        <TabNavigation activeTab={activeTab} onTabChange={setActiveTab} />
        
        {/* Tab Content */}
        <div className="animate-fade-in">
          {renderTabContent()}
        </div>
      </DashboardLayout>
    </DashboardFiltersProvider>
  );
};

export default Dashboard;
