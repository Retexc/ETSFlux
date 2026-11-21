<script setup>
import logoStm from "../../assets/figma/logo-stm.png";
import logoExo from "../../assets/figma/logo-exo-masque.png";

/** Bande de couleur sous l'en-tête, avec le logo du réseau (Figma « Screen - Transport - STM / EXO »). */
const props = defineProps({ reseau: { type: String, required: true } });   // stm | exo
const FOND = { stm: "#e4e8fe", exo: "#f5e8d2" };
</script>

<template>
  <div class="absolute left-0 top-[90px] h-[64px] w-[1920px]" :style="{ background: FOND[props.reseau] }">
    <img v-if="props.reseau === 'stm'" :src="logoStm" alt="STM" class="absolute left-[922px] top-[15px] h-[34.222px] w-[77px] object-cover" />
    <!-- Logo exo : image en masque, peinte en noir (comme dans la maquette) -->
    <div v-else role="img" aria-label="exo" class="absolute left-[909px] top-[15px] h-[33.576px] w-[102.219px] bg-black"
      :style="{ maskImage: `url(${logoExo})`, WebkitMaskImage: `url(${logoExo})`, maskSize: '102px 33.779px', WebkitMaskSize: '102px 33.779px', maskRepeat: 'no-repeat', WebkitMaskRepeat: 'no-repeat' }" />
  </div>
</template>
