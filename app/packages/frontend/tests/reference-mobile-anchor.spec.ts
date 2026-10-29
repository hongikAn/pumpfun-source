import { expect, test } from "@playwright/test";
import { writeFile } from "node:fs/promises";

for (const [label, width, mode] of [
  ["mobile contents", 375, "contents"],
  ["mobile direct fragment", 320, "fragment"],
  ["desktop contents", 1440, "contents"],
  ["desktop direct fragment", 1440, "fragment"],
] as const) {
  test(`${label} keeps the selected reference heading below the sticky header`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width, height: 812 });
    const requests: string[] = [];
    page.on("request", (request) => requests.push(`${request.method()} ${request.url()}`));
    await page.goto(mode === "fragment" ? "/docs/fees#platform-fee" : "/docs/fees");
    await expect(page.getByTestId("reference-document")).toBeVisible();
    await page.evaluate(() => document.fonts.ready);
    if (mode === "contents") {
      const contentsLink = page.getByRole("navigation", { name: "On this page" }).getByRole("link", { name: "Platform Fee", exact: true });
      await contentsLink.focus();
      await page.keyboard.press("Enter");
    }
    await expect(page).toHaveURL(/\/docs\/fees#platform-fee$/);
    const heading = page.locator("#platform-fee .reference-heading-link");
    await expect(heading).toBeInViewport();
    const headingBox = await heading.boundingBox();
    const headerBox = await page.getByRole("banner").boundingBox();
    const computed = await page.locator("#platform-fee").evaluate((element) => ({
      headingScrollMargin: getComputedStyle(element).scrollMarginTop,
      documentScrollPadding: getComputedStyle(document.documentElement).scrollPaddingTop,
      shellHeader: getComputedStyle(document.documentElement).getPropertyValue("--shell-header").trim(),
    }));
    await page.screenshot({ path: testInfo.outputPath("anchor.png") });
    await writeFile(testInfo.outputPath("geometry.json"), JSON.stringify({ width, mode, heading: headingBox, header: headerBox, computed }, null, 2));
    await writeFile(testInfo.outputPath("browser-requests.json"), JSON.stringify(requests, null, 2));
    expect(headingBox!.y).toBeGreaterThanOrEqual(headerBox!.y + headerBox!.height);
    await expect(heading).toContainText("Platform Fee");
    expect(requests.filter((request) => !request.startsWith("GET http://127.0.0.1:3010/") && !request.startsWith("HEAD http://127.0.0.1:3010/"))).toEqual([]);
  });
}
