// Adresses des services, choisies au build (fichier .env du dossier UI, ou variables de Vercel).
// Rien de secret ici : ces adresses sont publiques.

/** Serveur Flask d'ETSignage : prochains passages STM, alertes, météo. */
export const API_URL = (import.meta.env.VITE_API_URL || 'https://etsignage-backend.onrender.com').replace(/\/$/, '')

/** AMÉUX Flux : liste des annonces de l'écran (Annonces → Écran du salon). */
export const FLUX_URL = (import.meta.env.VITE_FLUX_URL || 'https://ameux.vercel.app').replace(/\/$/, '')
