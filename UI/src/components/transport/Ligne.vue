<script setup>
import direction from "../../assets/figma/direction.svg";
import accessible from "../../assets/figma/accessible.svg";
import bus from "../../assets/figma/bus.svg";
import busMasque from "../../assets/figma/bus-masque.svg";

/**
 * Une ligne de passage (composant « Bus Line » de la maquette) : pastille de la ligne, direction, arrêt,
 * puis à droite ce que la diapositive y met (heure, achalandage, accessibilité, type de véhicule).
 */
const props = defineProps({
  code: { type: String, required: true },
  couleur: { type: String, default: "#6e2379" },
  texte: { type: String, default: "#ffffff" },
  direction: { type: String, default: "" },
  arret: { type: String, default: "" },
  accessible: { type: Boolean, default: false },
  vehicule: { type: Boolean, default: false },  // icône d'autobus (STM)
});
</script>

<template>
  <div class="flex h-[90px] w-[1850.47px] shrink-0 items-center justify-between rounded-[10.648px] bg-white px-[30px] py-[11px]">
    <div class="flex min-w-0 items-center gap-[24px]">
      <div class="flex w-[84.003px] shrink-0 items-start justify-center rounded-[9.874px] px-[18.262px] py-[14.609px]" :style="{ background: props.couleur }">
        <p class="whitespace-nowrap font-satoshi text-[26.297px] font-black" :style="{ color: props.texte }">{{ props.code }}</p>
      </div>
      <div class="flex min-w-0 flex-col justify-center gap-[6.477px]">
        <div class="flex items-center gap-[8px]">
          <img :src="direction" alt="" class="size-[18.412px] shrink-0" />
          <p class="truncate font-satoshi text-[19.885px] font-black text-black">{{ props.direction }}</p>
        </div>
        <p v-if="props.arret" class="truncate font-atlas text-[19.885px] font-medium text-black">{{ props.arret }}</p>
      </div>
    </div>
    <div class="flex shrink-0 items-center gap-[31.01px]">
      <slot />
      <img v-if="props.accessible" :src="accessible" alt="Accessible" class="size-[39.063px]" />
      <div v-if="props.vehicule" class="flex size-[39.063px] items-center justify-center rounded-[7.813px] bg-[#3ec342] px-[6.511px] py-[2.604px]">
        <div class="size-[31.251px]" :style="{ maskImage: `url(${busMasque})`, WebkitMaskImage: `url(${busMasque})`, maskSize: '31.251px 31.251px', WebkitMaskSize: '31.251px 31.251px' }">
          <img :src="bus" alt="Autobus" class="size-full" />
        </div>
      </div>
    </div>
  </div>
</template>
