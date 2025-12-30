<script>
import { ref, computed, onMounted, watch } from "vue";
import { useAnnonceStore } from '../stores/annonceStore.js'
import draggable from 'vuedraggable'
import { supabase } from '../lib/supabaseClient.js'
import { useRouter } from "vue-router";
import FluxLogo from "../assets/icons/etsflux.svg";

export default {
  name: "AnnonceEditorWithMedia",
  components: {
    draggable
  },
  setup() {
    const router = useRouter();
    const annonceStore = useAnnonceStore()
    
    // MOBILE TABS STATE
    const currentTab = ref('ordre'); // 'ordre', 'media', 'duree', 'style'

    const pageActive = ref(1);
    const fileInput = ref(null);
    const isUploading = ref(false);
    const editingPageId = ref(null);
    const tempPageName = ref("");

    // Charger les annonces
    onMounted(async () => {
      await annonceStore.chargerAnnonces()
      // Create a local copy
      let currentAnnonces = [...annonceStore.annonces];
      
      // Check if STM Display page exists, if not add it
      const hasStmPage = currentAnnonces.some(a => a.type === 'stm');
      if (!hasStmPage) {
        console.log("Creating default STM page...");
        const stmPage = {
          id: 'stm-display',
          type: 'stm',
          nom: "Affichage Transport",
          enabled: true, 
          dureeAffichage: 15,
          transition: "fade",
          modeAffichage: "cover",
          linkURL: "https://etsignage.onrender.com/stm", 
          media: null,
          mediaType: null
        };
        currentAnnonces.push(stmPage);
      } else {
        // Ensure legacy STM pages have enabled property if missing
         currentAnnonces = currentAnnonces.map(a => {
            if (a.type === 'stm' && a.enabled === undefined) {
               return { ...a, enabled: true };
            }
            return a;
         });
      }
      
      annonces.value = currentAnnonces;
      
      // Select first page
      if (annonces.value.length > 0 && !annonces.value.find(a => a.id === pageActive.value)) {
         pageActive.value = annonces.value[0].id;
      }
    })

    const annonces = ref([
      {
        id: 1,
        nom: "Page 1",
        dureeAffichage: 5,
        transition: "fade",
        modeAffichage: "cover",
      },
    ]);

    // Sauvegarde automatique
    watch(annonces, async (newAnnonces) => {
      const annoncesToSave = newAnnonces.map(a => {
        // We need to keep type and enabled properties for persistence
        const { mediaURL, ...rest } = a
        return rest
      })
      await annonceStore.sauvegarderAnnonces(annoncesToSave)
    }, { deep: true })

    const pageSelectionnee = computed(() => {
      return annonces.value.find((a) => a.id === pageActive.value);
    });

    const ajouterPage = () => {
      const nouvelId = Date.now();
      // Ensure we don't accidentally create an STM type page
      const nouvellePage = {
        id: nouvelId,
        type: 'standard', // Explicitly mark as standard

        nom: `Page ${annonces.value.length + 1}`,
        media: null,
        mediaURL: null,
        mediaType: null,
        dureeAffichage: 5,
        transition: "fade",
        modeAffichage: "cover",
        loop: false,
        linkURL: "",
        dureeDebut: "",
        dureeFin: ""
      };
      annonces.value.push(nouvellePage);
      pageActive.value = nouvelId;
    };

    const supprimerPage = async (id) => {
      const pageToDelete = annonces.value.find(a => a.id === id);
      
      // Prevent deleting STM page
      if (pageToDelete && pageToDelete.type === 'stm') {
         alert("La page STM Display ne peut pas être supprimée. Vous pouvez la désactiver.");
         return;
      }

      if (pageToDelete && pageToDelete.media) {
        try {
          await supabase.storage.from('backgrounds').remove([pageToDelete.media]);
        } catch (error) { console.error(error); }
      }
      annonces.value = annonces.value.filter((a) => a.id !== id);
      if (pageActive.value === id) {
        pageActive.value = annonces.value.length > 0 ? annonces.value[0].id : null;
      }
    };

    const ouvrirSelecteurFichier = () => { if (fileInput.value) fileInput.value.click(); };

    const gererUploadFichier = async (event) => {
      const file = event.target.files[0];
      if (!file || !pageSelectionnee.value) return;

      if (file.size > 500 * 1024 * 1024) {
        alert("Fichier trop volumineux (Max 500MB)");
        return;
      }

      isUploading.value = true;
      try {
        let mediaType = null;
        if (file.type.startsWith("image/")) mediaType = "image";
        else if (file.type.startsWith("video/")) mediaType = "video";
        else if (file.type === "application/pdf") mediaType = "pdf";

        if (!mediaType) { alert("Format non supporté"); isUploading.value = false; return; }

        if (pageSelectionnee.value.media) {
           await supabase.storage.from('backgrounds').remove([pageSelectionnee.value.media]).catch(e => console.log(e));
        }

        const fileName = `${Date.now()}-${file.name.replace(/[^a-zA-Z0-9.-]/g, '_')}`;
        const { error } = await supabase.storage.from('backgrounds').upload(fileName, file);
        
        if (error) throw error;

        // Get URL (Mock returns path in DEV, Real returns public URL in PROD)
        const { data: urlData } = supabase.storage.from('backgrounds').getPublicUrl(fileName);
        let finalMediaUrl = urlData.publicUrl;

        // DEV MODE: Use local blob for immediate preview (since mock URL is just a path)
        if (import.meta.env.DEV) {
           console.log("🔧 DEV MODE: Using local blob for immediate preview");
           finalMediaUrl = URL.createObjectURL(file);
        }

        pageSelectionnee.value.media = fileName;
        pageSelectionnee.value.mediaURL = finalMediaUrl;
        pageSelectionnee.value.mediaType = mediaType;
        pageSelectionnee.value.mediaName = file.name;
        pageSelectionnee.value.mediaSize = file.size;

      } catch (error) {
        console.error(error);
        alert("Erreur upload");
      } finally {
        isUploading.value = false;
        event.target.value = "";
      }
    };

    const supprimerMedia = async () => {
      if (!pageSelectionnee.value) return;
      if (pageSelectionnee.value.media) {
         await supabase.storage.from('backgrounds').remove([pageSelectionnee.value.media]);
      }
      pageSelectionnee.value.media = null;
      pageSelectionnee.value.mediaURL = null;
      pageSelectionnee.value.mediaType = null;
      pageSelectionnee.value.mediaName = null;
      pageSelectionnee.value.mediaSize = null;
    };

    const formatFileSize = (bytes) => {
      if (!bytes) return "0 Bytes";
      const k = 1024;
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + ["Bytes", "KB", "MB", "GB"][i];
    };

    const goBack = () => router.push('/');

    return {
      annonces,
      pageActive,
      pageSelectionnee,
      ajouterPage,
      supprimerPage,
      fileInput,
      ouvrirSelecteurFichier,
      gererUploadFichier,
      supprimerMedia,
      isUploading,
      formatFileSize,
      currentTab,
      goBack,
      FluxLogo
    };
  },
};
</script>

