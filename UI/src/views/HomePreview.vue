<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import { motion } from "motion-v";
import Preview from "../components/Preview.vue";
import { useRouter } from "vue-router";

const running = ref(false);
const showMobileWarning = ref(false); //  State for warning modal
let statusTimer = null;

async function updateStatus() {
  try {
    const resp = await fetch("/admin/status");
    const { running: isUp } = await resp.json();
    running.value = isUp;
  } catch (e) {
    console.error("Error fetching status:", e);
  }
}

//  Function to handle click
function handleAccessClick() {
  // Check if screen is small (Mobile/Tablet < 768px)
  if (window.innerWidth < 768) {
    showMobileWarning.value = true;
  } else {
    // Desktop? Go straight there
    goToExternal();
  }
}

function goToExternal() {
  showMobileWarning.value = false; // Close modal if open
  const displayUrl = `${window.location.protocol}//${window.location.host}/display`;
  window.open(displayUrl, "_blank", "noopener");
}

onMounted(() => {
  updateStatus();
  statusTimer = setInterval(updateStatus, 2000);
});
onBeforeUnmount(() => {
  clearInterval(statusTimer);
});
</script>

<template>
  <div class="flex flex-col h-full overflow-hidden relative bg-[#F0F0F0]">
    
    <motion.div
      :initial="{ opacity: 0, y: 20, filter: 'blur(10px)' }"
      :animate="{
        opacity: 1,
        y: 0,
        filter: 'blur(0px)',
        transition: { duration: 0.6 },
      }"
      class="flex-1 relative overflow-hidden"
    >
      <Preview />
    </motion.div>

    <div class="md:hidden w-full p-4 bg-[#f3f4f6] shrink-0 z-20">
      <button
        @click="handleAccessClick"
        class="w-full py-4 bg-[#3B82F6] hover:bg-[#2563EB] text-black font-bold rounded-lg text-lg shadow-lg flex items-center justify-center gap-2"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
          <path fill-rule="evenodd" d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5"/>
          <path fill-rule="evenodd" d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0z"/>
        </svg>
        Accéder à l'afficheur
      </button>
    </div>

    <button
      @click="handleAccessClick"
      class="hidden md:flex flex-row items-center gap-1.5 px-4 bg-blue-400 font-black rounded-2xl p-2 absolute bottom-12 left-12 z-30 hover:bg-blue-500 transition-colors text-black shadow-lg"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
        <path fill-rule="evenodd" d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5"/>
        <path fill-rule="evenodd" d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0z"/>
      </svg>
      Accéder au tableau
    </button>

    <div v-if="showMobileWarning" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div class="bg-white rounded-2xl p-6 max-w-sm w-full shadow-2xl text-center">
        <div class="mx-auto w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h3 class="text-xl font-bold text-gray-900 mb-2">Attention</h3>
        <p class="text-gray-600 mb-6">
          L'affichage est optimisé pour les télévisions et les grands écrans. L'expérience sur mobile peut être inadaptée.
        </p>
        <div class="flex flex-col gap-3">
          <button @click="goToExternal" class="w-full py-3 bg-[#E4022C] text-white font-bold rounded-lg hover:bg-[#c00225]">
            Continuer quand même
          </button>
          <button @click="showMobileWarning = false" class="w-full py-3 bg-gray-100 text-gray-700 font-bold rounded-lg hover:bg-gray-200">
            Annuler
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
:host {
  display: block;
  height: 100%;
}
</style>