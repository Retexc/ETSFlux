<script setup>
import { computed } from "vue";
import qrcode from "qrcode-generator";
import logoNoir from "../../assets/figma/logo-ameux-noir.svg";
import logoBlanc from "../../assets/figma/logo-ameux-veille.svg";

/**
 * Annonce simple faite dans AMÉUX Flux (Figma « TV - Code QR ») : texte sur une couleur ou un dégradé,
 * petite ligne facultative, et à droite une image (carrée ou en affiche) ou un code QR.
 * Mêmes mesures que l'aperçu du site (components/affichage/diapo-simple.tsx), ici en pixels 1920 × 1080.
 */
const props = defineProps({
  simple: { type: Object, required: true },   // { texte, sousTexte, fond: { de, a }, encadre, format, lien }
  url: { type: String, default: null },        // image de l'encadré
});

const COULEUR = /^#[0-9a-f]{6}$/i;
const fond = computed(() => {
  const de = COULEUR.test(props.simple.fond?.de) ? props.simple.fond.de : "#0b2147";
  const a = COULEUR.test(props.simple.fond?.a ?? "") ? props.simple.fond.a : null;
  return { de, a };
});

// Texte blanc ou noir : le plus lisible sur toutes les couleurs du fond (même calcul que le site)
function luminance(hex) {
  return [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4))
    .reduce((s, c, i) => s + c * [0.2126, 0.7152, 0.0722][i], 0);
}
const contraste = (a, b) => { const [x, y] = [luminance(a), luminance(b)].sort((m, n) => n - m); return (x + 0.05) / (y + 0.05); };
const blanc = computed(() => {
  const couleurs = [fond.value.de, ...(fond.value.a ? [fond.value.a] : [])];
  const pire = (t) => Math.min(...couleurs.map((c) => contraste(t, c)));
  return pire("#ffffff") >= pire("#000000");
});

const css = computed(() => (fond.value.a ? `linear-gradient(135deg, ${fond.value.de} 0%, ${fond.value.a} 100%)` : fond.value.de));
const image = computed(() => props.simple.encadre === "image" && !!props.url);
const qr = computed(() => {
  if (props.simple.encadre !== "qr" || !props.simple.lien) return null;
  const q = qrcode(0, "M");
  q.addData(props.simple.lien);
  q.make();
  return q.createSvgTag({ cellSize: 8, margin: 0, scalable: true });
});
const encadre = computed(() => image.value || !!qr.value);
const affiche = computed(() => image.value && props.simple.format === "affiche");
</script>

<template>
  <div class="absolute inset-0 overflow-hidden" :style="{ background: css, color: blanc ? '#ffffff' : '#000000' }">
    <img :src="blanc ? logoBlanc : logoNoir" alt="AMÉUX" class="absolute left-[68px] top-[96px] h-[29px] w-auto" />
    <div class="absolute inset-y-0 left-[68px] flex flex-col justify-center" :style="{ width: encadre ? '960px' : '1690px' }">
      <p class="whitespace-pre-line font-satoshi text-[54px] font-black leading-[1.3]">{{ props.simple.texte }}</p>
      <p v-if="props.simple.sousTexte" class="mt-[24px] font-atlas text-[28px] font-medium leading-[1.35] opacity-75">{{ props.simple.sousTexte }}</p>
    </div>
    <div v-if="encadre" class="absolute right-[90px] top-1/2 -translate-y-1/2 overflow-hidden rounded-[44px] bg-white"
      :class="affiche ? 'h-[840px] w-[560px]' : 'size-[600px]'">
      <img v-if="image" :src="props.url" alt="" class="size-full object-cover" />
      <!-- SVG produit ici par qrcode-generator : le lien y est encodé en carrés, jamais inséré comme texte -->
      <div v-else class="qr size-full p-[50px]" v-html="qr" />
    </div>
  </div>
</template>

<style scoped>
.qr :deep(svg) { width: 100%; height: 100%; }
</style>
