import { Calendar, Clock, Settings, Filter, Database, Link as LinkIcon, Package, AlertTriangle } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { useDashboardSummary } from "@/hooks/use-dashboard-summary";
import { useDashboardFilters } from "@/lib/dashboard-filters";

const filters = [
  { 
    id: "temporal", 
    label: "Filtre Temporel", 
    icon: Calendar,
    options: [
      { value: "all-time", label: "Depuis le début" },
      { value: "today", label: "Aujourd'hui" },
      { value: "yesterday", label: "Hier" },
      { value: "this-week", label: "Cette semaine" },
      { value: "last-week", label: "Semaine dernière" },
      { value: "this-month", label: "Ce mois" },
    ],
    description: "Date / Semaine / Shift"
  },
  { 
    id: "shift", 
    label: "Shift", 
    icon: Clock,
    options: [
      { value: "all", label: "Tous les shifts" },
      { value: "shift-a", label: "Shift A (6h-14h)" },
      { value: "shift-b", label: "Shift B (14h-22h)" },
      { value: "shift-c", label: "Shift C (22h-6h)" },
    ],
    description: "Actualisation temps réel"
  },
  { 
    id: "machine", 
    label: "Machine / Poste de travail", 
    icon: Settings,
    options: [
      { value: "all", label: "Toutes machines" },
      { value: "poste-vissage", label: "Poste de vissage" },
      { value: "station-soudure", label: "Station soudure" },
      { value: "robot-cellulaire", label: "Robot cellulaire" },
      { value: "testeuse-connecteur", label: "Testeuse connecteur" },
      { value: "centre-usinage", label: "Centre usinage" },
    ],
    description: "TRS, Taux utilisation, Erreurs..."
  },
  { 
    id: "product", 
    label: "Produit / Référence", 
    icon: Package,
    options: [
      { value: "all", label: "Tous produits" },
      { value: "ph-203n", label: "PH-203N" },
      { value: "ph-104n", label: "PH-104N" },
      { value: "ph-402t", label: "PH-402T" },
      { value: "ph-301s", label: "PH-301S" },
    ],
    description: "Stock, Lead Time, Qualité..."
  },
  { 
    id: "of", 
    label: "Ordre de Fabrication (OF)", 
    icon: Database,
    options: [
      { value: "all", label: "Tous les OF" },
      { value: "of-210108", label: "OF-210108" },
      { value: "of-210091", label: "OF-210091" },
      { value: "of-210067", label: "OF-210067" },
      { value: "of-210054", label: "OF-210054" },
    ],
    description: "OTD, Lead Time, Exécution"
  },
  { 
    id: "error-type", 
    label: "Type d'erreur / Qualité", 
    icon: AlertTriangle,
    options: [
      { value: "all", label: "Tous types" },
      { value: "capteur", label: "Capteur" },
      { value: "robot", label: "Robot" },
      { value: "cnc", label: "CNC" },
      { value: "surchauffe", label: "Surchauffe" },
      { value: "autre", label: "Autre" },
    ],
    description: "Erreurs, Anomalies, Non-conformité"
  },
];

const dataLinks = [
  { label: "Export données brutes", href: "#export-raw" },
  { label: "API Performance", href: "#api-performance" },
  { label: "Historique maintenance", href: "#maintenance-history" },
  { label: "Rapport qualité", href: "#quality-report" },
];

export const LeftSidebar = () => {
  const { data } = useDashboardSummary();
  const { filters: values, setFilter, resetFilters } = useDashboardFilters();

  const dynamicOptions = {
    machine: data?.filter_options?.machines ?? [{ value: "all", label: "Toutes machines" }],
    product: data?.filter_options?.products ?? [{ value: "all", label: "Tous produits" }],
    of: data?.filter_options?.orders ?? [{ value: "all", label: "Tous les OF" }],
    "error-type": data?.filter_options?.error_types ?? [{ value: "all", label: "Tous types" }],
  } as const;

  const currentValueByFilterId: Record<string, string> = {
    temporal: values.temporal,
    shift: values.shift,
    machine: values.machine,
    product: values.product,
    of: values.of,
    "error-type": values.errorType,
  };

  const handleFilterChange = (filterId: string, nextValue: string) => {
    switch (filterId) {
      case "temporal":
        setFilter("temporal", nextValue);
        break;
      case "shift":
        setFilter("shift", nextValue);
        break;
      case "machine":
        setFilter("machine", nextValue);
        break;
      case "product":
        setFilter("product", nextValue);
        break;
      case "of":
        setFilter("of", nextValue);
        break;
      case "error-type":
        setFilter("errorType", nextValue);
        break;
      default:
        break;
    }
  };

  return (
    <aside className="w-64 bg-sidebar text-sidebar-foreground border-r flex flex-col h-full">
      {/* Filters Section */}
      <div className="p-4 flex-1 overflow-y-auto">
        <h3 className="text-sm font-semibold text-sidebar-foreground/70 uppercase tracking-wider mb-4 flex items-center gap-2">
          <Filter className="w-4 h-4" />
          Filtres
        </h3>

        <Button
          type="button"
          variant="outline"
          size="sm"
          className="mb-4 w-full bg-sidebar-accent border-sidebar-border text-sidebar-foreground hover:bg-sidebar-accent/80"
          onClick={resetFilters}
        >
          Réinitialiser les filtres
        </Button>
        
        <div className="space-y-4">
          {filters.map((filter) => (
            <div key={filter.id} className="space-y-1.5">
              <label className="text-xs font-medium text-sidebar-foreground/80 flex items-center gap-1.5">
                <filter.icon className="w-3.5 h-3.5" />
                {filter.label}
              </label>
              <Select
                value={currentValueByFilterId[filter.id] ?? filter.options[0].value}
                onValueChange={(nextValue) => handleFilterChange(filter.id, nextValue)}
              >
                <SelectTrigger className="h-9 w-full text-sm bg-sidebar-accent border-sidebar-border">
                  <SelectValue placeholder={filter.label} />
                </SelectTrigger>
                <SelectContent>
                  {(dynamicOptions[filter.id as keyof typeof dynamicOptions] ?? filter.options).map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-[10px] text-sidebar-foreground/50 pl-1">{filter.description}</p>
            </div>
          ))}
        </div>

        <Separator className="my-6 bg-sidebar-border" />

        {/* Data Links Section */}
        <h3 className="text-sm font-semibold text-sidebar-foreground/70 uppercase tracking-wider mb-3 flex items-center gap-2">
          <LinkIcon className="w-4 h-4" />
          Sources de données
        </h3>
        
        <div className="space-y-1">
          {dataLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="flex items-center gap-2 px-3 py-2 text-sm rounded-md hover:bg-sidebar-accent transition-colors text-sidebar-foreground/80 hover:text-sidebar-foreground"
            >
              <LinkIcon className="w-3.5 h-3.5" />
              {link.label}
            </a>
          ))}
        </div>
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-sidebar-border bg-sidebar-accent/50">
        <div className="text-xs text-sidebar-foreground/60">
          <p>Version 2.1.0</p>
          <p>© 2024 Téléphan Industries</p>
        </div>
      </div>
    </aside>
  );
};
