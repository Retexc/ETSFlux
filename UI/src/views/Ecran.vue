<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import Header from "../components/Header.vue";
import AlertBanner from "../components/AlertBanner.vue";
import STMBloc from "../components/STMBloc.vue";
import Jumelage from "../components/Jumelage.vue";
import { garderLiens, jeton, lireListe } from "../lib/flux.js";

/**
 * Écran du salon : bandeau (date, heure, météo), puis les annonces choisies dans AMÉUX Flux, dans leur
 * ordre et avec leur durée, le bloc STM compris. La liste est relue chaque minute ; elle ne change à
 * l'écran que si elle a changé dans Flux. Flux ou Internet en panne : la dernière liste reste affichée.
 */
const LECTURE_MS = 60_000;
const VIDEO_MAX_MS = 10 * 60_000;          // filet : une vidéo bloquée ne fige pas l'écran
const RECHARGER_APRES_MS = 24 * 3600_000;  // rechargement complet une fois par jour (mises à jour, mémoire)

const jumele = ref(!!jeton());
const liste = ref([]);
const version = ref(null);
const index = ref(0);
const video = ref(null);
const demarre = Date.now();
let minuterieDiapo = null;
let minuterieLecture = null;

const actuelle = computed(() => liste.value[index.value] || null);

async function lire() {
  const r = await lireListe();
  if (r.etat === "non-jumele") { jumele.value = false; liste.value = []; return; }
  if (!r.liste || r.liste.version === version.value) return;
  const idActuel = actuelle.value?.id;
  version.value = r.liste.version;
  liste.value = garderLiens(r.liste.diapos || [], liste.value);
  // La diapositive affichée continue si elle est encore dans la liste
  const i = liste.value.findIndex((d) => d.id === idActuel);
  index.value = i >= 0 ? i : 0;
  programmer();
}

function suivante() {
  if (Date.now() - demarre > RECHARGER_APRES_MS) { window.location.reload(); return; }
  if (!liste.value.length) return;
  index.value = (index.value + 1) % liste.value.length;
  programmer();
}

/** Minuterie de la diapositive affichée (une vidéo sans durée passe à la suivante à sa fin). */
function programmer() {
  clearTimeout(minuterieDiapo);
  const d = actuelle.value;
  if (!d || liste.value.length < 2) return;
  const ms = d.duree_s ? d.duree_s * 1000 : d.type === "video" ? VIDEO_MAX_MS : 10_000;
  minuterieDiapo = setTimeout(suivante, ms);
  prechargerSuivante();
}

function finVideo() {
  if (!actuelle.value?.duree_s) suivante();
}

/** Image suivante chargée d'avance : pas d'écran vide au changement. */
function prechargerSuivante() {
  const s = liste.value[(index.value + 1) % liste.value.length];
  if (s?.type === "image" && s.url) new Image().src = s.url;
}

// Une vidéo démarre à chaque fois qu'elle revient à l'écran
watch(actuelle, async (d) => {
  if (d?.type !== "video") return;
  await nextTick();
  if (video.value) { video.value.currentTime = 0; video.value.play().catch(() => setTimeout(suivante, 2000)); }
});

function commencer() {
  jumele.value = true;
  lire();
}

onMounted(() => {
  if (jumele.value) lire();
  minuterieLecture = setInterval(() => { if (jumele.value) lire(); }, LECTURE_MS);
});
onBeforeUnmount(() => {
  clearTimeout(minuterieDiapo);
  clearInterval(minuterieLecture);
});
</script>

<template>
  <Jumelage v-if="!jumele" @jumele="commencer" />
  <div v-else class="ecran fixed inset-0 flex flex-col bg-black">
    <Header class="shrink-0" />
    <main class="relative min-h-0 flex-1 overflow-hidden">
      <Transition name="fondu">
        <div v-if="actuelle" :key="actuelle.id" class="absolute inset-0">
          <STMBloc v-if="actuelle.type === 'stm'" />
          <video v-else-if="actuelle.type === 'video'" ref="video" :src="actuelle.url" muted playsinline autoplay
            :loop="liste.length === 1" class="size-full" :class="actuelle.cadrage === 'cover' ? 'object-cover' : 'object-contain'"
            @ended="finVideo" @error="suivante" />
          <img v-else :src="actuelle.url" :alt="actuelle.titre" class="size-full"
            :class="actuelle.cadrage === 'cover' ? 'object-cover' : 'object-contain'" @error="suivante" />
        </div>
      </Transition>
    </main>
    <AlertBanner />
  </div>
</template>

<style scoped>
.ecran { cursor: none; }
.size-full { width: 100%; height: 100%; }
.fondu-enter-active, .fondu-leave-active { transition: opacity 0.6s ease; }
.fondu-enter-from, .fondu-leave-to { opacity: 0; }
@media (prefers-reduced-motion: reduce) {
  .fondu-enter-active, .fondu-leave-active { transition: none; }
}
</style>
