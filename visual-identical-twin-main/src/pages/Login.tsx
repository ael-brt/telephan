import { FormEvent, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { User, Lock, Eye, EyeOff } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { ensureLoginCsrf, getCsrfToken } from "@/lib/auth";

function normalizeNext(next: string | null): string {
  if (!next || !next.startsWith("/")) return "/";
  if (next.startsWith("//")) return "/";
  return next;
}

const LoginPage = () => {
  const [searchParams] = useSearchParams();
  const nextPath = useMemo(() => normalizeNext(searchParams.get("next")), [searchParams]);

  const [showPassword, setShowPassword] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    void ensureLoginCsrf(nextPath);
  }, [nextPath]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      await ensureLoginCsrf(nextPath);
      const csrfToken = getCsrfToken();

      const body = new URLSearchParams();
      body.set("username", username);
      body.set("password", password);
      body.set("next", nextPath);
      if (rememberMe) {
        body.set("remember_me", "1");
      }
      if (csrfToken) {
        body.set("csrfmiddlewaretoken", csrfToken);
      }

      await fetch("/accounts/login/", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          Accept: "text/html,application/xhtml+xml",
          ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
        },
        body: body.toString(),
      });

      const verify = await fetch("/api/dashboard/summary/", {
        headers: { Accept: "application/json" },
        credentials: "include",
      });

      if (verify.status === 401) {
        setErrorMessage("Identifiants invalides. Vérifie ton nom d'utilisateur et ton mot de passe.");
        return;
      }

      if (!verify.ok) {
        setErrorMessage("Connexion effectuée, mais le dashboard est momentanément indisponible.");
        return;
      }

      window.location.href = nextPath;
    } catch {
      setErrorMessage("Impossible de se connecter pour le moment. Réessaie dans quelques secondes.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-primary/10 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-card rounded-xl shadow-xl p-8 animate-fade-in">
          <div className="flex items-center justify-center gap-2 mb-8">
            <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center text-primary-foreground font-bold text-xl">
              T
            </div>
            <span className="text-2xl font-bold text-primary">Téléphan</span>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <input type="hidden" name="next" value={nextPath} readOnly />

            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Nom d'utilisateur"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="pl-10 h-12"
                autoComplete="username"
                required
              />
            </div>

            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <Input
                type={showPassword ? "text" : "password"}
                placeholder="Mot de passe"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pl-10 pr-10 h-12"
                autoComplete="current-password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                aria-label={showPassword ? "Masquer le mot de passe" : "Afficher le mot de passe"}
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>

            {errorMessage ? (
              <p className="text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-md px-3 py-2">
                {errorMessage}
              </p>
            ) : null}

            <Button type="submit" className="w-full h-12 text-base font-medium" disabled={isSubmitting}>
              {isSubmitting ? "Connexion..." : "Se connecter"}
            </Button>

            <div className="flex items-center gap-2">
              <Checkbox
                id="remember"
                checked={rememberMe}
                onCheckedChange={(checked) => setRememberMe(checked === true)}
              />
              <label htmlFor="remember" className="text-sm text-muted-foreground cursor-pointer">
                Se souvenir de moi
              </label>
            </div>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-muted-foreground">
              Besoin d'aide ?{" "}
              <a href="#" className="text-primary hover:underline">
                Contactez le support technique.
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;

