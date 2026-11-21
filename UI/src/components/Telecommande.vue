<script setup>
import telecommande from "../assets/figma/telecommande.svg";

/** Notice « Appuyer sur n'importe quelle touche… » (Figma « Screen - Art »). */
</script>

<template>
  <div class="flex items-center gap-[4.481px] px-[10.241px]">
    <img :src="telecommande" alt="" class="size-[65.288px] shrink-0" />
    <div class="whitespace-nowrap font-satoshi text-[30.724px] font-black text-white">
      <p>Appuyer sur n’importe quelle touche de la télécommande</p>
      <p>pour quitter l’afficheur automatique</p>
    </div>
  </div>
</template>
