import { expect, test, type Page, type Route } from "@playwright/test";

const source = {
  mode: "developer-api",
  label: "Pump developer API",
  fetchedAt: "2026-10-28T12:00:00.000Z",
} as const;

const traderEntries = Array.from({ length: 22 }, (_, index) => ({
  rank: index + 1,
  walletAddress: `synthetic-wallet-${String(index + 1).padStart(2, "0")}`,
  username: `synthetic-trader-${String(index + 1).padStart(2, "0")}`,
  userId: `synthetic-user-${index + 1}`,
  xUsername: null,
  isVerified: index === 0,
  verifiedBadgeVisible: true,
  pnlUsd: 1_000 - index * 10,
  pnlPercent: 25 - index,
  realizedPnlUsd: 700 - index * 5,
  unrealizedPnlUsd: 300 - index * 5,
  buySpendSol: 10,
  positionsCount: 2,
  lastRefreshedAtMs: 1_700_000_000_000,
}));

const creatorEntries = Array.from({ length: 3 }, (_, index) => ({
  rank: index + 1,
  userId: `synthetic-creator-${index + 1}`,
  username: `synthetic-creator-${index + 1}`,
  walletAddress: `synthetic-creator-wallet-${index + 1}`,
  wallets: [`synthetic-creator-wallet-${index + 1}`],
  isVerified: false,
  verifiedBadgeVisible: true,
  totalPaidUsdc: 500 - index * 50,
  payoutCount: 10 - index,
  lastPaidAt: "2026-10-28T10:00:00.000Z",
}));

const competition = {
  id: "synthetic-competition-id",
  slug: "synthetic-competition",
  kind: "person",
  title: "Synthetic browser-test competition",
  description: "Explicitly synthetic browser interaction fixture.",
  prizeCopy: "$0 test fixture",
  prizes: [{ rankFrom: 1, rankTo: 1, amount: "$0 test fixture" }],
  minMembers: 1,
  maxMembers: 1,
  registrationOpensAt: "2026-10-20T00:00:00.000Z",
  registrationClosesAt: "2026-10-30T00:00:00.000Z",
  startsAt: "2026-10-21T00:00:00.000Z",
  endsAt: "2026-10-30T00:00:00.000Z",
  maxEntries: 50,
  entriesCount: 3,
  participants: 3,
  joinable: true,
  phase: "live",
  isFinal: false,
};

function traderResponse(entries = traderEntries) {
  return {
    ok: true,
    source,
    data: {
      kind: "traders",
      entries,
      periodLabel: "Synthetic daily test window",
      windowStartSec: 1_700_000_000,
    },
  };
}

function creatorResponse() {
  return {
    ok: true,
    source,
    data: {
      kind: "creators",
      entries: creatorEntries,
      totalEarners: 43,
      generatedAt: "2026-10-28T11:59:00.000Z",
      page: 1,
      pageSize: 20,
    },
  };
}

/** Explicit synthetic cap fixture; no production request is sent. */
async function mockCappedCreators(page: Page) {
  const blocked: string[] = [];
  await page.route("**/*", async (route) => {
    const request = route.request();
    if (
      new URL(request.url()).origin !== "http://127.0.0.1:3010" ||
      !["GET", "HEAD"].includes(request.method())
    ) {
      blocked.push(`${request.method()} ${request.url()}`);
      await route.abort();
      return;
    }
    await route.continue();
  });
  await page.route("**/api/leaderboard?**", async (route) => {
    if (
      new URL(route.request().url()).origin !== "http://127.0.0.1:3010" ||
      !["GET", "HEAD"].includes(route.request().method())
    ) {
      blocked.push(`${route.request().method()} ${route.request().url()}`);
      await route.abort();
      return;
    }
    const url = new URL(route.request().url());
    const currentPage = Number(url.searchParams.get("page") ?? "1");
    const firstRank = (currentPage - 1) * 20 + 1;
    const entries = Array.from(
      { length: Math.max(0, Math.min(20, 501 - firstRank)) },
      (_, i) => ({
        ...creatorEntries[0],
        rank: firstRank + i,
        username: `synthetic-capped-creator-${firstRank + i}`,
        userId: `synthetic-capped-id-${firstRank + i}`,
      }),
    );
    await fulfillJson(route, {
      ...creatorResponse(),
      data: {
        ...creatorResponse().data,
        totalEarners: 503,
        entries,
        page: currentPage,
      },
    });
  });
  return blocked;
}

