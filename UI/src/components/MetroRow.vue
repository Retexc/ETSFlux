<script setup>
import { ref, computed } from "vue";
import greenLine from '../assets/icons/green-line.svg'
import yellowLine from '../assets/icons/yellow-line.svg'
import blueLine from '../assets/icons/blue-line.svg'
import orangeLine from '../assets/icons/orange-line.svg'

const props = defineProps({
  line: {
    type: Object,
    required: true,
  }
});

const iconMap = {
  'green-line': greenLine,
  'yellow-line': yellowLine,
  'blue-line': blueLine,
  'orange-line': orangeLine
};

const lineIcon = computed(() => iconMap[props.line.icon] || greenLine);

const cleanStatus = computed(() => {
  if (!props.line.status) return "Information non disponible";
  
  let cleanText = props.line.status.replace(/<[^>]*>/g, '');
  return cleanText;
});

// Only show green status pill when service is normal
const showGreenStatus = computed(() => {
  return props.line.is_normal === true && props.line.status && props.line.status.trim() !== "";
});

// Determine status color based on content and is_normal flag
const statusColor = computed(() => {
  if (props.line.statusColor) {
    return props.line.statusColor;
  }
  
  if (props.line.is_normal === false) {
    return "text-red-400";
  }
  
  if (props.line.is_normal === true) {
    return "text-black";
  }
  
  const statusLower = (props.line.status || '').toLowerCase();
  if (statusLower.includes('service normal') || statusLower.includes('normal service')) {
    return "text-black ";
  }
  
  // Default to red for any other status
  return "text-red-400";
});
</script>

<template>
  <div class="w-full flex flex-row justify-between items-center bg-[#FFFFFF] rounded-xl px-4 md:px-6 py-3 gap-4">
    
    <div class="flex flex-row items-center gap-4 md:gap-6 flex-1 min-w-0">
      
      <img 
        :src="lineIcon" 
        :alt="`${props.line.color} line`" 
        class="w-12 h-12 ml-4 md:w-16 md:h-16 shrink-0" 
      />

      <div class="flex flex-col text-black font-bold opacity-90 rounded-xl min-w-0 ml-10">
        <div class="flex flex-row items-center gap-2">
          <h1 class="text-xl md:text-2xl truncate">{{ props.line.name }}</h1>       
        </div>
        <h1 class="text-lg md:text-xl truncate">{{ props.line.color }}</h1>
      </div>
    </div>

    <div class="flex flex-row items-center shrink-0">
      <div class="flex flex-col items-end">
        
        <h1 v-if="showGreenStatus" class="font-bold text-lg md:text-xl bg-green-500 rounded-xl text-black px-3 md:px-4 py-1.5 whitespace-nowrap">
          {{ cleanStatus }}
        </h1>
        
        <div v-if="!props.line.is_normal" class="flex items-center gap-2 md:gap-4 mt-1">
          <div class="w-3 h-3 md:w-4 md:h-4 bg-red-400 rounded-full animate-pulse shrink-0"></div>
          <span class="font-bold text-lg md:text-xl bg-red-400 rounded-xl text-black px-3 md:px-4 py-1.5 whitespace-nowrap">
            Service perturbé
          </span>
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped>
</style>