<script setup>
import logoStm from "../../assets/figma/logo-stm.png";
import logoExo from "../../assets/figma/logo-exo-masque.png";
import logoRem from "../../assets/figma/logo-rem.svg";

/** Bande de couleur sous l'en-tête, avec le logo du réseau (Figma « Screen - Transport - STM / EXO / REM »). */
const props = defineProps({ reseau: { type: String, required: true } });   // stm | exo | rem
const FOND = { stm: "#e4e8fe", exo: "#f5e8d2", rem: "#eafee7" };
</script>

<template>
  <div class="absolute left-0 top-[90px] h-[64px] w-[1920px]" :style="{ background: FOND[props.reseau] }">
    <img v-if="props.reseau === 'stm'" :src="logoStm" alt="STM" class="absolute left-[922px] top-[15px] h-[34.222px] w-[77px] object-cover" />
    <!-- Logo exo : image en masque, peinte en noir (comme dans la maquette) -->
    <div v-else-if="props.reseau === 'exo'" role="img" aria-label="exo" class="absolute left-[909px] top-[15px] h-[33.576px] w-[102.219px] bg-black"
      :style="{ maskImage: `url(${logoExo})`, WebkitMaskImage: `url(${logoExo})`, maskSize: '102px 33.779px', WebkitMaskSize: '102px 33.779px', maskRepeat: 'no-repeat', WebkitMaskRepeat: 'no-repeat' }" />
    <img v-else :src="logoRem" alt="REM" class="absolute left-[calc(50%+0.5px)] top-[9px] h-[46px] w-[73px] -translate-x-1/2" />
  </div>
</template>
