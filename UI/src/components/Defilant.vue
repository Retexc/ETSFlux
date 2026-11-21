<script setup>
import { computed } from "vue";

/**
 * Bandeau qui défile en bas de l'écran. `textes` : messages mis bout à bout. Vitesse constante quelle que
 * soit la longueur (environ 120 px par seconde à 1920 px de large).
 */
const props = defineProps({
  textes: { type: Array, default: () => [] },
  fond: { type: String, default: "#004952" },
  couleur: { type: String, default: "#ffffff" },
  icone: { type: String, default: "" },   // « alerte » : triangle
});
const texte = computed(() => props.textes.filter(Boolean).join("   •••   "));
const duree = computed(() => `${Math.max(20, Math.round((texte.value.length * 15 + 1920) / 120))}s`);
</script>

<template>
  <div v-if="texte" class="relative h-[56px] w-[1920px] overflow-hidden" :style="{ background: props.fond, color: props.couleur }">
    <div class="defilement absolute inset-y-0 left-0 flex w-max items-center" :style="{ animationDuration: duree }">
      <div v-for="copie in 2" :key="copie" class="flex items-center whitespace-nowrap pr-[80px] font-satoshi text-[26px] font-black" :aria-hidden="copie === 2">
        <svg v-if="props.icone === 'alerte'" class="mr-[14px] ml-[24px] size-[28px] shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
          <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" /><path d="M12 9v4" /><path d="M12 17h.01" />
        </svg>
        <span :class="props.icone ? '' : 'ml-[24px]'">{{ texte }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.defilement { animation: defiler linear infinite; }
@keyframes defiler { from { transform: translateX(0); } to { transform: translateX(-50%); } }
@media (prefers-reduced-motion: reduce) { .defilement { animation: none; } }
</style>
