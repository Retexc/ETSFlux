<script setup>
import Entete from "../../components/Entete.vue";
import Fond from "../../components/transport/Fond.vue";
import Bande from "../../components/transport/Bande.vue";
import Ligne from "../../components/transport/Ligne.vue";
import Heure from "../../components/transport/Heure.vue";

/** Figma « Screen - Transport - REM » : état de chaque ligne, indiqué par l'équipe dans AMÉUX Flux. */
const props = defineProps({ lignes: { type: Array, default: () => [] } });
</script>

<template>
  <Fond />
  <Entete />
  <Bande reseau="rem" />
  <div class="absolute left-[31.53px] top-[234px] flex w-[1850.47px] flex-col items-start gap-[58px]">
    <Ligne v-for="l in props.lignes" :key="l.code" :code="l.code" contour :direction="l.direction" :arret="l.interruption ? (l.message || '') : ''">
      <Heure v-if="l.interruption" etat="interruption" texte="Interruption de service" />
      <Heure v-else etat="normal" :texte="'Service  normal'" />
    </Ligne>
  </div>
</template>
