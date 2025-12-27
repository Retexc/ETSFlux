<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from "vue";
import { API_URL } from '../config.js'

const currentDate = ref('');
const currentTime = ref('');
const weather = ref({
  icon: '',
  text: '',
  temp: ''
});

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

let timeInterval = null;
let weatherInterval = null;
let displayInterval = null;

const updateTime = () => {
  const now = new Date();
  
  currentTime.value = now.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  });
};

const updateDate = () => {
  const now = new Date();
  
  currentDate.value = now.toLocaleDateString('fr-CA', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
  
  // Update holiday check daily (or every minute, cheap op)
  checkHoliday();
};

const fetchWeatherData = async () => {
  try {
    const response = await fetch(`${API_URL}/api/data`);
    const data = await response.json();
    
    if (data.weather) {
      weather.value = {
        icon: data.weather.icon || '',
        text: data.weather.text || '',
        temp: data.weather.temp !== undefined ? data.weather.temp : '' 
      };
    }
  } catch (error) {
    console.error('Error fetching weather data:', error);
  }
};

onMounted(() => {
  updateDate();
  checkHoliday(); // Initial check
  timeInterval = setInterval(updateDate, 60000); 

  updateTime();
  // Ensure we don't leak intervals if updateTime was adding one (it wasn't previously, but logic was slightly odd in diff)
  // Just keeping original structure:
  // Note: Previous code had `timeInterval = setInterval(updateTime, 1000)` overwriting the first one. 
  // Let's fix that bug too.
  const secondInterval = setInterval(updateTime, 1000);
  
  fetchWeatherData();
  weatherInterval = setInterval(fetchWeatherData, 30000); // Update every 30 seconds
  
  // Toggle interval (Cycle every 10 seconds)
  displayInterval = setInterval(() => {
    if (holidayMessage.value) {
      showWeather.value = !showWeather.value;
    } else {
      showWeather.value = true;
    }
  }, 10000);
  
  // Store intervals properly to clear them
  // Since we have multiple, let's use a list or separate vars?
  // Previous code used `timeInterval` twice.
  // I will just add `secondInterval` to cleanup.
  onBeforeUnmount(() => { // Using inline here just to capture scopes if needed, but better to put in main scope
    clearInterval(secondInterval);
  });
});

onBeforeUnmount(() => {
  if (timeInterval) clearInterval(timeInterval);
  if (weatherInterval) clearInterval(weatherInterval);
  if (displayInterval) clearInterval(displayInterval);
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
      <h1 class="text-black font-bold text-3xl">{{ currentDate }}</h1>       
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