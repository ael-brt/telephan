# Telephan Dashboard Frontend

Frontend React/Vite du tableau de bord TELEPHAN.

## Démarrage local

```sh
npm install
npm run dev
```

Le serveur de dev tourne sur `http://localhost:8080`.

## Intégration backend

Le frontend consomme l'API Django via le proxy Vite:

- `/api/*` -> `http://127.0.0.1:8000`
- `/accounts/*` -> `http://127.0.0.1:8000`

## Stack

- React + TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- TanStack Query
