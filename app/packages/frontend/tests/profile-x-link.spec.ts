import { expect, test } from "@playwright/test";

test("recorded X identity is an accessible external link with keyboard activation", async ({
  page,
  context,
}) => {
  const intercepted: string[] = [];
  await context.route("https://x.com/**", async (route) => {
    intercepted.push(route.request().url());
    await route.fulfill({
      status: 200,
      contentType: "text/html",
      body: "<title>Intercepted local test</title>",
    });
  });
  await page.goto("/profile/user-001");
  const link = page.getByRole("link", {
    name: "@alice_on_x on X",
    exact: true,
  });
  await expect(link).toBeVisible();
  await expect(link).toHaveAttribute("href", "https://x.com/alice_on_x");
  await expect(link).toHaveAttribute("target", "_blank");
  await expect(link).toHaveAttribute("rel", "noreferrer");
  await link.focus();
  await expect(link).toBeFocused();
  const popupPromise = page.waitForEvent("popup");
  await page.keyboard.press("Enter");
  const popup = await popupPromise;
  await expect(popup).toHaveURL("https://x.com/alice_on_x");
  await expect(popup).toHaveTitle("Intercepted local test");
  await expect(page).toHaveURL(/\/profile\/user-001$/);
  expect(intercepted).toEqual(["https://x.com/alice_on_x"]);
  await popup.close();
});

test("profiles without a recorded X identity do not invent a link", async ({
  page,
}) => {
  await page.goto("/profile/user-002");
  await expect(page.getByTestId("profile-header")).toBeVisible();
  await expect(page.getByTestId("user-x-badge")).toHaveCount(0);
});
