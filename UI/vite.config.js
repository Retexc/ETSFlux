import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";

// Écran du salon (Vue). Les adresses de Flask et de Flux viennent de .env (voir .env.example).
export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: { host: true },
});
