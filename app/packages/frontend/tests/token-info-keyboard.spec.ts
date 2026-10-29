import { expect, test } from "@playwright/test";
import { writeFile } from "node:fs/promises";

test("Control End and Home retain native document scrolling from the info bar", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 1440, height: 812 });
  const requests: string[] = [];
  page.on("request", (request) => requests.push(`${request.method()} ${request.url()}`));
  await page.goto("/docs/fees");
  const group = page.getByRole("radiogroup", { name: "Info bar content" });
  const positions = group.getByRole("radio", { name: "Positions", exact: true });
  await positions.click();
  await expect(positions).toHaveAttribute("aria-checked", "true");
  // Establish the real browser/platform default on a control with no key handler.
  await page.getByRole("button", { name: "Sign in", exact: true }).focus();
  await page.keyboard.press("Control+End");
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBeGreaterThan(0);
  const nativeEnd = await page.evaluate(() => window.scrollY);
  await page.keyboard.press("Control+Home");
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0);
  await positions.focus();
  await page.keyboard.press("Control+End");
  await page.waitForTimeout(250);
  const infoEnd = await page.evaluate(() => window.scrollY);
  const selectedAfterEnd = await group.locator('[aria-checked="true"]').getAttribute("aria-label");
  await page.screenshot({ path: testInfo.outputPath("after-control-end.png") });
  await writeFile(testInfo.outputPath("observations.json"), JSON.stringify({ nativeEnd, infoEnd, selectedAfterEnd }, null, 2));
  await writeFile(testInfo.outputPath("browser-requests.json"), JSON.stringify(requests, null, 2));
  expect(infoEnd).toBeGreaterThan(0);
  await expect(positions).toHaveAttribute("aria-checked", "true");
  await page.keyboard.press("Control+Home");
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0);
  await expect(positions).toHaveAttribute("aria-checked", "true");
  await expect(positions).toBeFocused();
  await page.screenshot({ path: testInfo.outputPath("after-control-home.png") });
  expect(requests.filter((r) => !r.startsWith("GET http://127.0.0.1:3010/") && !r.startsWith("HEAD http://127.0.0.1:3010/"))).toEqual([]);
});

test("plain info-bar Home End and arrows retain roving radio navigation", async ({ page }) => {
  await page.goto("/docs/fees");
  const group = page.getByRole("radiogroup", { name: "Info bar content" });
  await group.getByRole("radio", { name: "Positions", exact: true }).click();
  for (const key of ["Control+ArrowRight", "Alt+ArrowDown", "Meta+ArrowRight"]) {
    await page.keyboard.press(key);
    await expect(group.getByRole("radio", { name: "Positions", exact: true })).toHaveAttribute("aria-checked", "true");
  }
  for (const [key, label] of [["End", "Recently viewed"], ["Home", "Watchlist"], ["ArrowRight", "Positions"], ["ArrowDown", "Following"], ["ArrowLeft", "Positions"], ["ArrowUp", "Watchlist"], ["ArrowLeft", "Recently viewed"], ["ArrowRight", "Watchlist"]]) {
    await page.keyboard.press(key);
    const radio = group.getByRole("radio", { name: label, exact: true });
    await expect(radio).toHaveAttribute("aria-checked", "true");
    await expect(radio).toHaveAttribute("tabindex", "0");
    await expect(radio).toBeFocused();
    await expect(group.locator('[tabindex="0"]')).toHaveCount(1);
  }
});
