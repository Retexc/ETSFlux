<script setup>
import STMBloc from "../components/STMBloc.vue";
import AlertBanner from "../components/AlertBanner.vue";
</script>

<!-- /stm : prochains passages en plein écran, sans les annonces -->
<template>
  <div class="fixed inset-0 bg-black">
    <STMBloc />
    <AlertBanner />
  </div>
</template>
