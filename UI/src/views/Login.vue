<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/authStore";
import { motion } from "motion-v";
import bgImg from "../assets/images/Login_bg.jpg";
import FluxLogo from "../assets/icons/etsflux.svg";
import FluxDevLogo from "../assets/icons/etsflux-dev.svg";

// 🎯 Initialisation
const router = useRouter();
const authStore = useAuthStore();

// 📝 Variables du formulaire
const email = ref("");
const password = ref("");
const loading = ref(false);
const error = ref(null);

const logo = import.meta.env.MODE === 'development' ? FluxDevLogo : FluxLogo;

// 🔐 FONCTION DE CONNEXION
async function onSubmit() {
  // Réinitialiser l'erreur
  error.value = null;
  loading.value = true;

  try {
    // Appel au store pour se connecter
    const result = await authStore.signIn(email.value, password.value);

    if (result.success) {
      // ✅ Connexion réussie !
      console.log("✅ Connexion réussie, redirection...");
      
      // Rediriger vers la page d'accueil (ou où tu veux)
      router.push("/");
    } else {
      // ❌ Erreur de connexion
      console.error("❌ Erreur Supabase complète:", result.error);
      error.value = result.error || "Identifiants incorrects";
      
      // Traduire les erreurs courantes en français
      if (error.value.includes("Invalid login credentials")) {
        error.value = "Email ou mot de passe incorrect";
      } else if (error.value.includes("Email not confirmed")) {
        error.value = "ERREUR SUPABASE: " + error.value + " - Vérifiez dans Supabase → Users que l'email est confirmé";
      }
    }
  } catch (err) {
    console.error("Erreur inattendue:", err);
    error.value = "Une erreur est survenue. Réessayez.";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
/* nothing here—everything is in utility classes */
</style>

<template>
  <div
    class="min-h-screen bg-center bg-cover bg-no-repeat"
    :style="{ backgroundImage: `url(${bgImg})` }"
  >
    <div class="flex flex-col justify-center items-center md:flex-row md:justify-start h-screen w-full">
      <!-- WHITE CARD -->
      <div class="
      bg-white
      w-[90%] md:w-1/2 lg:w-2/5
      h-auto md:h-full
      p-8 px-6 md:px-18
      rounded-2xl md:rounded-none
      shadow-2xl md:shadow-none      
      overflow-hidden flex flex-col justify-center relative">
        <motion.div
          :initial="{ opacity: 0, y: 20, filter: 'blur(10px)' }"
          :animate="{
            opacity: 1,
            y: 0,
            filter: 'blur(0px)',
            transition: { duration: 1 },
          }"
        >
        </motion.div>

        <motion.div
          :initial="{ opacity: 0, y: 20, filter: 'blur(10px)' }"
          :animate="{
            opacity: 1,
            y: 0,
            filter: 'blur(0px)',
            transition: { delay: 0.5, duration: 1 },
          }"
          class="flex flex-col items-center justify-center space-y-6 w-full text-left"
        >
          <img
            :src="logo"
            alt="ETS Logo"
            class="w-40 md:w-54 self-center md:self-start mt-2 mb-2 drop-shadow-2xl"
          />

          <div class="flex flex-col items-center md:items-start justify-center w-full mb-6">
            <h1 class="text-2xl font-bold text-center md:text-left">Heureux de vous revoir !</h1>
            <p class="text-center text-gray-700 md:text-left">Entrez vos identifiants pour vous connecter.</p>
          </div>


          <!-- 🚨 MESSAGE D'ERREUR -->
          <div
            v-if="error"
            class="w-full p-3 bg-red-100 border-2 border-red-500 text-red-700 rounded"
          >
            {{ error }}
          </div>

          <!-- Form -->
          <form
            @submit.prevent="onSubmit"
            class="w-full flex flex-col space-y-6"
          >
            <div class="flex flex-col gap-1">
            <label class="font-semibold text-base ml-1">Adresse courriel</label>
            <input
              v-model="email"
              type="email"
              placeholder="votre.email@etsmtl.ca"
              required
              :disabled="loading"
              class="w-full p-3 bg-transparent border-2 border-[#535353] text-black placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#E4022C] text-sm disabled:opacity-50 rounded-xl"
            />
            </div>

            <div class="flex flex-col gap-1">
            <label class="font-semibold text-base ml-1">Mot de passe</label>
            <input
              v-model="password"
              type="password"
              placeholder="Mot de passe"
              required
              :disabled="loading"
              class="w-full p-3 bg-transparent border-2 border-[#535353] text-black placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#E4022C] text-sm disabled:opacity-50 rounded-xl"
            />              
            </div>


            <button
              type="submit"
              :disabled="loading"
              class="w-full py-3 bg-[#E4022C] hover:bg-[#D5052C] text-white font-bold disabled:opacity-50 disabled:cursor-not-allowed transition-all rounded-xl"
            >
              {{ loading ? "Connexion en cours..." : "Connexion" }}
            </button>

            <!-- Lien vers mot de passe oublié -->
            <router-link
              to="/forgot-password"
              class="text-sm text-[#E4022C] hover:underline self-center"
            >
              Mot de passe oublié ?
            </router-link>
          </form>
        </motion.div>
      </div>
    </div>
  </div>
</template>