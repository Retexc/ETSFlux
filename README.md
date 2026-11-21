 <img width="4746" height="1582" alt="github_banner" src="https://github.com/user-attachments/assets/929ae648-b4a7-4e47-991f-3f8d4ebfb687" />

# ETSignage — écran du salon étudiant (AMÉUX)

Affiche sur la TV du salon (design Figma « ETS Flux ») : un en-tête (logo, date, météo, heure), les annonces de
l'AMÉUX en image, en vidéo ou en **annonce simple** (texte sur un fond de couleur, avec une image ou un code QR), les prochains passages **STM** (lignes 61 et 36, avec l'achalandage), les trains **exo**
au départ de la gare Lucien-L'Allier (Candiac, Saint-Jérôme, Vaudreuil) et des **photos d'ambiance** (écran de veille, avec la notice de la télécommande).

- Bandeau du bas : messages de l'ÉTS / de l'AMÉUX sur toutes les diapositives ; alertes STM seulement sur les
  diapositives de transport. Rappel de la télécommande toutes les 3 minutes sur les autres diapositives.
- Tout est dessiné en 1920 × 1080 (taille des maquettes) puis mis à l'échelle de la TV (`components/Scene.vue`).
- Images des maquettes : `UI/src/assets/figma/` ; photos d'ambiance par défaut (Unsplash) : `UI/src/assets/ambiance/`.
  Police Satoshi chargée depuis Fontshare (sa licence ne permet pas de copier les fichiers dans le dépôt).

**Les annonces se gèrent dans AMÉUX Flux** : Annonces → Écran du salon (ajout, durée, dates, ordre,
interrupteurs, bloc STM, aperçu). Ce dépôt ne fait plus qu'afficher.

## Fonctionnement

| Partie | Rôle | Hébergement |
|---|---|---|
| `UI/` (Vue 3, Vite, Tailwind) | L'écran : `/` = rotation des annonces de Flux + bloc STM ; `/stm` = STM seulement | Vercel |
| `backend/` (Flask) | `GET /api/data` (bus, métro, alertes, météo, gardé 20 s) et `GET /api/meteo` | Render |
| AMÉUX Flux | `GET /api/affichage` : ce qui passe à l'écran maintenant, dans l'ordre | Vercel |

- **Jumelage** : la première fois, l'écran demande un code. Dans Flux : Annonces → Écran du salon → « Connecter un écran ».
  On tape le code sur la TV, ou on ouvre l'adresse `https://<écran>/?code=XXXXXXXX`. L'écran garde ensuite un jeton secret
  dans son navigateur. « Déconnecter » dans Flux le lui retire.
- L'écran relit la liste de Flux chaque minute et les données STM toutes les 30 secondes (une seule demande pour tout l'écran).
  Flux ou Internet en panne : la dernière liste reste affichée. La page se recharge seule une fois par jour.
- **Horaires STM (GTFS)** : au démarrage, Flask lit les fichiers filtrés du bucket Supabase `gtfs-files` ; à chaque démarrage
  (après 1 minute, en arrière-plan) et ensuite **chaque semaine**, il télécharge le GTFS public de la STM et garde seulement nos lignes et nos arrêts
  (`backend/loaders/gtfs_update.py`). Un fichier sans nos lignes est refusé : les anciens horaires restent. Lignes et arrêts : `backend/config.py`.

## Variables

Écran (`UI/.env`, ou Vercel ; voir `UI/.env.example`) : `VITE_API_URL` (Flask), `VITE_FLUX_URL` (Flux). Adresses publiques seulement.

Serveur (`.env` à la racine, ou Render ; jamais commité) : `STM_API_KEY`, `WEATHER_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`
(lecture du bucket `gtfs-files`), facultatives `GTFS_AUTO=non` (couper la mise à jour automatique), `GTFS_STM_URL`, `GLOBAL_DELAY_MINUTES`.
Trains exo : horaires publics téléchargés au démarrage puis chaque semaine (`backend/loaders/exo.py`) ; le temps réel
(retards, annulations) s'active seul quand `CHRONO_TOKEN` (clé de l'API Chrono d'exo) est ajoutée dans Render.

Dans Flux (Vercel) : `AFFICHAGE_ORIGINES` = adresse de l'écran (ex. `https://ecran.exemple.com`), sinon le navigateur de la TV
ne peut pas lire la liste ; `AFFICHAGE_URL_ECRAN` (facultative) = même adresse, montrée avec le code de jumelage.

## Lancer en local

```
cd UI && npm install && npm run dev                       # écran
waitress-serve --port=5000 backend.main:app            # serveur (depuis la racine)
```

Tests du serveur : `pip install -r requirements-dev.txt` puis `python -m pytest -q`.

## Plus tard

- `/api/roku` dans Flux : annonces + météo + 4 prochains bus déjà calculés, pour un économiseur d'écran Roku.
- Horaire d'allumage et d'extinction de la TV, géré depuis Flux.
