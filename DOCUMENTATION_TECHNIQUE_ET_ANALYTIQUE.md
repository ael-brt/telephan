# Documentation Technique et Analytique - TELEPHAN Dashboard

## 1) Documentation technique: tester l'application en local (Windows 10 + Python venv)

### 1.1 Objectif
Ce document explique comment lancer et tester TELEPHAN Dashboard sur **Windows 10**, avec un environnement Python isole via **venv**.

L'application contient:
- un backend Django (`qlio_dash`)
- un frontend React/Vite (`visual-identical-twin-main`)
- une base MariaDB via Docker (`docker-compose.yml`)

---

### 1.2 Prerequis Windows 10

Installer:
- Docker Desktop (Windows): https://www.docker.com/products/docker-desktop/
- Python 3 (recommande: 3.12.x 64-bit): https://www.python.org/downloads/windows/
- Node.js LTS + npm: https://nodejs.org/
- Git for Windows: https://git-scm.com/download/win

Versions utilisees dans l'environnement de reference:
- Python: `3.13.3`
- Node: `v22.21.1`

---

### 1.3 Installation et lancement (PowerShell)

#### Option rapide (recommandee)
1. Ouvrir Docker Desktop
2. Depuis l'explorateur Windows, double-cliquer `launch_telephan_windows.bat`

Arret:
- double-cliquer `stop_telephan_windows.bat`

Ou en terminal:
```powershell
cd C:\chemin\vers\telephan
.\launch_telephan_windows.bat
.\stop_telephan_windows.bat
```

#### Option manuelle (etapes detaillees)

#### Etape A - Cloner le projet
```powershell
git clone https://github.com/ael-brt/telephan.git
cd telephan
```

#### Etape B - Configurer `.env`
```powershell
Copy-Item .env.example .env
```

Ensuite, verifier dans `.env`:
- `DB_HOST=127.0.0.1` (important en execution locale Windows)
- `DB_PORT=3306`
- `DWH_SCHEMA=mes_kpi`

#### Etape C - Demarrer la base de donnees
Docker Desktop doit etre demarre.

```powershell
docker compose up -d mariadb
```

Optionnel (interface SQL):
```powershell
docker compose up -d phpmyadmin
```

#### Etape D - Backend Django avec venv
```powershell
cd qlio_dash
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Le backend tourne sur: `http://127.0.0.1:8000`

#### Etape E - Frontend React/Vite (nouveau terminal PowerShell)
```powershell
cd telephan\visual-identical-twin-main
npm ci
npm run dev
```

Le frontend tourne sur: `http://127.0.0.1:8080`

#### Etape F - Connexion
- URL: `http://127.0.0.1:8080`
- Identifiant: `admin`
- Mot de passe: `admin123`

---

### 1.4 URLs utiles
- Frontend: `http://127.0.0.1:8080`
- Backend Django: `http://127.0.0.1:8000`
- API resume: `http://127.0.0.1:8000/api/dashboard/summary/`
- phpMyAdmin (optionnel): `http://127.0.0.1:8081`

---

### 1.5 Procedure de test rapide (smoke test)
1. Ouvrir `http://127.0.0.1:8080`
2. Se connecter avec `admin/admin123`
3. Verifier que la page Dashboard s'affiche
4. Changer un filtre dans la barre laterale et verifier que les cartes/KPI se mettent a jour
5. Cliquer sur `Rafraichir` en haut et verifier la mise a jour
6. Verifier le rafraichissement automatique (toutes les 120 secondes)
7. Verifier que l'onglet Energie affiche des courbes/valeurs

Note Windows x64:
- Si `phpmyadmin` ne demarre pas a cause d'une image `arm64v8`, ce n'est pas bloquant pour tester la WebApp.
- Le dashboard fonctionne avec le service `mariadb` uniquement.

---

### 1.6 Liste des paquets et versions

## 1.6.1 Backend Python (paquets installes via `pip install -r qlio_dash/requirements.txt`)

- Django==5.2.6
- mysqlclient==2.2.6
- dash==2.17.1
- plotly==5.22.0
- pandas==2.2.3
- SQLAlchemy==2.0.38
- pymysql==1.1.1
- pytest==7.4.4

## 1.6.2 Backend Python (ensemble observe dans le venv de reference via `pip freeze`)

