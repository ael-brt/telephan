import { useLocation, Link } from "react-router-dom";
import { useEffect } from "react";
import { Home, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/Logo";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error("404 Error: User attempted to access non-existent route:", location.pathname);
  }, [location.pathname]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-center px-6">
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <Logo size="lg" />
        </div>

        {/* 404 Error */}
        <div className="mb-6">
          <h1 className="text-8xl font-bold text-primary mb-2">404</h1>
          <p className="text-2xl font-semibold text-foreground mb-2">Page non trouvée</p>
          <p className="text-muted-foreground max-w-md mx-auto">
            La page que vous recherchez n'existe pas ou a été déplacée.
          </p>
        </div>

        {/* Path info */}
        <div className="bg-muted rounded-lg px-4 py-2 mb-8 inline-block">
          <code className="text-sm text-muted-foreground">
            {location.pathname}
          </code>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Button asChild size="lg" className="gap-2">
            <Link to="/">
              <Home className="w-4 h-4" />
              Retour à l'accueil
            </Link>
          </Button>
          <Button 
            variant="outline" 
            size="lg" 
            className="gap-2"
            onClick={() => window.history.back()}
          >
            <ArrowLeft className="w-4 h-4" />
            Page précédente
          </Button>
        </div>

        {/* Footer */}
        <p className="text-xs text-muted-foreground mt-12">
          © 2024 Téléphan Industries — Tableau de Bord Industriel
        </p>
      </div>
    </div>
  );
};

export default NotFound;
