<script setup>
import { inject, ref } from "vue";
import Entete from "../../components/Entete.vue";
import Telecommande from "../../components/Telecommande.vue";
import degrade from "../../assets/figma/degrade-veille.png";

/** Figma « Screen - Art » : photo d'ambiance plein écran, en-tête transparent, notice de la télécommande. */
const props = defineProps({ photo: { type: Object, default: null } });   // { url, credit }
const basCredit = inject("basCredit", ref(6));
</script>

<template>
  <div aria-hidden="true" class="pointer-events-none absolute inset-0 bg-[#0b1d3a]">
    <img v-if="props.photo" :key="props.photo.url" :src="props.photo.url" alt="" class="absolute size-full max-w-none object-cover" />
    <div class="absolute inset-0 bg-black/50" />
  </div>
  <img :src="degrade" alt="" class="pointer-events-none absolute left-0 top-[701px] h-[432px] w-[1920px] max-w-none object-cover" />
  <Entete veille />
  <Telecommande class="absolute left-[57px] top-[914.39px]" />
  <p v-if="props.photo?.credit" class="absolute left-[8px] font-atlas text-[14px] text-white/45" :style="{ bottom: `${basCredit}px` }">{{ props.photo.credit }}</p>
</template>