- asgiref==3.9.2
- blinker==1.9.0
- certifi==2026.1.4
- charset-normalizer==3.4.4
- click==8.3.1
- dash==2.17.1
- dash-core-components==2.0.0
- dash-html-components==2.0.0
- dash-table==5.0.0
- Django==5.2.6
- Flask==3.0.3
- idna==3.11
- importlib_metadata==8.7.1
- iniconfig==2.3.0
- itsdangerous==2.2.0
- Jinja2==3.1.6
- MarkupSafe==3.0.3
- mysqlclient==2.2.6
- nest-asyncio==1.6.0
- numpy==2.4.2
- packaging==26.0
- pandas==2.2.3
- plotly==5.22.0
- pluggy==1.6.0
- PyMySQL==1.1.1
- pytest==7.4.4
- python-dateutil==2.9.0.post0
- pytz==2025.2
- requests==2.32.5
- retrying==1.4.2
- setuptools==82.0.0
- six==1.17.0
- SQLAlchemy==2.0.38
- sqlparse==0.5.3
- tenacity==9.1.4
- typing_extensions==4.15.0
- tzdata==2025.3
- urllib3==2.6.3
- Werkzeug==3.0.6
- zipp==3.23.0

## 1.6.3 Frontend Node (paquets directs observes via `npm ls --depth=0`)

- @eslint/js@9.32.0
- @hookform/resolvers@3.10.0
- @radix-ui/react-accordion@1.2.11
- @radix-ui/react-alert-dialog@1.1.14
- @radix-ui/react-aspect-ratio@1.1.7
- @radix-ui/react-avatar@1.1.10
- @radix-ui/react-checkbox@1.3.2
- @radix-ui/react-collapsible@1.1.11
- @radix-ui/react-context-menu@2.2.15
- @radix-ui/react-dialog@1.1.14
- @radix-ui/react-dropdown-menu@2.1.15
- @radix-ui/react-hover-card@1.1.14
- @radix-ui/react-label@2.1.7
- @radix-ui/react-menubar@1.1.15
- @radix-ui/react-navigation-menu@1.2.13
- @radix-ui/react-popover@1.1.14
- @radix-ui/react-progress@1.1.7
- @radix-ui/react-radio-group@1.3.7
- @radix-ui/react-scroll-area@1.2.9
- @radix-ui/react-select@2.2.5
- @radix-ui/react-separator@1.1.7
- @radix-ui/react-slider@1.3.5
- @radix-ui/react-slot@1.2.3
- @radix-ui/react-switch@1.2.5
- @radix-ui/react-tabs@1.1.12
- @radix-ui/react-toast@1.2.14
- @radix-ui/react-toggle-group@1.1.10
- @radix-ui/react-toggle@1.1.9
- @radix-ui/react-tooltip@1.2.7
- @tailwindcss/typography@0.5.16
- @tanstack/react-query@5.83.0
- @testing-library/jest-dom@6.9.1
- @testing-library/react@16.3.2
- @types/node@22.16.5
- @types/react-dom@18.3.7
- @types/react@18.3.23
- @vitejs/plugin-react-swc@3.11.0
- autoprefixer@10.4.21
- class-variance-authority@0.7.1
- clsx@2.1.1
- cmdk@1.1.1
- date-fns@3.6.0
- embla-carousel-react@8.6.0
- eslint-plugin-react-hooks@5.2.0
- eslint-plugin-react-refresh@0.4.20
- eslint@9.32.0
- globals@15.15.0
- input-otp@1.4.2
- jsdom@20.0.3
- lucide-react@0.462.0
- next-themes@0.3.0
- postcss@8.5.6
- react-day-picker@8.10.1
- react-dom@18.3.1
- react-hook-form@7.61.1
- react-resizable-panels@2.1.9
- react-router-dom@6.30.1
- react@18.3.1
- recharts@2.15.4
- sonner@1.7.4
- tailwind-merge@2.6.0
- tailwindcss-animate@1.0.7
- tailwindcss@3.4.17
- typescript-eslint@8.38.0
- typescript@5.8.3
- vaul@0.9.9
- vite@5.4.19
- vitest@3.2.4
- zod@3.25.76

## 1.6.4 Images Docker
- mariadb:latest
- arm64v8/phpmyadmin:5.2.1

---

## 2) Documentation technique des fonctionnalites de la WebApp

### 2.1 Authentification

### 2.1.1 Login frontend
- Route frontend: `/login`
- Formulaire avec:
  - username
  - password
  - affichage/masquage du mot de passe
  - option `Se souvenir de moi`
- Le frontend recupere un cookie CSRF (`/accounts/csrf/`) puis poste vers `/accounts/login/`.

