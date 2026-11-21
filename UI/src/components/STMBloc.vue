<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import BusRow from "./BusRow.vue";
import MetroRow from "./MetroRow.vue";
import STMLogo from "../assets/icons/STM.png";
import Background from "../assets/images/Login_bg.jpg";
import { useTransit } from "../composables/useTransit.js";

/**
 * Prochains passages STM et état du métro. Dessiné en 1920 × 1080 puis mis à l'échelle de son cadre :
 * le même rendu en plein écran (/stm) et dans la rotation de l'écran (/).
 */
const { buses, metroLines, erreur } = useTransit();

const LARGEUR = 1920;
const HAUTEUR = 1080;
const cadre = ref(null);
const echelle = ref(1);
let observateur = null;

onMounted(() => {
  observateur = new ResizeObserver(([e]) => {
    echelle.value = Math.min(e.contentRect.width / LARGEUR, e.contentRect.height / HAUTEUR);
  });
  observateur.observe(cadre.value);
});
onBeforeUnmount(() => observateur?.disconnect());

// Les heures en minutes (nombres) d'abord, puis les heures écrites (texte)
const busTries = computed(() => [...buses.value].sort((a, b) => {
  const x = a.arrival_time, y = b.arrival_time;
  if (typeof x === "number" && typeof y === "number") return x - y;
  if (typeof x === "string" && typeof y === "string") return x.localeCompare(y);
  return typeof x === "number" ? -1 : typeof y === "number" ? 1 : 0;
}));
</script>

<template>
  <div ref="cadre" class="relative w-full h-full overflow-hidden flex items-center justify-center bg-black"
    :style="{ backgroundImage: `url(${Background})`, backgroundSize: 'cover' }">
    <div class="relative flex flex-col px-8 pt-8 pb-4 gap-4 box-border origin-center shrink-0"
      :style="{ width: `${LARGEUR}px`, height: `${HAUTEUR}px`, transform: `scale(${echelle})` }">
      <div class="flex justify-center bg-white rounded-2xl py-4 mb-2">
        <img :src="STMLogo" alt="STM" class="h-10 w-auto" />
      </div>
      <p v-if="erreur && !busTries.length" class="text-white text-4xl text-center mt-20">{{ erreur }}</p>
      <bus-row v-for="bus in busTries" :key="bus.trip_id" :bus="bus" />
      <div v-if="metroLines.length > 0" class="h-px bg-white/30 my-2 mx-4"></div>
      <metro-row v-for="line in metroLines" :key="line.name" :line="line" />
    </div>
  </div>
</template>
