<script setup>
import { inject, ref } from "vue";
import fond from "../../assets/figma/fond-ets.png";
// Hauteur des bandeaux du bas (Ecran.vue) : le crédit reste visible au-dessus
const basCredit = inject("basCredit", ref(6));

/** Fond des diapositives de transport : photo de l'ÉTS assombrie (maquette), crédit en bas à gauche. */
</script>

<template>
  <div aria-hidden="true" class="pointer-events-none absolute inset-0">
    <img :src="fond" alt="" class="absolute size-full max-w-none object-cover" />
    <div class="absolute inset-0 bg-black/50" />
  </div>
  <p class="absolute left-[8px] font-atlas text-[14px] text-white/45" :style="{ bottom: `${basCredit}px` }">Photo : Stéphane Brugger</p>
</template>