### 2.1.2 Login backend
- Endpoint: `POST /accounts/login/`
- Si `remember_me=1`, la session est prolongee (30 jours).
- Redirection vers la page demandee (`next`) apres connexion.

### 2.1.3 Logout
- Endpoint: `POST /accounts/logout/`
- Bouton `Deconnexion` en haut du dashboard
- Redirection vers login

### 2.1.4 Protection API
- Endpoint principal: `GET /api/dashboard/summary/`
- Si non authentifie: `401` avec `{"error":"auth_required","login_url":...}`

---

### 2.2 Dashboard global

### 2.2.1 Structure
Le dashboard est organise en 7 onglets:
- Vue generale
- Performance
- Qualite
- Stock
- Delai
- Energie
- Maintenance

### 2.2.2 Refresh
- Bouton manuel `Rafraichir` dans l'entete
- Refresh automatique toutes les 2 minutes (`refetchInterval: 120000`)

### 2.2.3 Indicateur de source
La source de donnees est exposee dans la reponse API (`data_source`):
- `telephan_warehouse` (schema facts/dimensions `mes_kpi`)
- `mes_raw` (fallback tables MES brutes)

---

### 2.3 Filtres lateraux

Filtres disponibles:
- `temporal`: all-time, today, yesterday, this-week, last-week, this-month
- `shift`: all, shift-a, shift-b, shift-c
- `machine`
- `product`
- `of` (ordre de fabrication)
- `error_type`

Comportement:
- Les filtres sont stockes dans un contexte React global
- Chaque changement de filtre relance un appel API
- Certaines listes (`machine`, `product`, `of`, `error_type`) sont alimentees dynamiquement par `filter_options` du backend

---

### 2.4 Description de chaque onglet

### 2.4.1 Vue generale
- Carte de synthese par bloc metier (Performance, Qualite, Stock, Delai, Energie, Maintenance)
- Statut par bloc: `success`, `warning`, `danger`, `unknown`
- Clic sur une carte -> navigation vers l'onglet detaille correspondant

### 2.4.2 Performance
- KPI affiches:
  - Taux d'utilisation machine
  - TRS
  - Temps de cycle
  - Taux d'execution des operations
- Visualisations:
  - Jauge TRS + courbe d'evolution
  - Courbe temps de cycle

### 2.4.3 Qualite
- KPI affiches:
  - Taux de non-conformite
  - Nombre total d'erreurs
  - Nombre d'erreurs critiques
- Visualisations:
  - Jauge/courbe non-conformite
  - Histogramme erreurs par machine
  - Table des erreurs critiques

### 2.4.4 Stock
- KPI affiches:
  - Niveau moyen de stock
  - Taux d'occupation stockage
  - Taux d'occupation encours (WIP)
- Visualisations:
  - Jauge + evolution stock
  - Barres occupation par zone

### 2.4.5 Delai
- KPI affiches:
  - Lead Time global
  - OTD (livre dans les temps)
- Visualisations:
  - Jauge + evolution OTD
  - Histogramme lead time par OF/produit

### 2.4.6 Energie
- KPI affiches:
  - Consommation energetique
  - Air comprime moyen
- Visualisations:
  - Jauge + courbe energie
  - Graphique combine energie/air
- Particularite implementation:
  - Si les mesures energie entrepot sont absentes ou nulles, fallback sur un CSV energie reel (`dataEnergy.csv`) avec integration puissance/debit dans le temps

### 2.4.7 Maintenance
- KPI affiches:
  - Erreurs critiques
  - Erreurs totales
  - Temps d'arret lie aux erreurs
- Visualisations:
  - Evolution erreurs (totales vs critiques)
  - Evolution temps d'arret

---

### 2.5 API Dashboard (contrat principal)

Endpoint:
- `GET /api/dashboard/summary/`

Parametres query supportes:
- `temporal`
- `shift`
- `machine`
- `product`
- `of`
- `error_type`

Champs de reponse principaux:
- `generated_at`
- `window_minutes`
- `data_source`
- `kpis` (valeurs unitaires)
- `sections` (groupement par onglet)
- `details` (series pour graphiques)
- `filter_options` (options dynamiques de filtres)

---

## 3) Documentation analytique: choix et pertinence des indicateurs

### 3.1 Logique de pilotage
Le tableau de bord suit 6 axes qui couvrent le pilotage industriel de bout en bout:
- Performance (cadence et rendement)
- Qualite (defauts et criticite)
- Stock (niveau et saturation)
- Delai (flux et respect des echeances)
- Energie (efficacite energetique)
- Maintenance (fiabilite et indisponibilites)

