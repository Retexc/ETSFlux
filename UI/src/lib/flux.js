import { FLUX_URL } from '../config.js'

/**
 * Lien avec AMÉUX Flux. L'écran est jumelé une fois par un code (Flux → Annonces → Écran du salon →
 * « Connecter un écran ») et reçoit un jeton secret, gardé dans ce navigateur seulement.
 */
const CLE_JETON = 'ecran:jeton'
const CLE_LISTE = 'ecran:liste'

const lireStockage = (cle) => { try { return localStorage.getItem(cle) } catch { return null } }
const ecrireStockage = (cle, v) => { try { v === null ? localStorage.removeItem(cle) : localStorage.setItem(cle, v) } catch { /* stockage indisponible */ } }

export const jeton = () => lireStockage(CLE_JETON)
export const oublierJeton = () => { ecrireStockage(CLE_JETON, null); ecrireStockage(CLE_LISTE, null) }

/** Échange le code affiché dans Flux contre le jeton de l'écran. Renvoie un message d'erreur, ou null. */
export async function jumeler(saisie) {
  // « abcd-2345 » → « ABCD2345 » (Flux fait aussi la conversion)
  const code = String(saisie || '').toUpperCase().replace(/[^A-Z0-9]/g, '')
  try {
    const r = await fetch(`${FLUX_URL}/api/affichage/jumeler`, {
      method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ code }),
    })
    const data = await r.json().catch(() => ({}))
    if (!r.ok || !data.jeton) return data.error || 'Code invalide ou expiré.'
    ecrireStockage(CLE_JETON, data.jeton)
    return null
  } catch {
    return 'Flux est injoignable. Vérifie la connexion Internet.'
  }
}

/**
 * Liste de ce qui passe à l'écran maintenant. `{ etat: 'ok', liste }`, `{ etat: 'non-jumele' }` (jeton
 * refusé : l'écran redemande un code) ou `{ etat: 'erreur', liste }` (dernière liste connue, gardée dans
 * le navigateur : une panne de Flux ou d'Internet ne vide pas l'écran).
 */
export async function lireListe() {
  const j = jeton()
  if (!j) return { etat: 'non-jumele' }
  try {
    const r = await fetch(`${FLUX_URL}/api/affichage`, { headers: { authorization: `Bearer ${j}` }, cache: 'no-store' })
    if (r.status === 401) { oublierJeton(); return { etat: 'non-jumele' } }
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    const data = await r.json()
    ecrireStockage(CLE_LISTE, JSON.stringify(data))
    return { etat: 'ok', liste: data }
  } catch (e) {
    console.error('[flux]', e)
    const garde = lireStockage(CLE_LISTE)
    return { etat: 'erreur', liste: garde ? JSON.parse(garde) : null }
  }
}

/**
 * Garde les liens déjà reçus tant que la diapositive n'a pas changé (le fichier reste dans le cache du
 * navigateur : moins de téléchargements, quota de Supabase ménagé). Liens renouvelés après 5 jours
 * (ils sont valides 7 jours).
 */
const RENOUVELER_MS = 5 * 24 * 3600 * 1000
export function garderLiens(nouvelle, ancienne) {
  const vieux = new Map((ancienne || []).map((d) => [d.id, d]))
  const maintenant = Date.now()
  return nouvelle.map((d) => {
    const v = vieux.get(d.id)
    if (v && v.version === d.version && v.url && maintenant - (v.recu || 0) < RENOUVELER_MS) return { ...d, url: v.url, recu: v.recu }
    return { ...d, recu: maintenant }
  })
}
