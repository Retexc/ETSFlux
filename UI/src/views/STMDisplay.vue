<script setup>
import Scene from "../components/Scene.vue";
import AlertBanner from "../components/AlertBanner.vue";
import DiapoStm from "./diapos/DiapoStm.vue";
</script>

<!-- /stm : prochains passages STM en plein écran, sans les annonces -->
<template>
  <Scene>
    <DiapoStm />
    <div class="absolute bottom-0 left-0 w-[1920px]"><AlertBanner /></div>
  </Scene>
</template>
