<script setup>
import Entete from "../../components/Entete.vue";
import Fond from "../../components/transport/Fond.vue";
import Bande from "../../components/transport/Bande.vue";
import Ligne from "../../components/transport/Ligne.vue";
import Heure from "../../components/transport/Heure.vue";
import Occupation from "../../components/transport/Occupation.vue";
import { useTransit } from "../../composables/useTransit.js";
import { texteDepart } from "../../lib/temps.js";

/** Figma « Screen - Transport - EXO » : prochain train de chaque ligne au départ de Lucien-L'Allier. */
const { exo } = useTransit();
</script>

<template>
  <Fond />
  <Entete />
  <Bande reseau="exo" />
  <div class="absolute left-[31.53px] top-[234px] flex w-[1850.47px] flex-col items-start gap-[47px]">
    <Ligne v-for="t in exo" :key="t.ligne" :code="t.ligne" :couleur="t.couleur" :texte="t.texte" :direction="t.direction" :arret="t.arret" :accessible="t.accessible">
      <Heure v-if="t.annule" etat="annule" texte="Annulé" />
      <Heure v-else :texte="texteDepart(t)" :en-direct="t.temps_reel" />
      <Occupation niveau="NO_DATA" />
    </Ligne>
    <p v-if="!exo.length" class="font-satoshi text-[32px] font-black text-white">Horaires des trains en chargement…</p>
  </div>
</template>
