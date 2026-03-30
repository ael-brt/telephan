#  QLIO Dashboard

Application **Django** pour afficher un tableau de bord avec une dizaine d’indicateurs.
Projet réalisé dans le cadre du cours **SAE QLIO**.

---

##  Installation locale

### 1. Cloner le dépôt

```bash
git clone https://github.com/<ton-compte>/qlio_dash.git
cd qlio_dash
```

### 2. Créer l’environnement virtuel

**macOS / Linux :**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell) :**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Appliquer les migrations

```bash
python manage.py migrate
```

### 5. Créer un superutilisateur (admin)

```bash
python manage.py createsuperuser
```

 Choisis un identifiant et un mot de passe (ex. `admin` / `admin123`).

### 6. Lancer le serveur

```bash
python manage.py runserver
```

* Application : [http://127.0.0.1:8000](http://127.0.0.1:8000)
* Admin Django : [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

##  Gestion utilisateurs

* **Connexion** : `/accounts/login/`
* **Déconnexion** : `/accounts/logout/`
* Les mots de passe sont **hachés automatiquement** par Django (sécurité native).

---

##  Structure du projet

```
qlio_dash/
├─ config/          # configuration Django (settings, urls)
├─ accounts/        # gestion des utilisateurs (login/logout)
├─ dashboard/       # tableau de bord avec les indicateurs
├─ templates/       # templates HTML
├─ static/          # fichiers statiques (CSS, JS, images)
├─ requirements.txt # dépendances
└─ manage.py        # commandes Django
```

---

##  Tests

Lancer les tests unitaires :

```bash
python manage.py test
```

---

##  Remarques

* Projet prévu pour tourner **en local** (SQLite comme base de données).
* Ne pas utiliser en production sans configuration supplémentaire.
* Pour toute installation sur un autre poste, répéter les étapes d’installation ci-dessus.

---
