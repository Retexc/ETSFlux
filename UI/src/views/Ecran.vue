<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, provide, ref, watch } from "vue";
import Scene from "../components/Scene.vue";
import Entete from "../components/Entete.vue";
import AlertBanner from "../components/AlertBanner.vue";
import Defilant from "../components/Defilant.vue";
import Telecommande from "../components/Telecommande.vue";
import Jumelage from "../components/Jumelage.vue";
import DiapoStm from "./diapos/DiapoStm.vue";
import DiapoExo from "./diapos/DiapoExo.vue";
import DiapoVeille from "./diapos/DiapoVeille.vue";
import DiapoSimple from "./diapos/DiapoSimple.vue";
import { useTransit } from "../composables/useTransit.js";
import { garderLiens, jeton, lireListe } from "../lib/flux.js";

/**
 * Écran du salon (Figma « ETS Flux ») : les diapositives choisies dans AMÉUX Flux, dans leur ordre et avec
 * leur durée (images, vidéos, annonces simples, STM, trains exo, photos d'ambiance).
 * - Bandeau d'annonces (messages de l'ÉTS / de l'AMÉUX) : en bas de TOUTES les diapositives.
 * - Alertes STM : seulement sur les diapositives de transport (pas de surcharge ailleurs).
 * - Notice de la télécommande : toujours sur les photos d'ambiance, et de temps à autre sur les autres.
 * La liste est relue chaque minute ; Flux ou Internet en panne : la dernière liste reste affichée.
 */
const LECTURE_MS = 60_000;
const VIDEO_MAX_MS = 10 * 60_000;
const RECHARGER_APRES_MS = 24 * 3600_000;
const NOTICE_TOUTES_MS = 3 * 60_000;   // rappel de la télécommande toutes les 3 minutes…
const NOTICE_DUREE_MS = 10_000;        // … pendant 10 secondes

// Photos d'ambiance par défaut, livrées avec l'écran (nature, art abstrait ; licence dans assets/ambiance)
const PHOTOS_DEFAUT = Object.values(import.meta.glob("../assets/ambiance/*.jpg", { eager: true, import: "default" }))
  .map((url) => ({ id: url, url, credit: "Photo : Unsplash" }));

const { alerts } = useTransit();   // une seule lecture STM / météo / exo pour tout l'écran
const jumele = ref(!!jeton());
const liste = ref([]);
const messages = ref([]);
const photos = ref([]);
const photosParDefaut = ref(true);
const version = ref(null);
const index = ref(0);
const photoIndex = ref(0);
const notice = ref(false);
const video = ref(null);
const demarre = Date.now();
let minuterieDiapo = null;
let minuterieLecture = null;
let minuterieNotice = null;
let minuterieNoticeFin = null;

const actuelle = computed(() => liste.value[index.value] || null);
const transport = computed(() => !!actuelle.value?.transport);
const veille = computed(() => actuelle.value?.type === "veille");
const galerie = computed(() => [...photos.value, ...(photosParDefaut.value ? PHOTOS_DEFAUT : [])]);
const photo = computed(() => (galerie.value.length ? galerie.value[photoIndex.value % galerie.value.length] : null));
// Hauteur occupée par les bandeaux du bas (56 px chacun) : crédits photo et rappel posés au-dessus
const HAUTEUR_BANDEAU = 56;
const bandeaux = computed(() => (messages.value.length ? 1 : 0) + (transport.value && alerts.value.length ? 1 : 0));
const basCredit = computed(() => 6 + bandeaux.value * HAUTEUR_BANDEAU);
provide("basCredit", basCredit);

async function lire() {
  const r = await lireListe();
  if (r.etat === "non-jumele") { jumele.value = false; liste.value = []; return; }
  if (!r.liste || r.liste.version === version.value) return;
  const idActuel = actuelle.value?.id;
  version.value = r.liste.version;
  liste.value = garderLiens(r.liste.diapos || [], liste.value);
  messages.value = r.liste.messages || [];
  photos.value = garderLiens((r.liste.photos || []).map((p) => ({ ...p, version: p.credit ?? "" })), photos.value);
  photosParDefaut.value = r.liste.photosParDefaut !== false;
  const i = liste.value.findIndex((d) => d.id === idActuel);
  index.value = i >= 0 ? i : 0;
  programmer();
}

function suivante() {
  if (Date.now() - demarre > RECHARGER_APRES_MS) { window.location.reload(); return; }
  if (!liste.value.length) return;
  index.value = (index.value + 1) % liste.value.length;
  if (veille.value) photoIndex.value += 1;   // une photo différente à chaque passage
  programmer();
}

