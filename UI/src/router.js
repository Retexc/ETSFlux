import { createRouter, createWebHistory } from "vue-router";
import Ecran from "./views/Ecran.vue";
import STMDisplay from "./views/STMDisplay.vue";

/**
 * /     : l'écran du salon (annonces de Flux + bloc STM, dans l'ordre choisi dans Flux)
 * /stm  : prochains passages STM seulement, en plein écran
 * /apercu : le même écran, dans le cadre « Aperçu » d'AMÉUX Flux (liste envoyée par Flux)
 * Anciennes adresses (/display, /login, /editor…) : renvoyées vers l'écran.
 */
const routes = [
  { path: "/", name: "Ecran", component: Ecran },
  { path: "/stm", name: "STM", component: STMDisplay },
  { path: "/apercu", name: "Apercu", component: Ecran, props: { apercu: true } },
  { path: "/:pathMatch(.*)*", redirect: "/" },
];

export default createRouter({ history: createWebHistory(), routes });
