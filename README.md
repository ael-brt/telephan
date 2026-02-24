# TELEPHAN Dashboard (SAE QLIO)

Projet full-stack pour le dashboard TELEPHAN:

- `qlio_dash/` : backend Django + API KPI + auth
- `visual-identical-twin-main/` : frontend React/Vite (dashboard)
- `telephan.sql` : schema DWH (`mes_kpi`)
- `qlio_dash/dashboard/sql/populate_mes_kpi_from_mes4.sql` : ETL `mes4 -> mes_kpi`

Le frontend consomme l'API Django et utilise l'auth Django (session + CSRF) avec une page de login frontend (`/login`).

## Demarrage simplifie (client)

Pour un lancement simple (macOS), utiliser le script fourni.

Important: il faut quand meme installer les prerequis systeme ci-dessous avant le premier lancement.

- double-clic sur `launch_telephan.command`
- ou en terminal:

```bash
./launch_telephan.command
```

Le script:

- demarre `mariadb` + `phpMyAdmin` (Docker)
- prepare le backend Python (`.venv`) si besoin
- prepare le frontend (`node_modules`) si besoin
- lance Django + Vite
- ouvre automatiquement le dashboard dans le navigateur

Arret:

```bash
./stop_telephan.command
```

Note: le premier lancement peut prendre plusieurs minutes (installation des dependances Python + Node).

## Prerequis

### Prerequis obligatoires (tous)

- OS: macOS (scripts `.command` fournis). Linux possible en suivant les commandes manuelles du README.
- Docker Desktop installe et demarre (obligatoire pour MariaDB + phpMyAdmin)
- Docker Compose v2 (`docker compose`)
- Python `3.12+` (teste avec `3.13`)
- `python3-venv` / module `venv` disponible
- Node.js `18+` (recommande `20 LTS`) + `npm`
- Connexion internet au premier lancement (telechargement `pip` + `npm`)
- Navigateur web recent (Chrome / Edge / Firefox)

### Prerequis systeme Python (backend `mysqlclient`)

Le backend installe `mysqlclient`, qui necessite des dependances systeme.

#### macOS (recommande pour eviter les erreurs de build)

- Xcode Command Line Tools:

```bash
xcode-select --install
```

- Homebrew installe
- paquets Homebrew:

```bash
brew install pkg-config mysql-client
```

Si `mysqlclient` echoue quand meme a l'installation, ouvrir un nouveau terminal puis relancer `./launch_telephan.command`.

### Ressources machine recommandees

- RAM: `8 Go` minimum (Docker + Node + Python)
- Espace disque libre: `5 Go+` (images Docker, `node_modules`, venv)

### Ports utilises (doivent etre libres)

- `3306` : MariaDB (Docker)
- `8081` : phpMyAdmin
- `8000` : backend Django
- `8080` : frontend Vite

Si un port est deja pris, l'application peut ne pas demarrer correctement.

### Donnees / base de donnees (pour les vraies courbes)

- dump MES brut (ex: `FestoMES-2025-12-02.sql`) disponible localement
- `telephan.sql` (versionne dans ce repo) pour creer `mes_kpi`
- ETL `qlio_dash/dashboard/sql/populate_mes_kpi_from_mes4.sql` (versionne)

Sans dump MES, l'interface peut s'afficher mais certaines donnees seront vides ou en fallback.

### Compte utilisateur (connexion dashboard)

- Un compte Django est necessaire pour se connecter au dashboard.
- Creer au moins un utilisateur avec:

```bash
cd qlio_dash
python manage.py createsuperuser
```

### Verification rapide des prerequis (optionnel)

```bash
docker --version
docker compose version
python3 --version
npm --version
```

## 1. Cloner et preparer l'environnement

```bash
git clone <URL_DU_REPO>
cd SAEQLIO
cp .env.example .env
```

`docker-compose.yml` lit automatiquement `.env`.

## 2. Lancer MariaDB + phpMyAdmin (Docker)

```bash
docker compose up -d mariadb phpmyadmin
```

Acces utiles:

- MariaDB: `127.0.0.1:3306`
- phpMyAdmin: `http://127.0.0.1:8081`

## 3. Importer les donnees MES (si besoin)

Le dashboard utilise prioritairement le schema DWH `mes_kpi`, alimente a partir de `mes4`.

### 3.1 Import du dump MES brut dans `mes4`

Option simple via phpMyAdmin:

- ouvrir `http://127.0.0.1:8081`
- selectionner la base `mes4`
- importer le dump MES (non versionne dans ce repo)

Option CLI (exemple):

```bash
docker compose exec -T mariadb sh -c 'mariadb -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"' < FestoMES-2025-12-02.sql
```

Note: les dumps volumineux ne sont pas inclus dans le repo par defaut (voir `.gitignore`).

### 3.2 Creer le schema DWH `mes_kpi`

```bash
docker compose exec -T mariadb sh -c 'mariadb -u"$MYSQL_USER" -p"$MYSQL_PASSWORD"' < telephan.sql
```

### 3.3 Alimenter `mes_kpi` depuis `mes4`

```bash
docker compose exec -T mariadb sh -c 'mariadb -u"$MYSQL_USER" -p"$MYSQL_PASSWORD"' < qlio_dash/dashboard/sql/populate_mes_kpi_from_mes4.sql
```

## 4. Backend Django (API + auth)

```bash
cd qlio_dash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```

Lancement backend avec la vraie base MariaDB:

```bash
USE_SQLITE_FALLBACK=0 \
DB_NAME=mes4 \
DB_USER=example_user \
DB_PASSWORD=example_password \
DB_HOST=127.0.0.1 \
DB_PORT=3306 \
DWH_SCHEMA=mes_kpi \
FRONTEND_BASE_URL=http://127.0.0.1:8080 \
python manage.py runserver 127.0.0.1:8000
```

Si tu veux juste afficher les pages sans data reelle, laisse `USE_SQLITE_FALLBACK=1` (par defaut).

## 5. Frontend React/Vite

Dans un autre terminal:

```bash
cd visual-identical-twin-main
npm install
npm run dev
```

Frontend:

- `http://127.0.0.1:8080`

Le proxy Vite redirige:

- `/api/*` -> Django `127.0.0.1:8000`
- `/accounts/*` -> Django `127.0.0.1:8000`

## 6. Flux de connexion

- ouvrir `http://127.0.0.1:8080`
- si non connecte: redirection vers `/login` (frontend)
- le formulaire frontend poste vers Django (`/accounts/login/`)
- logout en `POST` vers Django, puis retour sur `/login`

## 7. Verification rapide

- API dashboard: `http://127.0.0.1:8000/api/dashboard/summary/`
- Si `data_source = telephan_warehouse`, le schema `mes_kpi` est bien utilise
- Si `data_source = mes_raw`, fallback sur les tables MES brutes

## 8. Fichiers importants a versionner

Le repo doit contenir au minimum:

- `qlio_dash/` (code backend)
- `visual-identical-twin-main/` (code frontend)
- `docker-compose.yml`
- `.env.example`
- `telephan.sql`
- `qlio_dash/dashboard/sql/populate_mes_kpi_from_mes4.sql`

Le repo n'a pas besoin de contenir:

- `node_modules/`
- `.venv/`
- `data/` (volume MariaDB Docker)
- dumps SQL volumineux (`FestoMES-*.sql`)
- documents de rendu / exports locaux