L'objectif est de donner une lecture operationnelle immediate pour agir vite: production, qualite, methodes, maintenance, management.

---

### 3.2 Indicateurs retenus, formule et pertinence

| Axe | KPI | Formule (implementation) | Pertinence metier |
|---|---|---|---|
| Performance | Taux d'utilisation machine | `sum(busy_seconds) / sum(available_seconds) * 100` | Mesure l'usage reel des moyens, detecte sous-charge et arrets inutiles. |
| Performance | TRS | `Disponibilite * Performance * Qualite * 100` (calcul compose) | KPI synthetique de rendement global atelier. Permet arbitrage prioritaire. |
| Performance | Temps de cycle | `moyenne(cycle_time_seconds > 0)` | Mesure la cadence reelle, identifie pertes de vitesse et goulots. |
| Performance | Taux d'execution operations | `operations_terminees / operations_total * 100` | Suit la capacite a finir le plan d'operations. |
| Qualite | Taux de non-conformite | `quantite_nok / quantite_totale * 100` | Indicateur direct de derive qualite et cout de non-qualite. |
| Qualite | Nombre total d'erreurs | `sum(piece_count)` sur evenements qualite | Mesure le volume de defauts a traiter. |
| Qualite | Nombre d'erreurs critiques | `sum(piece_count where is_critical=1)` | Priorise les risques majeurs (securite, rebuts forts, blocage ligne). |
| Stock | Niveau moyen de stock | `mean(quantity)` | Verifie l'equilibre de stock global et les immobilisations. |
| Stock | Taux d'occupation stockage | `sum(positions_used)/sum(capacity_positions)*100` | Detecte saturation des zones de stockage. |
| Stock | Taux d'occupation encours (WIP) | meme ratio limite aux buffers encours | Surveille accumulation inter-postes et fluidite du flux. |
| Delai | Lead Time global | `mean(real_lead_time_seconds)/60` | Mesure vitesse reelle de traversée du flux. |
| Delai | OTD | `mean(delivered_on_time)*100` | Mesure tenue des engagements de livraison client. |
| Energie | Consommation energetique | `sum(energy_mws)/pieces/3_600_000_000` (ou fallback CSV) | Suit efficacite energetique par unite produite. |
| Energie | Air comprime moyen | `sum(air_mnl)/pieces/1000` (ou fallback CSV) | Suit un cout cache important en environnement industriel. |
| Maintenance | Erreurs critiques | issu des evenements qualite critiques | Donne la priorite d'intervention maintenance/fiabilite. |
| Maintenance | Erreurs totales | agrégat erreurs qualite | Mesure la charge globale incidents machine/process. |
| Maintenance | Temps d'arret | aggregation des plages d'erreur/indisponibilite | Traduit directement la perte de capacite productive. |

---

### 3.3 Pourquoi ces KPI sont pertinents ensemble

1. Ils relient les causes aux effets.
- Exemple: hausse erreurs critiques -> baisse TRS -> hausse lead time -> baisse OTD.

2. Ils couvrent le triangle industriel cout/qualite/delai.
- Cout: energie, air, temps d'arret, surstock.
- Qualite: non-conformite, erreurs.
- Delai: lead time, OTD.

3. Ils sont actionnables par les equipes.
- Production agit sur cadence/TRS.
- Qualite agit sur non-conformite/erreurs.
- Maintenance agit sur criticite et arrets.
- Supply agit sur stock et encours.

4. Ils permettent le pilotage court terme et moyen terme.
- Court terme: filtres temporels et rafraichissement automatique 2 min.
- Moyen terme: tendances hebdomadaires dans chaque onglet.

---

### 3.4 Limites connues et interpretation

- Si la base n'est pas alimentee sur une periode recente, certains KPI peuvent etre `null` ou proches de 0.
- Le bloc Energie dispose d'un fallback CSV pour garantir des mesures reelles meme si l'entrepot est incomplet.
- Le mode `temporal=now` peut renvoyer peu de donnees si aucune nouvelle mesure n'est presente dans la fenetre courante.

---

### 3.5 Conclusion analytique

Le choix d'indicateurs est pertinent car il combine:
- une vue synthese decisionnelle (6 blocs)
- des KPI operationnels actionnables
- des details graphiques pour diagnostic

Cette combinaison est adaptee a un pilotage atelier en continu avec prise de decision rapide.
