import { defineConfig } from "vite";

export default defineConfig({
  base: "./",
  build: {
    target: "chrome109",
    outDir: "www",
    emptyOutDir: true,
  },
});