for (const width of [390, 1280]) {
  test(`creator cap keeps whole-board count and disables the unavailable 26th page at ${width}px`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 900 });
    const blocked = await mockCappedCreators(page);
    await page.goto("/leaderboard?category=creators&page=25");
    await expect(
      page.getByText("503 confirmed earners", { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByText("Top 500 available", { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByText("Page 25 of 25", { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Next", exact: true }),
    ).toBeDisabled();
    await expect(
      page.getByText("@synthetic-capped-creator-500", { exact: true }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Previous", exact: true }).click();
    await expect(page).toHaveURL(/page=24/);
    await expect(
      page.getByText("Page 24 of 25", { exact: true }),
    ).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
    expect(blocked).toEqual([]);
  });
}

test("creator empty local filter retains usable page navigation", async ({
  page,
}) => {
  const blocked = await mockCappedCreators(page);
  await page.goto(
    "/leaderboard?category=creators&page=2&q=unmatched-synthetic-filter",
  );
  await expect(page.getByTestId("leaderboard-empty")).toContainText(
    "No creator on this loaded page",
  );
  await expect(page.getByText("Page 2 of 25", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Previous", exact: true }).click();
  await expect(page.getByText("Page 1 of 25", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Previous", exact: true }),
  ).toBeDisabled();
  expect(blocked).toEqual([]);
});

test("an out-of-range creator bookmark offers recovery without relabeling the empty page", async ({
  page,
}) => {
  const blocked = await mockCappedCreators(page);
  await page.goto("/leaderboard?category=creators&page=26&period=1d");
  await expect(page.getByTestId("leaderboard-empty")).toContainText(
    "Page 26 is outside the available payout board",
  );
  await expect(
    page.getByRole("navigation", { name: "Leaderboard pages" }),
  ).toHaveCount(0);
  await page
    .getByRole("button", { name: "Back to first payout page", exact: true })
    .click();
  await expect(page.getByText("Page 1 of 25", { exact: true })).toBeVisible();
  await expect(page).toHaveURL(/period=1d/);
  await page.reload();
  await expect(page.getByText("Page 1 of 25", { exact: true })).toBeVisible();
  expect(blocked).toEqual([]);
});

function competitionListResponse() {
  return {
    ok: true,
    source,
    data: {
      kind: "competitions",
      live: [competition],
      upcoming: [
        {
          ...competition,
          id: "synthetic-upcoming-id",
          slug: "synthetic-upcoming",
          title: "Synthetic upcoming competition",
          phase: "upcoming",
          joinable: false,
        },
      ],
      past: [
        {
          ...competition,
          id: "synthetic-past-id",
          slug: "synthetic-past",
          title: "Synthetic past competition",
          phase: "ended",
          isFinal: true,
          joinable: false,
        },
      ],
    },
  };
}

function competitionDetailResponse() {
  return {
    ok: true,
    source,
    data: {
      kind: "competition-detail",
      competition,
      entries: [
        {
          entryId: "synthetic-entry-id",
          participantId: "synthetic-participant-id",
          kind: "person",
          rank: 1,
          pnlUsd: 30,
          realizedPnlUsd: 20,
          unrealizedPnlUsd: 10,
          memberCount: 1,
          membersFresh: 1,
          struck: false,
          lastRefreshedAtMs: 1_700_000_000_000,
          walletAddress: "synthetic-entry-wallet",
          username: "synthetic-entrant",
          isVerified: false,
          verifiedBadgeVisible: true,
        },
      ],
      totalRanked: 1,
      builtAtMs: 1_700_000_000_000,
      isFinal: false,
    },
  };
}

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function mockLeaderboard(page: Page) {
  await page.route("**/api/leaderboard?**", async (route) => {
    const url = new URL(route.request().url());
    const category = url.searchParams.get("category");
    if (category === "creators") {
      await fulfillJson(route, creatorResponse());
      return;
    }
    if (category === "competitions") {
      await fulfillJson(
        route,
        url.searchParams.has("id")
          ? competitionDetailResponse()
          : competitionListResponse(),
      );
      return;
    }
    await fulfillJson(route, traderResponse());
  });
}

test("default mode states the credential boundary without rendering rankings", async ({
  page,
}) => {
  await page.goto("/leaderboard");

  await expect(
    page.getByRole("heading", { name: "Leaderboard" }),
  ).toBeVisible();
  await expect(page.getByTestId("leaderboard-error")).toContainText(
    "Developer API credential not configured",
  );
  await expect(page.getByRole("list", { name: "Trader rankings" })).toHaveCount(
    0,
  );
  await expect(
    page.getByText("No cached, sample or inferred ranking rows"),
  ).toBeVisible();

  const response = await page.request.get("/api/leaderboard?category=traders");
  expect(response.status()).toBe(503);
  expect(await response.json()).toMatchObject({
    ok: false,
    error: { code: "DATA_SOURCE_UNAVAILABLE" },
    source: { mode: "offline" },
  });
});

test("category navigation survives Back and Forward", async ({ page }) => {
  await mockLeaderboard(page);
  await page.goto("/leaderboard");
  await expect(
    page.getByRole("list", { name: "Trader rankings" }),
  ).toBeVisible();

  await page.getByRole("link", { name: "Creator payouts" }).click();
  await expect(page).toHaveURL(/category=creators/);
  await expect(
    page.getByRole("list", { name: "Creator payout rankings" }),
  ).toBeVisible();

  await page.goBack();
  await expect(
    page.getByRole("list", { name: "Trader rankings" }),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: "Trader PnL" })).toHaveAttribute(
    "aria-current",
    "page",
  );

  await page.goForward();
  await expect(
    page.getByRole("list", { name: "Creator payout rankings" }),
  ).toBeVisible();
});

test("trader period, sorting, local search and pagination update real URL state", async ({
  page,
}) => {
  const requests: string[] = [];
  await page.route("**/api/leaderboard?**", async (route) => {
    requests.push(route.request().url());
    await fulfillJson(route, traderResponse());
  });
  await page.goto("/leaderboard");

  await page.getByLabel("Trader period").selectOption("weekly");
  await page.getByLabel("Trader sort").selectOption("realized");
  await expect.poll(() => requests.at(-1) ?? "").toContain("period=weekly");
  await expect.poll(() => requests.at(-1) ?? "").toContain("sort=realized");
  await expect(page).toHaveURL(/period=weekly/);
  await expect(page).toHaveURL(/sort=realized/);

  await page.getByLabel("Filter loaded results").fill("synthetic-trader-15");
  await page.getByRole("button", { name: "Filter" }).click();
  await expect(page.getByRole("listitem")).toContainText([
    "synthetic-trader-15",
  ]);
  await expect(
    page.getByRole("list", { name: "Trader rankings" }),
  ).not.toContainText("synthetic-trader-01");

  await page.getByLabel("Filter loaded results").fill("");
  await page.getByRole("button", { name: "Filter" }).click();
  await expect(page).not.toHaveURL(/q=/);
  await expect(page.getByText("synthetic-trader-01")).toBeVisible();
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page).toHaveURL(/page=2/);
  await expect(page.getByText("synthetic-trader-11")).toBeVisible();
  await expect(page.getByText("Page 2 of 3")).toBeVisible();
});

test("competition status and ranked entry detail are keyboard-operable", async ({
  page,
}) => {
  await mockLeaderboard(page);
  await page.goto("/leaderboard?category=competitions");

  await page.getByLabel("Competition status").selectOption("past");
  await expect(page.getByText("Synthetic past competition")).toBeVisible();
  await page.getByLabel("Competition status").selectOption("live");
  await expect(page).toHaveURL(/status=live/);
  await expect(
    page.getByText("Synthetic browser-test competition"),
  ).toBeVisible();

  const detailLink = page.getByRole("link", { name: "View ranked entries" });
  await detailLink.focus();
  await expect(detailLink).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/competition=synthetic-competition/);
  await expect(
    page.getByRole("list", { name: "Competition rankings" }),
  ).toContainText("synthetic-entrant");

  await page.getByRole("button", { name: /Back to competitions/ }).click();
  await expect(page.getByLabel("Competition status")).toBeVisible();
});

test("loading, empty and invalid data states are explicit", async ({
  page,
}) => {
  await page.route("**/api/leaderboard?**", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 200));
    await fulfillJson(route, traderResponse([]));
  });
  await page.goto("/leaderboard");
  await expect(page.getByTestId("leaderboard-loading")).toBeVisible();
  await expect(page.getByTestId("leaderboard-empty")).toBeVisible();

  await page.unroute("**/api/leaderboard?**");
  await page.route("**/api/leaderboard?**", (route) =>
    fulfillJson(route, {
      ok: true,
      source,
      data: { kind: "traders", entries: [{ fabricated: true }] },
    }),
  );
  await page.reload();
  await expect(page.getByTestId("leaderboard-invalid")).toBeVisible();
  await expect(page.getByRole("list", { name: "Trader rankings" })).toHaveCount(
    0,
  );
});

test("network failure exposes retry and retry recovers", async ({ page }) => {
  let attempts = 0;
  let allowSuccess = false;
  await page.route("**/api/leaderboard?**", async (route) => {
    attempts += 1;
    if (!allowSuccess) {
      await fulfillJson(
        route,
        {
          ok: false,
          error: {
            code: "NETWORK_FAILURE",
            message: "The local leaderboard adapter could not be reached.",
            retryable: true,
          },
          source: { mode: "offline", label: "Local adapter unavailable" },
        },
        502,
      );
      return;
    }
    await fulfillJson(route, traderResponse(traderEntries.slice(0, 1)));
  });
  await page.goto("/leaderboard");
  await expect(page.getByTestId("leaderboard-error")).toContainText(
    "local leaderboard adapter",
  );
  allowSuccess = true;
  await page.getByRole("button", { name: "Retry" }).click();
  await expect(
    page.getByRole("list", { name: "Trader rankings" }),
  ).toBeVisible();
  expect(attempts).toBeGreaterThanOrEqual(2);
});

test("controls have accessible names and keyboard focus indicators", async ({
  page,
}) => {
  await mockLeaderboard(page);
  await page.goto("/leaderboard");

  await expect(
    page.getByRole("navigation", { name: "Leaderboard categories" }),
  ).toBeVisible();
  await expect(page.getByLabel("Trader period")).toBeVisible();
  await expect(page.getByLabel("Trader sort")).toBeVisible();
  await expect(page.getByLabel("Filter loaded results")).toBeVisible();

  await page.getByRole("link", { name: "Trader PnL" }).focus();
  await expect(page.getByRole("link", { name: "Trader PnL" })).toBeFocused();
  const outline = await page
    .getByRole("link", { name: "Trader PnL" })
    .evaluate((element) => getComputedStyle(element).outlineStyle);
  expect(outline).not.toBe("none");
});

test("all supported viewports avoid document-level horizontal overflow", async ({
  page,
}) => {
  await mockLeaderboard(page);
  for (const viewport of [
    { width: 320, height: 640 },
    { width: 375, height: 812 },
    { width: 768, height: 1024 },
    { width: 1024, height: 768 },
    { width: 1440, height: 900 },
  ]) {
    await page.setViewportSize(viewport);
    await page.goto("/leaderboard");
    await expect(
      page.getByRole("heading", { name: "Leaderboard" }),
    ).toBeVisible();
    await expect(page.getByLabel("Filter loaded results")).toBeVisible();
    const dimensions = await page.evaluate(() => ({
      clientWidth: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
    }));
    expect(
      dimensions.scrollWidth,
      JSON.stringify(viewport),
    ).toBeLessThanOrEqual(dimensions.clientWidth);
  }
});

test("the browser interface issues no external or mutating requests", async ({
  page,
}) => {
  const prohibited: string[] = [];
  page.on("request", (request) => {
    const url = request.url();
    if (
      request.method() !== "GET" ||
      url.includes("api.pump.fun") ||
      url.includes("frontend-api-v3.pump.fun")
    ) {
      prohibited.push(`${request.method()} ${url}`);
    }
  });
  await mockLeaderboard(page);
  await page.goto("/leaderboard");
  await page.getByRole("link", { name: "Creator payouts" }).click();
  await expect(
    page.getByRole("list", { name: "Creator payout rankings" }),
  ).toBeVisible();
  expect(prohibited).toEqual([]);
});

async function allowLocalNavigationRequests(page: Page) {
  const unexpected: string[] = [];
  await page.route("**/*", async (route) => {
    const request = route.request();
    if (
      new URL(request.url()).origin !== "http://127.0.0.1:3010" ||
      !["GET", "HEAD"].includes(request.method())
    ) {
      unexpected.push(`${request.method()} ${request.url()}`);
      await route.abort();
      return;
    }
    await route.continue();
  });
  return unexpected;
}

test("competition title filters do not hide participants after opening detail", async ({
  page,
}, testInfo) => {
  const unexpected = await allowLocalNavigationRequests(page);
  const requests: string[] = [];
  page.on("request", (request) => {
    if (new URL(request.url()).pathname === "/api/leaderboard")
      requests.push(`${request.method()} ${request.url()}`);
  });
  await mockLeaderboard(page);
  await page.goto(
    "/leaderboard?category=competitions&status=live&q=browser-test",
  );
  await expect(
    page.getByText("Synthetic browser-test competition", { exact: true }),
  ).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("filtered-list.png") });
  const detail = page.getByRole("link", { name: "View ranked entries" });
  await detail.focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("list", { name: "Competition rankings" }),
  ).toContainText("synthetic-entrant");
  await expect(page.getByLabel("Filter loaded results")).toHaveValue("");
  await expect(page).not.toHaveURL(/[?&]q=/);
  await expect(page).toHaveURL(/status=live/);
  await page.screenshot({ path: testInfo.outputPath("unfiltered-detail.png") });
  await page.goBack();
  await expect(page.getByLabel("Filter loaded results")).toHaveValue(
    "browser-test",
  );
  await expect(
    page.getByText("Synthetic browser-test competition", { exact: true }),
  ).toBeVisible();
  await page.goForward();
  await expect(
    page.getByRole("list", { name: "Competition rankings" }),
  ).toContainText("synthetic-entrant");
  expect(unexpected).toEqual([]);
  await testInfo.attach("local-api-requests", {
    body: JSON.stringify(requests, null, 2),
    contentType: "application/json",
  });
});

