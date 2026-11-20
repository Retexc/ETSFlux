<script setup>
import { onMounted, ref } from "vue";
import { jumeler } from "../lib/flux.js";

/**
 * Écran pas encore relié à AMÉUX Flux : on tape le code affiché dans Flux (Annonces → Écran du salon →
 * « Connecter un écran »). Le code peut aussi arriver dans l'adresse (?code=…), sans clavier.
 */
const emit = defineEmits(["jumele"]);
const code = ref("");
const erreur = ref(null);
const occupe = ref(false);

async function envoyer() {
  if (occupe.value) return;
  occupe.value = true;
  erreur.value = await jumeler(code.value);
  occupe.value = false;
  if (!erreur.value) emit("jumele");
}

onMounted(() => {
  const url = new URL(window.location.href);
  const depuisAdresse = url.searchParams.get("code");
  if (depuisAdresse) {
    // Le code ne reste pas dans l'adresse ni dans l'historique
    url.searchParams.delete("code");
    window.history.replaceState(null, "", url.pathname + url.search);
    code.value = depuisAdresse;
    envoyer();
  }
});
</script>

<template>
  <div class="fixed inset-0 flex items-center justify-center bg-[#0b1d3a] text-white">
    <form class="w-[min(90vw,560px)] space-y-6 text-center" @submit.prevent="envoyer">
      <h1 class="text-4xl font-bold">Connecter cet écran</h1>
      <p class="text-xl text-white/80">Dans AMÉUX Flux : Annonces → Écran du salon → « Connecter un écran ».</p>
      <input v-model="code" autofocus autocomplete="off" spellcheck="false" maxlength="9" placeholder="XXXX-XXXX" aria-label="Code"
        class="w-full rounded-2xl bg-white px-6 py-5 text-center font-mono text-5xl font-bold uppercase tracking-[0.2em] text-black outline-none" />
      <p v-if="erreur" class="text-xl text-[#ffb4a8]">{{ erreur }}</p>
      <button type="submit" :disabled="occupe || !code"
        class="w-full rounded-2xl bg-[#00a1b3] py-4 text-2xl font-bold disabled:opacity-50">
        {{ occupe ? "Connexion…" : "Connecter" }}
      </button>
    </form>
  </div>
</template>
