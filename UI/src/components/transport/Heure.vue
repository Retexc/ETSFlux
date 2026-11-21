<script setup>
import rss from "../../assets/figma/rss.svg";

/**
 * Pastille de l'heure (composant « Time » de la maquette) : « 10 min » + icône « en direct », ou
 * « Annulé » / « Interruption de service » en rose, ou « Service normal » en vert (REM).
 */
const props = defineProps({
  texte: { type: String, required: true },
  enDirect: { type: Boolean, default: false },
  etat: { type: String, default: "heure" },   // heure | annule | interruption | normal
});
</script>

<template>
  <div v-if="props.etat === 'heure'" class="flex h-[51.683px] w-[160.79px] shrink-0 items-center justify-center rounded-[13.782px] bg-white px-[9.403px] py-[7.835px]">
    <div class="flex items-start justify-end gap-[2px]">
      <p class="whitespace-nowrap font-satoshi text-[24px] font-black text-black">{{ props.texte }}</p>
      <img v-if="props.enDirect" :src="rss" alt="" class="size-[18.777px]" />
    </div>
  </div>
  <div v-else-if="props.etat === 'annule'" class="flex h-[51.683px] w-[160.79px] shrink-0 items-center justify-center rounded-[12px] bg-[#ff5675] px-[8.187px] py-[6.822px]">
    <p class="whitespace-nowrap font-satoshi text-[27.564px] font-black text-black">{{ props.texte }}</p>
  </div>
  <div v-else-if="props.etat === 'interruption'" class="flex h-[45px] min-w-[230px] w-[310px] shrink-0 items-center justify-center rounded-[12px] bg-[#ff5675] px-[8.187px] py-[6.822px]">
    <p class="whitespace-nowrap font-satoshi text-[24px] font-black text-black">{{ props.texte }}</p>
  </div>
  <div v-else class="flex h-[51.683px] min-w-[220px] shrink-0 items-center justify-center rounded-[12px] bg-[#3dc342] px-[8.187px] py-[6.822px]">
    <p class="whitespace-pre font-satoshi text-[27.564px] font-black text-black">{{ props.texte }}</p>
  </div>
</template>