function programmer() {
  clearTimeout(minuterieDiapo);
  const d = actuelle.value;
  if (!d || liste.value.length < 2) return;
  const ms = d.duree_s ? d.duree_s * 1000 : d.type === "video" ? VIDEO_MAX_MS : 10_000;
  minuterieDiapo = setTimeout(suivante, ms);
  const s = liste.value[(index.value + 1) % liste.value.length];
  if ((s?.type === "image" || s?.type === "simple") && s.url) new Image().src = s.url;
  if (s?.type === "veille" && galerie.value.length) new Image().src = galerie.value[(photoIndex.value + 1) % galerie.value.length].url;
}

function finVideo() { if (!actuelle.value?.duree_s) suivante(); }

watch(actuelle, async (d) => {
  if (d?.type !== "video") return;
  await nextTick();
  if (video.value) { video.value.currentTime = 0; video.value.play().catch(() => setTimeout(suivante, 2000)); }
});

function rappelTelecommande() {
  notice.value = true;
  clearTimeout(minuterieNoticeFin);
  minuterieNoticeFin = setTimeout(() => { notice.value = false; }, NOTICE_DUREE_MS);
}

function commencer() { jumele.value = true; lire(); }

onMounted(() => {
  if (jumele.value) lire();
  minuterieLecture = setInterval(() => { if (jumele.value) lire(); }, LECTURE_MS);
  minuterieNotice = setInterval(rappelTelecommande, NOTICE_TOUTES_MS);
});
onBeforeUnmount(() => {
  clearTimeout(minuterieDiapo); clearInterval(minuterieLecture); clearInterval(minuterieNotice); clearTimeout(minuterieNoticeFin);
});
</script>

<template>
  <Jumelage v-if="!jumele" @jumele="commencer" />
  <Scene v-else class="ecran">
    <Transition name="fondu">
      <div v-if="actuelle" :key="actuelle.id" class="absolute inset-0">
        <DiapoStm v-if="actuelle.type === 'stm'" />
        <DiapoExo v-else-if="actuelle.type === 'exo'" />
        <DiapoVeille v-else-if="actuelle.type === 'veille'" :photo="photo" />
        <DiapoSimple v-else-if="actuelle.type === 'simple' && actuelle.simple" :simple="actuelle.simple" :url="actuelle.url" />
        <template v-else>
          <!-- Image ou vidéo de l'AMÉUX : en-tête blanc, puis le fichier sur fond noir -->
          <Entete />
          <div class="absolute inset-x-0 bottom-0 top-[90px] bg-black">
            <video v-if="actuelle.type === 'video'" ref="video" :src="actuelle.url" muted playsinline autoplay
              :loop="liste.length === 1" class="size-full" :class="actuelle.cadrage === 'cover' ? 'object-cover' : 'object-contain'"
              @ended="finVideo" @error="suivante" />
            <img v-else :src="actuelle.url" :alt="actuelle.titre" class="size-full"
              :class="actuelle.cadrage === 'cover' ? 'object-cover' : 'object-contain'" @error="suivante" />
            <p v-if="actuelle.credit" class="absolute left-[8px] font-atlas text-[14px] text-white/60 drop-shadow" :style="{ bottom: `${basCredit}px` }">{{ actuelle.credit }}</p>
          </div>
        </template>
      </div>
    </Transition>

    <div v-if="!actuelle" class="absolute inset-0">
      <Entete />
    </div>

    <!-- Rappel de la télécommande (déjà affiché en permanence sur les photos d'ambiance) -->
    <Transition name="fondu">
      <div v-if="notice && !veille" class="absolute left-[40px] rounded-[20px] bg-black/70 py-[14px] pr-[24px] backdrop-blur"
        :style="{ bottom: `${basCredit + 34}px` }">
        <Telecommande />
      </div>
    </Transition>

    <!-- Bas de l'écran : alertes STM (transport seulement), puis messages de l'ÉTS / de l'AMÉUX (toujours) -->
    <div class="absolute bottom-0 left-0 flex w-[1920px] flex-col">
      <AlertBanner v-if="transport" />
      <Defilant :textes="messages" fond="#004952" couleur="#ffffff" />
    </div>
  </Scene>
</template>

<style scoped>
.ecran { cursor: none; }
.fondu-enter-active, .fondu-leave-active { transition: opacity 0.6s ease; }
.fondu-enter-from, .fondu-leave-to { opacity: 0; }
@media (prefers-reduced-motion: reduce) {
  .fondu-enter-active, .fondu-leave-active { transition: none; }
}
</style>
