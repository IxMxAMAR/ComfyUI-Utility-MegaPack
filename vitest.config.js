import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    include: ["web/__tests__/**/*.test.js"],
    coverage: {
      include: ["web/**/*.js"],
      exclude: ["web/__tests__/**", "web/themes/**"],
      reporter: ["text", "json"],
    },
  },
});
