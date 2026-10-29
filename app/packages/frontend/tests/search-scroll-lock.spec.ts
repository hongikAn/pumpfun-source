import { expect, test } from "@playwright/test";
import { writeFile } from "node:fs/promises";
import { openShellSearch } from "./shell-controls";

for (const [label, width, close] of [
  ["desktop Escape", 1440, "escape"],
  ["mobile Escape", 375, "escape"],
  ["desktop shortcut toggle", 1440, "shortcut"],
] as const) {
  test(`search keeps the background still and releases it after ${label}`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width, height: 812 });
    const requests: string[] = [];
    page.on("request", (request) => requests.push(`${request.method()} ${request.url()}`));
    await page.goto("/docs/fees");
    const input = await openShellSearch(page);
    await input.fill("alice");
    const dialog = page.getByRole("dialog", { name: "Search for coins and users", exact: true });
    await expect(dialog.getByRole("link", { name: "alice_pump", exact: true })).toBeVisible();
    const before = await page.evaluate(() => window.scrollY);
    // Wheel on the real modal backdrop, outside its search-results scroller.
    await page.mouse.move(width - 12, 650);
    await page.mouse.wheel(0, 500);
    await page.waitForTimeout(250);
    const open = await page.evaluate(() => ({ scrollY: window.scrollY, overflow: document.body.style.overflow }));
    await page.screenshot({ path: testInfo.outputPath("search-open.png") });
    await writeFile(testInfo.outputPath("scroll.json"), JSON.stringify({ before, open }, null, 2));
    await writeFile(testInfo.outputPath("browser-requests.json"), JSON.stringify(requests, null, 2));
    expect(open.scrollY).toBe(before);
    if (close === "escape") await page.keyboard.press("Escape");
    else await page.keyboard.press("Control+k");
    await expect(dialog).not.toBeVisible();
    await page.mouse.move(width - 12, 650);
    await page.mouse.wheel(0, 500);
    await expect.poll(() => page.evaluate(() => window.scrollY)).toBeGreaterThan(before);
    const closed = await page.evaluate(() => ({ scrollY: window.scrollY, overflow: document.body.style.overflow }));
    await writeFile(testInfo.outputPath("scroll.json"), JSON.stringify({ before, open, closed }, null, 2));
    await page.screenshot({ path: testInfo.outputPath("search-closed.png") });
    expect(requests.filter((r) => !r.startsWith("GET http://127.0.0.1:3010/") && !r.startsWith("HEAD http://127.0.0.1:3010/"))).toEqual([]);
  });
}


test("search submission releases the modal scroll lock", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 1440, height: 812 });
  await page.goto("/docs/fees");
  const initialOverflow = await page.evaluate(() => document.body.style.overflow);
  const input = await openShellSearch(page);
  await input.fill("alice");
  await expect.poll(() => page.evaluate(() => document.body.style.overflow)).toBe("hidden");
  await input.press("Enter");
  await expect(page).toHaveURL(/\/explore\?q=alice$/, { timeout: 15_000 });
  await expect(page.getByRole("dialog", { name: "Search for coins and users", exact: true })).not.toBeVisible();
  await expect.poll(() => page.evaluate(() => document.body.style.overflow)).toBe(initialOverflow);
  await page.screenshot({ path: testInfo.outputPath("submitted.png") });
});

test("closing Search preserves the underlying Settings scroll lock", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 1440, height: 812 });
  await page.goto("/docs/fees?settings=privacy");
  const settings = page.getByRole("dialog", { name: "Settings", exact: true });
  await expect(settings).toBeVisible();
  await expect.poll(() => page.evaluate(() => document.body.style.overflow)).toBe("hidden");
  await page.keyboard.press("Control+k");
  const search = page.getByRole("dialog", { name: "Search for coins and users", exact: true });
  await expect(search).toBeVisible();
  await search.getByRole("searchbox").fill("alice");
  await expect(search.getByRole("link", { name: "alice_pump", exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(search).not.toBeVisible();
  await expect(settings).toBeVisible();
  await expect.poll(() => page.evaluate(() => document.body.style.overflow)).toBe("hidden");
  await page.mouse.move(1428, 780);
  await page.mouse.wheel(0, 500);
  await page.waitForTimeout(250);
  expect(await page.evaluate(() => window.scrollY)).toBe(0);
  await page.screenshot({ path: testInfo.outputPath("settings-still-locked.png") });
  await settings.getByRole("button", { name: "Close settings", exact: true }).click();
  await expect(settings).not.toBeVisible();
  await expect.poll(() => page.evaluate(() => document.body.style.overflow)).toBe("");
  await page.mouse.move(1428, 780);
  await page.mouse.wheel(0, 500);
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBeGreaterThan(0);
});
