import { LogOut, Bell } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/Logo";

interface TopHeaderProps {
  onLogout: () => void;
}

export const TopHeader = ({ onLogout }: TopHeaderProps) => {
  return (
    <header className="h-14 bg-primary text-primary-foreground px-6 flex items-center justify-between border-b border-primary/20">
      {/* Logo & Navigation */}
      <div className="flex items-center gap-6">
        <Logo size="md" className="[&_span]:text-primary-foreground [&_svg_rect]:fill-primary-foreground/20 [&_svg_path]:fill-primary-foreground" />
        
        <nav className="hidden md:flex items-center gap-4 ml-4">
          <span className="text-sm text-primary-foreground/70">
            Tableau de Bord Industriel
          </span>
        </nav>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-primary-foreground/70 hidden sm:block">
          Dernière mise à jour : Il y a 5 min
        </span>
        
        <Button 
          variant="ghost" 
          size="icon"
          className="text-primary-foreground hover:bg-primary-foreground/10"
        >
          <Bell className="w-5 h-5" />
        </Button>
        
        <Button 
          variant="outline" 
          size="sm"
          onClick={onLogout}
          className="bg-transparent border-primary-foreground/30 text-primary-foreground hover:bg-primary-foreground/10 hover:text-primary-foreground gap-2"
        >
          <LogOut className="w-4 h-4" />
          <span className="hidden sm:inline">Déconnexion</span>
        </Button>
      </div>
    </header>
  );
};
