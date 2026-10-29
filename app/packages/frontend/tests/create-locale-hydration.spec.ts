import { expect, test } from "@playwright/test";
import { writeFile } from "node:fs/promises";

for (const locale of ["de-DE", "en-US"]) {
  test.describe(locale, () => {
    test.use({ locale });
    test("Create counter hydrates consistently and keeps draft editing usable", async ({ page }, testInfo) => {
      const errors: string[] = [];
      const requests: string[] = [];
      page.on("pageerror", (error) => errors.push(error.message));
      page.on("request", (request) => requests.push(`${request.method()} ${request.url()}`));
      const response = await page.goto("/create");
      const html = await response!.text();
      const responseCounter = html.match(/id="description-hint"[^>]*>([\s\S]*?)<\/div>/)?.[1];
      await page.getByRole("textbox", { name: "Coin name" }).fill("Local draft");
      await expect(page.getByRole("heading", { name: "Local draft", exact: true })).toBeVisible();
      const hint = page.locator("#description-hint");
      await hint.scrollIntoViewIfNeeded();
      await page.screenshot({ path: testInfo.outputPath("create-counter.png") });
      const observation = { locale, browser: await page.evaluate(() => Intl.NumberFormat().resolvedOptions().locale), serverCounterHtml: responseCounter, clientCounter: await hint.textContent(), errors, requests };
      await writeFile(testInfo.outputPath("observations.json"), JSON.stringify(observation, null, 2));
      expect(responseCounter).toContain("2,000");
      expect(observation.browser).toBe(locale);
      expect(errors).toEqual([]);
      await expect(hint).toContainText("2,000");
      await page.getByRole("textbox", { name: "Description" }).fill("Edited locally");
      await expect(hint).toContainText("14/2,000");
      await expect(page.getByRole("textbox", { name: "Coin name" })).toHaveValue("Local draft");
      await page.getByRole("button", { name: "Reset draft", exact: true }).click();
      await expect(hint).toContainText("0/2,000");
      expect(requests.filter((r) => !r.startsWith("GET http://127.0.0.1:3010/") && !r.startsWith("HEAD http://127.0.0.1:3010/"))).toEqual([]);
    });
  });
}
