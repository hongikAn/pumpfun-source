import { expect, test } from "@playwright/test";
import { writeFile } from "node:fs/promises";

for (const width of [320, 375, 767]) {
  test(`mobile drawer Create menu stays visible at ${width}px`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width, height: 812 });
    const requests: string[] = [];
    page.on("request", (request) => requests.push(`${request.method()} ${request.url()}`));
    await page.goto("/");
    await page.getByRole("button", { name: "Open navigation", exact: true }).click();
    const trigger = page.getByTestId("create-button-sidebar");
    await trigger.click();
    const menu = page.getByRole("menu", { name: "Create", exact: true });
    await expect(menu).toBeVisible();
    const box = await menu.boundingBox();
    const triggerBox = await trigger.boundingBox();
    await page.screenshot({ path: testInfo.outputPath("menu.png") });
    await writeFile(testInfo.outputPath("geometry.json"), JSON.stringify({ width, height: 812, menu: box, trigger: triggerBox }, null, 2));
    expect(box).not.toBeNull();
    expect(box!.x).toBeGreaterThanOrEqual(0);
    expect(box!.x + box!.width).toBeLessThanOrEqual(width);
    expect(box!.y).toBeGreaterThanOrEqual(0);
    expect(box!.y + box!.height).toBeLessThanOrEqual(812);
    await page.getByRole("menuitem", { name: "Create coin", exact: true }).click();
    await expect(page).toHaveURL(/\/create$/, { timeout: 15_000 });
    await expect(page.getByRole("heading", { level: 1, name: "Create a coin" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Open navigation", exact: true })).toHaveAttribute("aria-expanded", "false");
    await page.screenshot({ path: testInfo.outputPath("destination.png") });
    await writeFile(testInfo.outputPath("browser-requests.json"), JSON.stringify(requests, null, 2));
    expect(requests.filter((request) => !request.startsWith("GET http://127.0.0.1:3010/") && !request.startsWith("HEAD http://127.0.0.1:3010/"))).toEqual([]);
  });
}

test("desktop Create menu retains right-side placement in both sidebar states", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");
  for (const expanded of [false, true]) {
    if (expanded) await page.locator("#app-sidebar-trigger").click();
    const trigger = page.getByTestId("create-button-sidebar");
    await trigger.click();
    const menu = page.getByRole("menu", { name: "Create", exact: true });
    await expect(menu).toBeVisible();
    const box = await menu.boundingBox();
    const triggerBox = await trigger.boundingBox();
    expect(box!.x).toBeCloseTo(triggerBox!.x + triggerBox!.width + 4, 0);
    expect(box!.x + box!.width).toBeLessThanOrEqual(1440);
    await page.screenshot({ path: testInfo.outputPath(expanded ? "expanded.png" : "collapsed.png") });
    await page.keyboard.press("Escape");
    await expect(menu).toHaveCount(0);
    await expect(trigger).toBeFocused();
  }
});
