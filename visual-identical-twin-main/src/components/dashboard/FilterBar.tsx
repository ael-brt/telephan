import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Calendar, Clock, Settings, Package, Database, AlertTriangle } from "lucide-react";

const filters = [
  { 
    id: "temporal", 
    label: "Période",
    icon: Calendar,
    options: [
      { value: "today", label: "Aujourd'hui" },
      { value: "this-week", label: "Cette semaine" },
      { value: "this-month", label: "Ce mois" },
    ]
  },
  { 
    id: "shift", 
    label: "Shift",
    icon: Clock,
    options: [
      { value: "all", label: "Tous" },
      { value: "shift-a", label: "Shift A" },
      { value: "shift-b", label: "Shift B" },
      { value: "shift-c", label: "Shift C" },
    ]
  },
  { 
    id: "machine", 
    label: "Machine",
    icon: Settings,
    options: [
      { value: "all", label: "Toutes" },
      { value: "poste-vissage", label: "Poste vissage" },
      { value: "station-soudure", label: "Station soudure" },
      { value: "robot-cellulaire", label: "Robot" },
    ]
  },
  { 
    id: "product", 
    label: "Produit",
    icon: Package,
    options: [
      { value: "all", label: "Tous" },
      { value: "ph-203n", label: "PH-203N" },
      { value: "ph-104n", label: "PH-104N" },
      { value: "ph-402t", label: "PH-402T" },
    ]
  },
  { 
    id: "of", 
    label: "OF",
    icon: Database,
    options: [
      { value: "all", label: "Tous" },
      { value: "of-210108", label: "OF-210108" },
      { value: "of-210091", label: "OF-210091" },
    ]
  },
  { 
    id: "error-type", 
    label: "Type erreur",
    icon: AlertTriangle,
    options: [
      { value: "all", label: "Tous" },
      { value: "capteur", label: "Capteur" },
      { value: "robot", label: "Robot" },
      { value: "cnc", label: "CNC" },
    ]
  },
];

export const FilterBar = () => {
  return (
    <div className="bg-card border-b px-6 py-3 flex items-center gap-3 flex-wrap">
      {filters.map((filter) => (
        <div key={filter.id} className="flex items-center gap-1.5">
          <filter.icon className="w-3.5 h-3.5 text-muted-foreground" />
          <Select defaultValue={filter.options[0].value}>
            <SelectTrigger className="h-8 w-auto min-w-[90px] text-sm bg-background">
              <SelectValue placeholder={filter.label} />
            </SelectTrigger>
            <SelectContent>
              {filter.options.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      ))}
    </div>
  );
};
