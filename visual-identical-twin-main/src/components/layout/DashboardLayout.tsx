import { ReactNode } from "react";
import { TopHeader } from "./TopHeader";
import { LeftSidebar } from "./LeftSidebar";

interface DashboardLayoutProps {
  children: ReactNode;
  onLogout: () => void;
}

export const DashboardLayout = ({ children, onLogout }: DashboardLayoutProps) => {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Bandeau Haut */}
      <TopHeader onLogout={onLogout} />
      
      <div className="flex flex-1 overflow-hidden">
        {/* Bandeau Gauche */}
        <LeftSidebar />
        
        {/* Tableau de Bord (Main Content) */}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
};
