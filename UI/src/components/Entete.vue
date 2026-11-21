<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useTransit } from "../composables/useTransit.js";
import logoNoir from "../assets/figma/logo-ameux-noir.svg";
import logoBlanc from "../assets/figma/logo-ameux-veille.svg";

/**
 * Bandeau du haut (Figma « ETS Flux ») : logo AMÉUX, date, météo, heure.
 * `veille` : version transparente en blanc, plus grande, posée sur la photo (écran de veille).
 */
const props = defineProps({ veille: { type: Boolean, default: false } });
const { weather } = useTransit();

const maintenant = ref(new Date());
let minuterie = null;
onMounted(() => { minuterie = setInterval(() => { maintenant.value = new Date(); }, 1000); });
onBeforeUnmount(() => clearInterval(minuterie));

const TZ = "America/Toronto";
const date = computed(() => new Intl.DateTimeFormat("fr-CA", { timeZone: TZ, weekday: "long", day: "numeric", month: "long", year: "numeric" }).format(maintenant.value));
const heure = computed(() => new Intl.DateTimeFormat("fr-CA", { timeZone: TZ, hour: "numeric", minute: "2-digit" }).format(maintenant.value));
// Icônes de WeatherAPI : version 128 px (plus nette), agrandie car le dessin n'occupe que le centre de l'image
const icone = computed(() => (weather.value?.icon || "").replace("/64x64/", "/128x128/"));
const meteo = computed(() => (weather.value?.text ? `${weather.value.temp !== "" ? `${weather.value.temp}°C ` : ""}${weather.value.text}` : ""));
</script>

<template>
  <header v-if="!props.veille" class="absolute left-0 top-0 flex h-[90px] w-[1920px] items-center justify-between bg-white px-[38px] font-satoshi text-[22.931px] font-black text-black">
    <div class="flex items-center gap-[42px]">
      <img :src="logoNoir" alt="AMÉUX" class="h-[25.257px] w-[102px]" />
      <p class="whitespace-nowrap first-letter:uppercase">{{ date }}</p>
    </div>
    <div class="flex items-center gap-[43px]">
      <div v-if="meteo" class="flex items-center gap-[18px]">
        <img v-if="icone" :src="icone" alt="" class="size-[42.45px] scale-[1.7]" />
        <p class="whitespace-nowrap">{{ meteo }}</p>
      </div>
      <p class="whitespace-nowrap">{{ heure }}</p>
    </div>
  </header>

  <header v-else class="absolute left-[57px] top-[83px] flex w-[1825px] items-center justify-between font-satoshi text-[28.32px] font-black text-white">
    <img :src="logoBlanc" alt="AMÉUX" class="h-[53px] w-[214.043px]" />
    <div class="flex items-center gap-[53.104px]">
      <div v-if="meteo" class="flex items-center gap-[22.23px]">
        <img v-if="icone" :src="icone" alt="" class="size-[52.425px] scale-[1.7]" />
        <p class="whitespace-nowrap">{{ meteo }}</p>
      </div>
      <p class="whitespace-nowrap">{{ heure }}</p>
    </div>
  </header>
</template>
