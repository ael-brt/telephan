# TELEPHAN Dashboard (SAE QLIO)

Projet de dashboard industriel (frontend + backend) realise dans le cadre de la SAE QLIO.

- `visual-identical-twin-main/` : frontend React/Vite
- `qlio_dash/` : backend Django + API + login
- `telephan.sql` : schema de la base KPI (`mes_kpi`)

## Lancement rapide (macOS)

Le plus simple:

1. Installer `Docker Desktop`, `Python 3`, `Node.js`
2. Ouvrir Docker Desktop (le laisser demarre)
3. Double-cliquer sur `launch_telephan.command`

Le script lance:
- MariaDB + phpMyAdmin
- le backend Django
- le frontend React

Puis il ouvre automatiquement le dashboard dans le navigateur.

Pour arreter:

```bash
./stop_telephan.command
```

## URLs utiles

- Dashboard (frontend): `http://127.0.0.1:8080`
- Backend Django: `http://127.0.0.1:8000`
- phpMyAdmin: `http://127.0.0.1:8081`

## Connexion

Le dashboard demande un compte Django.

Pour l'instant, utiliser le compte admin de demo:

- Identifiant: `admin`
- Mot de passe: `admin123`

Connexion via `http://127.0.0.1:8080`.

## Donnees (pour voir les vraies courbes)

Le projet peut s'afficher sans donnees reelles, mais pour avoir les vraies courbes il faut:

1. Importer un dump MES dans `mes4` (ex: `FestoMES-2025-12-02.sql`)
2. Importer `telephan.sql` (cree `mes_kpi`)
3. Lancer l'ETL `mes4 -> mes_kpi`

Commandes (si besoin):

```bash
docker compose exec -T mariadb sh -c 'mariadb -u"$MYSQL_USER" -p"$MYSQL_PASSWORD"' < telephan.sql
docker compose exec -T mariadb sh -c 'mariadb -u"$MYSQL_USER" -p"$MYSQL_PASSWORD"' < qlio_dash/dashboard/sql/populate_mes_kpi_from_mes4.sql
```

## Installation manuelle (si tu ne veux pas utiliser le script)

### 1) Backend

```bash
cd qlio_dash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

### 2) Frontend

```bash
cd visual-identical-twin-main
npm install
npm run dev
```

### 3) Docker (base de donnees)

```bash
docker compose up -d mariadb phpmyadmin
```

## Prerequis (simple)

Il faut juste:

- Docker Desktop
- Python 3 (3.12+)
- Node.js + npm
- Internet au premier lancement (installation des dependances)

## Si ca bloque (rapide)

- `docker compose` ne marche pas: verifier que Docker Desktop est bien lance
- `pip install` bloque sur `mysqlclient` (macOS): installer `Xcode Command Line Tools` + `brew install pkg-config mysql-client`
- le dashboard ouvre mais rien ne s'affiche: verifier que le backend tourne (`http://127.0.0.1:8000`)
- pas de courbes: verifier que les donnees MES ont bien ete importees

## Fichiers importants du projet

- `docker-compose.yml`
- `.env.example`
- `telephan.sql`
- `qlio_dash/dashboard/sql/populate_mes_kpi_from_mes4.sql`
