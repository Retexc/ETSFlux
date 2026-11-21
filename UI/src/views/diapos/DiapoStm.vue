<script setup>
import { computed } from "vue";
import Entete from "../../components/Entete.vue";
import Fond from "../../components/transport/Fond.vue";
import Bande from "../../components/transport/Bande.vue";
import Ligne from "../../components/transport/Ligne.vue";
import Heure from "../../components/transport/Heure.vue";
import Occupation from "../../components/transport/Occupation.vue";
import { useTransit } from "../../composables/useTransit.js";
import { heureQuebec, texteMinutes } from "../../lib/temps.js";

/** Figma « Screen - Transport - STM » : prochains passages des lignes 61 et 36 près de l'ÉTS. */
const { buses, erreur } = useTransit();

// Minutes (temps réel) d'abord, puis les heures prévues
const lignes = computed(() => [...buses.value].sort((a, b) => {
  const x = a.arrival_time, y = b.arrival_time;
  if (typeof x === "number" && typeof y === "number") return x - y;
  return typeof x === "number" ? -1 : typeof y === "number" ? 1 : String(x).localeCompare(String(y));
}).slice(0, 4));

const heure = (b) => (typeof b.arrival_time === "number" ? texteMinutes(b.arrival_time) : heureQuebec(b.arrival_time));
const enDirect = (b) => typeof b.arrival_time === "number" && b.service_status !== "scheduled";
</script>

<template>
  <Fond />
  <Entete />
  <Bande reseau="stm" />
  <div class="absolute left-[31.53px] top-[234px] flex w-[1850.47px] flex-col items-start gap-[47px]">
    <Ligne v-for="b in lignes" :key="`${b.route_id}-${b.direction}-${b.trip_id}`" :code="String(b.route_id)" couleur="#6e2379" texte="#ffffff"
      :direction="b.direction" :arret="b.location" :accessible="!!b.wheelchair_accessible" vehicule>
      <Heure v-if="b.cancelled" etat="annule" texte="Annulé" />
      <Heure v-else :texte="heure(b)" :en-direct="enDirect(b)" />
      <Occupation :niveau="b.cancelled ? 'NO_DATA' : b.occupancy" />
    </Ligne>
    <p v-if="!lignes.length" class="font-satoshi text-[32px] font-black text-white">{{ erreur || "Chargement des passages…" }}</p>
  </div>
</template>
