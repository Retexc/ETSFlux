<script setup>
import { computed } from "vue";
import Defilant from "./Defilant.vue";
import { useTransit } from "../composables/useTransit.js";

/** Alertes STM (réseau, lignes 61 et 36, métro) : seulement sur les diapositives de transport. */
const { alerts } = useTransit();
const cle = (a) => `${a.header}-${a.description}-${a.routes}-${a.alert_type || ""}`;

const textes = computed(() => alerts.value
  .filter((a, i, arr) => arr.findIndex((b) => cle(b) === cle(a)) === i)
  .map((a) => {
    if (a.alert_type === "general_network") return `🚨 Réseau STM : ${a.header} - ${a.description}`;
    if (a.alert_type === "route_specific") return `🚌 Ligne(s) ${a.routes} : ${a.header} - ${a.description}`;
    if (a.alert_type === "metro") return `🚇 ${a.header} : ${a.description}`;
    return `${a.header} : ${a.description}`;
  }));
</script>

<template>
  <Defilant :textes="textes" fond="linear-gradient(135deg, #ff8c00, #ff6b00)" couleur="#000000" icone="alerte" />
</template>
