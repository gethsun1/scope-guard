import { defineConfig } from "@playwright/test";

const apiURL = process.env.SCOPE_GUARD_API_URL ?? "http://127.0.0.1:8000";
const baseURL = process.env.SCOPE_GUARD_WEB_URL ?? "http://127.0.0.1:3000";

export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  workers: 1,
  fullyParallel: false,
  use: { baseURL, trace: "retain-on-failure" },
  webServer: process.env.SCOPE_GUARD_EXTERNAL_WEB ? undefined : {
    command: "corepack pnpm dev --hostname 127.0.0.1",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: false,
    timeout: 120_000,
    env: { NEXT_PUBLIC_API_URL: apiURL, NEXT_TELEMETRY_DISABLED: "1" },
  },
});
