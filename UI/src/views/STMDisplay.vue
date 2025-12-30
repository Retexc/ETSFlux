<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import BusRow from "../components/BusRow.vue";
import MetroRow from "../components/MetroRow.vue";
import STMLogo from "../assets/icons/STM.png";
import Background from "../assets/images/Login_bg.jpg";
import AlertBanner from "../components/AlertBanner.vue";
import { API_URL } from "../config.js";

// Data from the API
const buses = ref([]);
const metroLines = ref([]);
const loading = ref(true);
const error = ref(null);
const showContent = ref(false); // Pour contrôler l'affichage du contenu

const baseWidth = 1920;  
const baseHeight = 1080; 
const scale = ref(1);
const contentRef = ref(null);

const updateScale = () => {

  const availableWidth = window.innerWidth;
  const availableHeight = window.innerHeight;

  const scaleX = availableWidth / baseWidth;
  const scaleY = availableHeight / baseHeight;

  scale.value = Math.min(scaleX, scaleY); 
};

// Sort buses by arrival time
const sortedBuses = computed(() => {
  return [...buses.value].sort((a, b) => {
    const timeA = a.arrival_time;
    const timeB = b.arrival_time;

    if (typeof timeA === "number" && typeof timeB === "number") {
      return timeA - timeB;
    }

    if (typeof timeA === "string" && typeof timeB === "string") {
      return timeA.localeCompare(timeB);
    }

    if (typeof timeA === "number") return -1;
    if (typeof timeB === "number") return 1;

    return 0;
  });
});

// Function to fetch data from the backend
const fetchData = async () => {
  try {
    const response = await fetch(`${API_URL}/api/data`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    buses.value = data.buses || [];
    metroLines.value = data.metro_lines || [];

    // Attendre un petit délai pour une transition fluide
    setTimeout(() => {
      loading.value = false;
      // Attendre que loading soit false, puis afficher le contenu
      setTimeout(() => {
        showContent.value = true;
      }, 100);
    }, 500);

    error.value = null;
  } catch (err) {
    console.error("Error fetching data:", err);
    error.value = "Unable to load transit data";
    loading.value = false;
    showContent.value = true;
  }
};

// Refresh interval (every 30 seconds)
let refreshInterval = null;

onMounted(() => {
  fetchData();
  refreshInterval = setInterval(fetchData, 30000);
  updateScale();
  window.addEventListener('resize', updateScale);
});

onBeforeUnmount(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }
});
</script>

<template>
      <div class="absolute top-5 left-0 z-50 flex flex-row justify-center w-full bg-white p-4">
      <img :src="STMLogo" alt="STM Logo" class="w-auto h-8">
    </div>
  <div 
    class="w-screen h-screen bg-black overflow-hidden flex items-center justify-center relative mt-5"
    :style="{ backgroundImage: `url(${Background})`, backgroundSize: 'cover' }"
  >
    <div
      ref="contentRef"
      class="relative flex flex-col px-8 pt-28 pb-4 gap-4 box-border origin-center"
      :style="{
        width: `${baseWidth}px`,
        height: `${baseHeight}px`,
        transform: `scale(${scale})`
      }"
    >
      <bus-row v-for="bus in sortedBuses" :key="bus.trip_id" :bus="bus" />
      
      <div v-if="metroLines.length > 0" class="h-px bg-white/30 my-2 mx-4"></div>
      
      <metro-row v-for="line in metroLines" :key="line.name" :line="line" />

    </div>
    
  </div>
</template>

<style scoped>
/* Animation personnalisée pour le logo */
@keyframes logo-bounce {
  0%,
  100% {
    transform: translateY(0) scale(1);
  }
  50% {
    transform: translateY(-10px) scale(1.05);
  }
}

.animate-logo-bounce {
  animation: logo-bounce 2s ease-in-out infinite;
}

/* Bus list transitions */
.bus-list-move,
.bus-list-enter-active,
.bus-list-leave-active {
  transition: all 0.6s ease-out;
}

.bus-list-enter-from {
  opacity: 0;
  transform: translateX(-2rem);
}

.bus-list-leave-to {
  opacity: 0;
  transform: translateX(2rem);
}

.bus-list-leave-active {
  position: absolute;
  left: 2rem;
  width: calc(100% - 4rem);
}

/* Metro list transitions */
.metro-list-move,
.metro-list-enter-active,
.metro-list-leave-active {
  transition: all 0.6s ease-out;
}

.metro-list-enter-from {
  opacity: 0;
  transform: translateX(-2rem);
}

.metro-list-leave-to {
  opacity: 0;
  transform: translateX(2rem);
}

.metro-list-leave-active {
  position: absolute;
  left: 2rem;
  width: calc(100% - 4rem);
}
</style>