<template>
  <div class="h-[100dvh] bg-[#F0F0F0] flex flex-col overflow-hidden">
    
    <div class="md:hidden flex flex-col h-full">
      <div class="h-16 bg-white border-b flex items-center justify-between px-4 shrink-0">
        <button @click="goBack" class="p-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <span class="font-bold text-lg">Éditeur d'annonces</span>
        <div class="w-8"></div>
      </div>

      <div class="w-full h-64 bg-gray-200 shrink-0 relative flex items-center justify-center overflow-hidden">
        <div v-if="pageSelectionnee?.mediaURL || (pageSelectionnee?.type === 'stm' && pageSelectionnee?.linkURL)" class="w-full h-full flex items-center justify-center">
            <img v-if="pageSelectionnee.mediaType === 'image'" :src="pageSelectionnee.mediaURL" class="w-full h-full object-contain" />
            <video v-else-if="pageSelectionnee.mediaType === 'video'" :src="pageSelectionnee.mediaURL" controls class="w-full h-full object-contain"></video>
            <iframe v-else-if="pageSelectionnee.type === 'stm' || pageSelectionnee.linkURL" :src="pageSelectionnee.linkURL" class="w-full h-full border-0"></iframe>
            <div v-else-if="pageSelectionnee.mediaType === 'pdf'" class="text-gray-500">PDF Preview (Non disponible sur mobile)</div>
        </div>
        <div v-else class="text-gray-400 flex flex-col items-center">
          <svg class="w-12 h-12 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
          <span class="text-sm">Aucun média</span>
        </div>
      </div>

      <div class="flex overflow-x-auto bg-white border-b shrink-0">
        <button @click="currentTab = 'ordre'" :class="['flex-1 py-3 px-4 text-sm font-bold whitespace-nowrap', currentTab === 'ordre' ? 'text-[#E4022C] border-b-2 border-[#E4022C]' : 'text-gray-500']">Ordre</button>
        <button @click="currentTab = 'media'" :class="['flex-1 py-3 px-4 text-sm font-bold whitespace-nowrap', currentTab === 'media' ? 'text-[#E4022C] border-b-2 border-[#E4022C]' : 'text-gray-500']">Média</button>
        <button @click="currentTab = 'duree'" :class="['flex-1 py-3 px-4 text-sm font-bold whitespace-nowrap', currentTab === 'duree' ? 'text-[#E4022C] border-b-2 border-[#E4022C]' : 'text-gray-500']">Durée</button>
        <button @click="currentTab = 'style'" :class="['flex-1 py-3 px-4 text-sm font-bold whitespace-nowrap', currentTab === 'style' ? 'text-[#E4022C] border-b-2 border-[#E4022C]' : 'text-gray-500']">Style</button>
      </div>

      <div class="flex-1 overflow-y-auto bg-white p-4">
        <div v-if="currentTab === 'ordre'" class="space-y-3">
          <button @click="ajouterPage" class="w-full py-3 bg-[#E4022C] text-white rounded-lg font-bold mb-4 shadow-md">+ Ajouter une page</button>
          <draggable v-model="annonces" item-key="id" class="space-y-2" handle=".drag-handle">
            <template #item="{ element: annonce }">
              <div :class="['p-3 rounded-lg border flex items-center justify-between', pageActive === annonce.id ? 'bg-red-50 border-red-500' : 'bg-white border-gray-200']" @click="pageActive = annonce.id">
                 <div class="flex items-center gap-3">
                   <span class="drag-handle text-gray-400 p-2"><svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20"><path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"></path></svg></span>
                   <div class="w-10 h-10 bg-gray-100 rounded flex items-center justify-center">
                      <svg v-if="annonce.type === 'stm'" class="w-6 h-6 text-blue-500" fill="currentColor" viewBox="0 0 20 20"><path d="M10 2a8 8 0 100 16 8 8 0 000-8zM4.33 10a5.67 5.67 0 0111.34 0c-.39.87-.97 1.63-1.68 2.22l-1.3-2.16A3 3 0 107.31 8l-1.3 2.16A5.64 5.64 0 014.33 10z"/></svg>
                      <svg v-else-if="annonce.mediaType === 'video'" class="w-6 h-6 text-red-500" fill="currentColor" viewBox="0 0 20 20"><path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z"></path></svg>
                      <svg v-else class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                   </div>
                   <div class="flex flex-col">
                      <span class="font-semibold">{{ annonce.nom }}</span>
                      <span v-if="annonce.type === 'stm' && annonce.enabled === false" class="text-xs text-red-500 font-bold">DÉSACTIVÉE</span>
                   </div>
                 </div>
                 <!-- Hide delete button for STM page, maybe show toggle icon? For now just hide delete -->
                 <button v-if="annonce.type !== 'stm'" @click.stop="supprimerPage(annonce.id)" class="text-red-500 p-2"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg></button>
                 <button v-else @click.stop="annonce.enabled = !annonce.enabled" :title="annonce.enabled !== false ? 'Désactiver' : 'Activer'" :class="['p-2 rounded', annonce.enabled !== false ? 'text-green-500' : 'text-gray-400']">
                    <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>
                 </button>
              </div>
            </template>
          </draggable>
        </div>

        <div v-if="currentTab === 'media' && pageSelectionnee" class="space-y-6">
          
          <!-- Controls for STM Page -->
          <div v-if="pageSelectionnee.type === 'stm'" class="space-y-6">
             <div>
                <label class="block text-sm font-bold text-gray-700 mb-2">Lien URL (Page Web)</label>
                <input v-model="pageSelectionnee.linkURL" type="url" placeholder="https://example.com" class="w-full p-3 border rounded-lg bg-gray-50" />
             </div>
             
             <div class="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div class="flex items-center justify-between">
                   <span class="font-bold text-gray-700">État de la page</span>
                   <button 
                      @click="pageSelectionnee.enabled = !pageSelectionnee.enabled"
                      :class="['px-4 py-2 rounded-lg font-bold text-white transition-colors', pageSelectionnee.enabled !== false ? 'bg-green-500 hover:bg-green-600' : 'bg-gray-400 hover:bg-gray-500']"
                   >
                      {{ pageSelectionnee.enabled !== false ? 'Activée' : 'Désactivée' }}
                   </button>
                </div>
                <p class="text-xs text-gray-500 mt-2">
                   Si désactivée, cette page ne sera pas affichée.
                </p>
             </div>
          </div>

          <!-- Controls for Normal Pages -->
          <div v-else>
            <div class="bg-blue-50 p-4 rounded-lg mb-4">
               <h3 class="text-sm font-bold text-blue-900 mb-2">Média actuel</h3>
               <div v-if="pageSelectionnee.media">
                  <p class="text-sm text-blue-800">Nom: {{ pageSelectionnee.mediaName }}</p>
                  <p class="text-sm text-blue-800">Taille: {{ formatFileSize(pageSelectionnee.mediaSize) }}</p>
               </div>
               <p v-else class="text-sm text-gray-500">Aucun média sélectionné</p>
            </div>
            <button @click="ouvrirSelecteurFichier" class="w-full py-4 bg-blue-500 text-white rounded-lg font-bold shadow flex items-center justify-center gap-2">Importer un média</button>
            <button v-if="pageSelectionnee.media" @click="supprimerMedia" class="w-full mt-4 py-4 bg-white border-2 border-red-500 text-red-500 rounded-lg font-bold flex items-center justify-center gap-2">Supprimer le média</button>
          </div>
        </div>

        <div v-if="currentTab === 'duree' && pageSelectionnee" class="space-y-6">
          <div>
            <label class="block text-sm font-bold text-gray-700 mb-2">Durée (secondes)</label>
            <input v-model.number="pageSelectionnee.dureeAffichage" type="number" class="w-full p-3 border rounded-lg bg-gray-50 font-bold text-lg" />
          </div>
          <div class="space-y-4">
             <label class="block text-sm font-bold text-gray-700">Période d'affichage</label>
             <div class="flex gap-2 items-center">
               <span class="w-12 text-sm text-gray-500">Du</span>
               <input v-model="pageSelectionnee.dureeDebut" type="date" class="flex-1 p-3 border rounded-lg bg-gray-50" />
             </div>
             <div class="flex gap-2 items-center">
               <span class="w-12 text-sm text-gray-500">Au</span>
               <input v-model="pageSelectionnee.dureeFin" type="date" class="flex-1 p-3 border rounded-lg bg-gray-50" />
             </div>
          </div>
        </div>

        <div v-if="currentTab === 'style' && pageSelectionnee" class="space-y-6">
          <div>
            <label class="block text-sm font-bold text-gray-700 mb-2">Transition</label>
            <select v-model="pageSelectionnee.transition" class="w-full p-3 border rounded-lg bg-white h-12">
               <option value="fade">Fondu</option>
               <option value="slide-left">Glissement gauche</option>
               <option value="zoom">Zoom</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-bold text-gray-700 mb-2">Mode d'affichage</label>
            <select v-model="pageSelectionnee.modeAffichage" class="w-full p-3 border rounded-lg bg-white h-12">
               <option value="cover">Couvrir (Remplir)</option>
               <option value="contain">Contenir (Entier)</option>
            </select>
          </div>
          <div v-if="pageSelectionnee.mediaType === 'video'" class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
             <input type="checkbox" v-model="pageSelectionnee.loop" class="w-6 h-6 text-red-500 rounded" />
             <span class="font-bold text-gray-700">Lire en boucle</span>
          </div>
        </div>
      </div>
    </div>


    <div class="hidden md:flex flex-col h-full">
      
      <div class="flex flex-row justify-between items-center bg-white p-2 py-4 drop-shadow-xl shrink-0 z-10">
        <div class="flex flex-row items-center mr-6 p-2">
          <button @click="goBack" class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-2 rounded-lg inline-flex items-center">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div class="flex flex-row items-center gap-4">
            <img :src="FluxLogo" alt="ETSFlux logo" class="w-28 ml-6 -mb-4" />
            <h1 class="text-black font-bold text-2xl">Éditeur d'annonces</h1>
          </div>
        </div>
      </div>

      <div class="flex flex-1 overflow-hidden bg-gray-100">
        
        <div class="w-60 xl:w-80 bg-white shadow-lg p-4 flex flex-col z-0 transition-all duration-300">
          <button @click="ajouterPage" class="w-full mb-4 py-3 px-4 bg-blue-500 hover:bg-blue-600 text-white rounded-lg flex items-center justify-center transition-colors">
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
            <span class="hidden xl:inline">Ajouter une page</span>
            <span class="xl:hidden">Ajouter</span>
          </button>

          <div class="flex-1 overflow-y-auto">
            <draggable v-model="annonces" item-key="id" class="space-y-2" :animation="200" handle=".drag-handle">
              <template #item="{ element: annonce }">
                <div :class="['p-3 rounded-lg cursor-pointer transition-all', pageActive === annonce.id ? 'bg-blue-100 border-2 border-blue-500' : 'bg-gray-50 hover:bg-gray-100']" @click="pageActive = annonce.id">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center flex-1 min-w-0">
                      <svg class="w-5 h-5 text-gray-400 mr-2 drag-handle cursor-move flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"></path></svg>
                      
                      <svg v-if="annonce.type === 'stm'" class="w-5 h-5 text-blue-500 mr-2" fill="currentColor" viewBox="0 0 20 20"><path d="M10 2a8 8 0 100 16 8 8 0 000-8zM4.33 10a5.67 5.67 0 0111.34 0c-.39.87-.97 1.63-1.68 2.22l-1.3-2.16A3 3 0 107.31 8l-1.3 2.16A5.64 5.64 0 014.33 10z"/></svg>
                      <svg v-else-if="!annonce.media" class="w-5 h-5 text-gray-400 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                      <svg v-else-if="annonce.mediaType === 'image'" class="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd"></path></svg>
                      <svg v-else-if="annonce.mediaType === 'video'" class="w-5 h-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20"><path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z"></path></svg>

                      <div class="flex-1 min-w-0">
                         <div class="flex items-center gap-2">
                             <p class="font-medium text-sm truncate">{{ annonce.nom }}</p>
                             <span v-if="annonce.type === 'stm' && annonce.enabled === false" class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-gray-200 text-gray-500">OFF</span>
                         </div>
                         <p v-if="annonce.media" class="text-xs text-gray-500 truncate">{{ annonce.mediaName }}</p>
                      </div>
                    </div>
                    <button v-if="annonce.type !== 'stm'" @click.stop="supprimerPage(annonce.id)" class="text-red-500 hover:bg-red-100 p-1 rounded"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg></button>
                    <button v-else @click.stop="annonce.enabled = !annonce.enabled" :title="annonce.enabled !== false ? 'Désactiver' : 'Activer'" :class="['p-1 rounded transition-colors', annonce.enabled !== false ? 'text-green-500 hover:bg-green-100' : 'text-gray-400 hover:bg-gray-200']">
                       <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <circle cx="10" cy="10" r="8" v-if="annonce.enabled !== false"/>
                          <path v-else fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                       </svg>
                    </button>
                  </div>
                </div>
              </template>
            </draggable>
          </div>
        </div>

      <div class="flex-1 flex flex-col p-4 xl:p-8 min-h-0 overflow-hidden">
        
        <div class="flex-1 bg-white rounded-lg shadow-lg flex items-center justify-center overflow-hidden relative min-h-0">
            
            <div v-if="isUploading" class="absolute inset-0 bg-black/50 z-50 flex items-center justify-center text-white">Upload...</div>
            
             <div v-if="pageSelectionnee?.mediaURL || (pageSelectionnee?.type === 'stm' && pageSelectionnee?.linkURL)" class="w-full h-full flex items-center justify-center">
                <img v-if="pageSelectionnee.mediaType === 'image'" :src="pageSelectionnee.mediaURL" class="max-w-full max-h-full object-contain" />
                <video v-else-if="pageSelectionnee.mediaType === 'video'" :src="pageSelectionnee.mediaURL" controls class="max-w-full max-h-full"></video>
                <iframe v-else-if="pageSelectionnee.type === 'stm' || pageSelectionnee.linkURL" :src="pageSelectionnee.linkURL" class="w-full h-full border-0"></iframe>
                <iframe v-else-if="pageSelectionnee.mediaType === 'pdf'" :src="pageSelectionnee.mediaURL" class="w-full h-full"></iframe>
             </div>
            
            <div v-else class="text-center text-gray-400">
              <svg class="w-24 h-24 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
              <p>Aucun média</p>
            </div>
        </div>
                <div v-if="pageSelectionnee?.type !== 'stm'" class="mt-4 xl:mt-6 flex flex-col xl:flex-row justify-center gap-2 xl:gap-4 shrink-0">
             <button @click="ouvrirSelecteurFichier" class="px-4 py-3 xl:px-6 bg-pink-500 hover:bg-pink-600 text-white rounded-lg font-bold flex items-center justify-center gap-2">
               <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
               Importer un média
             </button>
             <button v-if="pageSelectionnee?.media" @click="supprimerMedia" class="px-4 py-3 xl:px-6 bg-red-500 hover:bg-red-600 text-white rounded-lg font-bold flex items-center justify-center gap-2">
               <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
               Supprimer
             </button>
          </div>
          <div v-else class="mt-4 xl:mt-6 text-center text-gray-500 italic">
             Cette page affiche un contenu web externe.
          </div>
      </div>

        <div class="w-64 xl:w-80 bg-white shadow-lg p-6 overflow-y-auto z-0 transition-all duration-300">
          <h2 class="text-xl font-bold mb-6">Propriétés</h2>

          <div v-if="pageSelectionnee">
             
             <div v-if="pageSelectionnee.media" class="mb-6 p-4 bg-blue-50 rounded-lg">
                <h3 class="text-sm font-semibold text-blue-900 mb-2">Média actuel</h3>
                <p class="text-sm text-blue-700">Type : {{ pageSelectionnee.mediaType }}</p>
                <p class="text-sm text-blue-700 truncate">Nom : {{ pageSelectionnee.mediaName }}</p>
                <p class="text-sm text-blue-700">Taille : {{ formatFileSize(pageSelectionnee.mediaSize) }}</p>
             </div>

             <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">Nom de la page</label>
                <input v-model="pageSelectionnee.nom" :disabled="pageSelectionnee.type === 'stm'" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-500" />
             </div>

             <!-- URL Link ONLY for STM page -->
             <div v-if="pageSelectionnee.type === 'stm'" class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">Lien URL (Page Web)</label>
                <input v-model="pageSelectionnee.linkURL" type="url" placeholder="https://example.com" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" />
             </div>
             
             <!-- Enable/Disable toggle for STM page -->
             <div v-if="pageSelectionnee.type === 'stm'" class="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div class="flex items-center justify-between">
                   <span class="font-bold text-gray-700">État de la page</span>
                   <button 
                      @click="pageSelectionnee.enabled = !pageSelectionnee.enabled"
                      :class="['px-4 py-2 rounded-lg font-bold text-white transition-colors', pageSelectionnee.enabled !== false ? 'bg-green-500 hover:bg-green-600' : 'bg-gray-400 hover:bg-gray-500']"
                   >
                      {{ pageSelectionnee.enabled !== false ? 'Activée' : 'Désactivée' }}
                   </button>
                </div>
                <p class="text-xs text-gray-500 mt-2">
                   Si désactivée, cette page ne sera pas affichée dans le cycle de lecture.
                </p>
             </div>

             <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">Période d'affichage</label>
                <div class="flex items-center space-x-2 mb-2">
                  <span class="text-sm text-gray-600 w-12">Début</span>
                  <input v-model="pageSelectionnee.dureeDebut" type="date" class="flex-1 px-3 py-2 border border-gray-300 rounded-md" />
                </div>
                <div class="flex items-center space-x-2">
                  <span class="text-sm text-gray-600 w-12">Fin</span>
                  <input v-model="pageSelectionnee.dureeFin" type="date" class="flex-1 px-3 py-2 border border-gray-300 rounded-md" />
                </div>
             </div>

             <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">Durée à l'écran (secondes)</label>
                <input v-model.number="pageSelectionnee.dureeAffichage" type="number" min="1" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" />
             </div>

             <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">Transition</label>
                <select v-model="pageSelectionnee.transition" class="w-full px-3 py-2 border border-gray-300 rounded-md">
                  <option value="fade">Fondu</option>
                  <option value="slide-left">Glissement gauche</option>
                  <option value="zoom">Zoom</option>
                </select>
             </div>

             <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">Mode d'affichage</label>
                <select v-model="pageSelectionnee.modeAffichage" class="w-full px-3 py-2 border border-gray-300 rounded-md">
                  <option value="cover">Couvrir (remplir l'écran)</option>
                  <option value="contain">Contenir (afficher tout)</option>
                </select>
             </div>

             <div v-if="pageSelectionnee.mediaType === 'video'" class="mb-6">
                <label class="flex items-center">
                  <input type="checkbox" v-model="pageSelectionnee.loop" class="mr-2" />
                  <span class="text-sm font-medium text-gray-700">Lire en boucle</span>
                </label>
             </div>

          </div>
          <div v-else class="text-gray-500 text-center mt-10">
            Sélectionnez une page pour voir ses propriétés
          </div>
        </div>
      </div>
    </div>

    <input ref="fileInput" type="file" @change="gererUploadFichier" accept="image/*,video/*,application/pdf" class="hidden" />
  </div>
</template>

<style scoped>
.drag-handle { cursor: grab; }
.drag-handle:active { cursor: grabbing; }
</style>