test("participant filters do not hide competitions when returning to the list", async ({
  page,
}, testInfo) => {
  const unexpected = await allowLocalNavigationRequests(page);
  const requests: string[] = [];
  page.on("request", (request) => {
    if (new URL(request.url()).pathname === "/api/leaderboard")
      requests.push(`${request.method()} ${request.url()}`);
  });
  await mockLeaderboard(page);
  await page.goto(
    "/leaderboard?category=competitions&status=live&competition=synthetic-competition&q=synthetic-entrant",
  );
  await expect(
    page.getByRole("list", { name: "Competition rankings" }),
  ).toContainText("synthetic-entrant");
  await page.screenshot({ path: testInfo.outputPath("filtered-detail.png") });
  await page.getByRole("button", { name: /Back to competitions/ }).click();
  await expect(
    page.getByRole("link", { name: "View ranked entries" }),
  ).toBeVisible();
  await expect(page.getByLabel("Filter loaded results")).toHaveValue("");
  await expect(page).not.toHaveURL(/[?&](q|competition|page)=/);
  await expect(page).toHaveURL(/status=live/);
  await page.screenshot({ path: testInfo.outputPath("unfiltered-list.png") });
  expect(unexpected).toEqual([]);
  await testInfo.attach("local-api-requests", {
    body: JSON.stringify(requests, null, 2),
    contentType: "application/json",
  });
});
