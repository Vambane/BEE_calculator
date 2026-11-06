import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [svelte()],
  worker: { format: "es" },
  build: { target: "es2022", sourcemap: false },
});
