<script setup>
import { computed } from "vue";
import personne from "../../assets/figma/personne.svg";
import personnePale from "../../assets/figma/personne-pale.svg";

/** Achalandage (composant « Occupancy ») : couleur et nombre de personnes pleines selon la STM. */
const props = defineProps({ niveau: { type: String, default: "NO_DATA" } });
const NIVEAUX = {
  MANY_SEATS_AVAILABLE: { fond: "#3dc342", pleines: 1 },
  FEW_SEATS_AVAILABLE: { fond: "#3dc342", pleines: 2 },
  STANDING_ROOM_ONLY: { fond: "#ffaa00", pleines: 3 },
  CRUSHED_STANDING_ROOM_ONLY: { fond: "#ff5675", pleines: 4 },
  FULL: { fond: "#ff5675", pleines: 4 },
};
const n = computed(() => NIVEAUX[props.niveau] ?? { fond: "#999999", pleines: 0 });
</script>

<template>
  <div class="flex h-[51.683px] w-[132.078px] shrink-0 items-center justify-center gap-[1.149px] rounded-[13.782px] px-[9.188px] py-[4.594px]" :style="{ background: n.fond }">
    <img v-for="i in 4" :key="i" :src="i <= n.pleines ? personne : personnePale" alt="" class="size-[27.564px]" />
  </div>
</template>
