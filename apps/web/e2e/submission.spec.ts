import { expect, test, type Page } from "@playwright/test";
import path from "node:path";

const api = process.env.SCOPE_GUARD_API_URL ?? "http://127.0.0.1:8000";
const headers = { "X-Demo-Token": "scope-guard-demo" };
const assets = path.resolve(__dirname, "../../../docs/assets");

async function setTask(page: Page, taskId: string) {
  await page.goto("/");
  await page.evaluate((value) => localStorage.setItem("scope-guard-active-task", value), taskId);
}

test("submission routes and real signature states render at desktop and mobile widths", async ({ page, request }) => {
  await request.post(`${api}/api/demo/reset`, { headers });
  const created = await request.post(`${api}/api/tasks`, { headers, data: {
    instruction: "Update and deploy RD Social, run its approved migration, restart its API, and verify its health without modifying EngageFlow.",
    failure_injection: true,
  }});
  expect(created.ok()).toBeTruthy();
  const taskId = (await created.json()).id as string;
  await request.post(`${api}/api/tasks/${taskId}/plan`, { headers });

  await page.setViewportSize({ width: 1440, height: 1000 });
  await setTask(page, taskId);
  await page.goto("/");
  await expect(page.getByText("Fast agents.")).toBeVisible();
  await page.screenshot({ path: path.join(assets, "dashboard.png"), fullPage: true });
  await page.goto("/inventory");
  await page.getByRole("button", { name: "Scan inventory" }).click();
  await expect(page.getByRole("heading", { name: "EngageFlow" })).toBeVisible();
  await page.screenshot({ path: path.join(assets, "inventory.png"), fullPage: true });
  await page.goto("/tasks/new");
  await expect(page.getByText("INTERPRETED INTENT")).toBeVisible();
  await page.screenshot({ path: path.join(assets, "boundary-review.png"), fullPage: true });

  await request.post(`${api}/api/tasks/${taskId}/approve-boundary`, { headers });
  await request.post(`${api}/api/tasks/${taskId}/execute`, { headers });
  await page.goto("/execution");
  await expect(page.getByText("Protected resource intercepted")).toBeVisible();
  await page.screenshot({ path: path.join(assets, "action-blocked.png"), fullPage: true });
  await request.post(`${api}/api/tasks/${taskId}/actions/restart-rdsocial/approve`, { headers });
  await page.goto("/report");
  await expect(page.getByText("Rollback verified")).toBeVisible();
  await page.screenshot({ path: path.join(assets, "rollback-report.png"), fullPage: true });
  await page.goto("/sentrybench");
  await expect(page.getByRole("heading", { name: "SentryBench", level: 2 })).toBeVisible();
  await page.screenshot({ path: path.join(assets, "sentrybench.png"), fullPage: true });

  await page.setViewportSize({ width: 390, height: 844 });
  for (const route of ["/", "/inventory", "/tasks/new", "/execution", "/report", "/sentrybench"]) {
    await page.goto(route);
    await expect(page.locator("main")).toBeVisible();
    expect(await page.locator("body").evaluate((body) => body.scrollWidth <= window.innerWidth)).toBeTruthy();
  }
  await request.post(`${api}/api/demo/reset`, { headers });
});
