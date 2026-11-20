<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue";
import { useTransit } from "../composables/useTransit.js";

const currentDate = ref('');
const currentTime = ref('');
// Météo lue une seule fois pour tout l'écran (composables/useTransit.js)
const { weather } = useTransit();

// Holiday Logic
const holidayMessage = ref(null);
const showWeather = ref(true);

const checkHoliday = () => {
  const now = new Date();
  const month = now.getMonth() + 1; // 1-12
  const day = now.getDate(); // 1-31

  // 1. New Year (Jan 1-7)
  if (month === 1 && day <= 7) {
    const year = now.getFullYear();
    holidayMessage.value = `Bonne année ${year} ! 🎉`;
    return;
  }
  
  // 2. Saint-Valentin (Feb 14)
  if (month === 2 && day === 14) {
    holidayMessage.value = "Joyeuse Saint-Valentin ! ❤️";
    return;
  }
  
  // 3. Saint-Jean-Baptiste / Fête Nationale (June 24)
  if (month === 6 && day === 24) {
    holidayMessage.value = "Bonne Saint-Jean ! ⚜️";
    return;
  }
  
  // 4. Canada Day (July 1)
  if (month === 7 && day === 1) {
    holidayMessage.value = "Bonne fête du Canada ! 🇨🇦";
    return;
  }
  
  // 5. Halloween (Oct 31)
  if (month === 10 && day === 31) {
    holidayMessage.value = "Joyeuse Halloween ! 🎃";
    return;
  }
  
  // 6. Christmas (Dec 25)
  if (month === 12 && day === 25) {
    holidayMessage.value = "Joyeux Noël ! 🎄";
    return;
  }
  
  // 7. Holiday Season (Dec 20 - Jan 5)
  // Check if we are in Dec (>= 20) OR Jan (<= 5)
  const isDecHolidays = month === 12 && day >= 20;
  const isJanHolidays = month === 1 && day <= 5;
  
  if (isDecHolidays || isJanHolidays) {
    holidayMessage.value = "Joyeuses fêtes ! ❄️";
    return;
  }

  // No holiday
  holidayMessage.value = null;
};

let dateInterval = null;
let timeInterval = null;
let displayInterval = null;

const updateTime = () => {
  currentTime.value = new Date().toLocaleTimeString('fr-CA', { hour: '2-digit', minute: '2-digit', timeZone: 'America/Toronto' });
};

const updateDate = () => {
  currentDate.value = new Date().toLocaleDateString('fr-CA', { weekday: 'long', day: 'numeric', month: 'long', timeZone: 'America/Toronto' });
  checkHoliday();
};

onMounted(() => {
  updateDate();
  updateTime();
  dateInterval = setInterval(updateDate, 60000);
  timeInterval = setInterval(updateTime, 1000);
  // Alterne météo et message de fête toutes les 10 secondes
  displayInterval = setInterval(() => {
    showWeather.value = holidayMessage.value ? !showWeather.value : true;
  }, 10000);
});

onBeforeUnmount(() => {
  clearInterval(dateInterval);
  clearInterval(timeInterval);
  clearInterval(displayInterval);
});
</script>

<template>
  <div class="flex flex-row justify-between items-center bg-white p-2 py-4 h-24">
    <!-- LEFT SIDE: Logo + Weather/Holiday -->
    <div class="flex flex-row items-center gap-4 ml-6">
      <img src="../assets/icons/ETS.svg" alt="ETS Logo" class="w-16"></img>
      
      <!-- Content Section with Transition -->
      <!-- Fixed width container to prevent layout jumping? Or let it flow. -->
      <div class="relative h-10 min-w-[300px] flex items-center">
        <Transition name="fade" mode="out-in">
          <!-- Weather -->
          <div 
            v-if="showWeather || !holidayMessage" 
            key="weather"
            class="flex flex-row items-center gap-2 absolute left-0"
          >
            <div v-if="weather.icon" class="flex flex-row items-center gap-2">
              <img :src="weather.icon" :alt="weather.text" class="w-8 h-8" />
              <span class="text-black font-bold text-3xl whitespace-nowrap">
                {{ weather.temp }}°C {{ weather.text }}
              </span>
            </div>
          </div>
          
          <!-- Holiday Message -->
          <div 
            v-else 
            key="holiday"
            class="flex flex-row items-center gap-2 absolute left-0"
          >
             <span class="text-black font-bold text-3xl whitespace-nowrap">
                {{ holidayMessage }}
             </span>
          </div>
        </Transition>
      </div>
    </div>

    <!-- RIGHT SIDE: Date + Time -->
    <div class="flex flex-row items-center gap-4 mr-6">
      <h1 class="text-black font-bold text-3xl first-letter:uppercase">{{ currentDate }}</h1>       
      <h1 class="text-black font-bold text-3xl">{{ currentTime }}</h1>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>