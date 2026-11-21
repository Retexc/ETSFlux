import { ref, onMounted, onBeforeUnmount } from 'vue'
import { API_URL } from '../config.js'

/**
 * Données STM et météo, partagées par tout l'écran (bandeau, alertes, bloc STM) : UNE seule demande
 * au serveur Flask toutes les 30 secondes, quel que soit le nombre de composants qui s'en servent.
 * En cas d'erreur, les dernières données reçues restent affichées.
 */
const buses = ref([])
const metroLines = ref([])
const alerts = ref([])
const exo = ref([])
const weather = ref({ icon: '', text: '', temp: '' })
const chargement = ref(true)
const erreur = ref(null)

const INTERVALLE_MS = 30_000
let abonnes = 0
let minuterie = null

async function lire() {
  try {
    const r = await fetch(`${API_URL}/api/data`, { cache: 'no-store' })
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    const data = await r.json()
    buses.value = data.buses || []
    metroLines.value = data.metro_lines || []
    alerts.value = data.alerts || []
    exo.value = data.exo || []
    if (data.weather) weather.value = data.weather
    erreur.value = null
  } catch (e) {
    console.error('[transit]', e)
    erreur.value = 'Données STM indisponibles'
  } finally {
    chargement.value = false
  }
}

export function useTransit() {
  onMounted(() => {
    abonnes += 1
    if (abonnes === 1) {
      lire()
      minuterie = setInterval(lire, INTERVALLE_MS)
    }
  })
  onBeforeUnmount(() => {
    abonnes -= 1
    if (abonnes === 0 && minuterie) {
      clearInterval(minuterie)
      minuterie = null
    }
  })
  return { buses, metroLines, alerts, exo, weather, chargement, erreur }
}
