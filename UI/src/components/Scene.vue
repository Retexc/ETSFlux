<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";

/**
 * Scène de 1920 × 1080 (taille des maquettes Figma) mise à l'échelle de l'écran : les positions et tailles
 * des maquettes sont reprises telles quelles, et le rendu est le même sur toute TV 16:9.
 */
const LARGEUR = 1920;
const HAUTEUR = 1080;
const cadre = ref(null);
const echelle = ref(1);
let obs = null;

onMounted(() => {
  obs = new ResizeObserver(([e]) => {
    echelle.value = Math.min(e.contentRect.width / LARGEUR, e.contentRect.height / HAUTEUR);
  });
  obs.observe(cadre.value);
});
onBeforeUnmount(() => obs?.disconnect());
</script>

<template>
  <div ref="cadre" class="fixed inset-0 flex items-center justify-center overflow-hidden bg-black">
    <div class="relative shrink-0 overflow-hidden" :style="{ width: `${LARGEUR}px`, height: `${HAUTEUR}px`, transform: `scale(${echelle})` }">
      <slot />
    </div>
  </div>
</template>
