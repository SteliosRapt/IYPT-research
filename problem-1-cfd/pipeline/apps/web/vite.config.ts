import { fileURLToPath, URL } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
      "@fixed-geometry/shared-schema": fileURLToPath(
        new URL("../../packages/shared-schema/src/index.ts", import.meta.url)
      )
    }
  },
  publicDir: fileURLToPath(new URL("../../examples", import.meta.url)),
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts"
  }
});

