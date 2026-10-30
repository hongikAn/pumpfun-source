import { createServer } from "node:http";

const HOST = "127.0.0.1";
const PORT = 3001;
const SOURCE = "synthetic-home-feed-local-v1";
const COMPATIBILITY = "local-unqualified";
const RANK_CURSOR = "eyJ2IjoxLCJrIjoicmFuayJ9.rank_signature";
const NEW_CURSOR = "eyJ2IjoxLCJrIjoibmV3In0.new_signature";
const HEAD_CURSOR = "eyJ2IjoxLCJrIjoiaGVhZCJ9.head_signature";

let mode = "normal";
let requests = [];

function coin(index) {
  return {
    coinMint: `LOCAL_EXAMPLE_MINT_00${index}`,
    coinName: `Local Example ${["Alpha", "Beta", "Gamma", "Delta"][index - 1]}`,
    coinImage: null,
    symbol: `LX${index}`,
    coinDescription: null,
    marketCap: 100_000 + index * 1_000,
    protocol: null,
    platform: null,
    program: null,
    chain: index % 2 === 0 ? "base" : "solana",
    narrative: null,
    position: {
      userId: `local-author-${index}`,
      userName: `Local Author ${index}`,
      profileImage: null,
      walletAddress: null,
      isVerified: false,
      verifiedBadgeVisible: false,
      resolvedAvatarDecoration: null,
      accountKind: "person",
      followerCount: null,
      xUsername: null,
      xProfileImage: null,
      totalCallouts: 1,
      amountHeld: 0,
      valueUsd: null,
      pnlUsd: null,
      pnlPercentage: null,
      realizedPnlUsd: 0,
      tokenPriceUsd: null,
      costBasisAmount: 0,
      costBasisUsd: 500 + index,
      amountBoughtUsd: null,
      amountBought: null,
      callout: {
        calloutId: `00000000-0000-4000-8000-00000000000${index}`,
        chain: index % 2 === 0 ? "base" : "solana",
        assetClass: "ASSET_CLASS_TOKEN",
        calledOutAtMcap: 90_000 + index * 1_000,
        multiple: 1 + index / 10,
        thesis: `Synthetic local thesis ${index}.`,
        mediaUrl: null,
        calloutTimestamp: `2026-10-28T11:${String(60 - index * 5).padStart(2, "0")}:00.000Z`,
        likes: 0,
        hasLiked: null,
        updates: [],
        updateCount: 0,
        commentCount: 0,
        replyCount: 0,
        maxMultiplier: null,
        maxMultiplierAt: null,
        calloutPrice: 0,
        repostCount: 0,
        quoteCount: 0,
        hasReposted: null,
        actingUserId: `local-author-${index}`,
        actingUser: null,
        quotedCallout: null,
      },
      contentKind: "callout",
      quote: null,
    },
    followedHolders: null,
  };
}

function sendJson(response, status, body, headers = {}) {
  response.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
    "x-reconstruction-data-source": SOURCE,
    "x-reconstruction-compatibility": COMPATIBILITY,
    ...headers,
  });
  response.end(JSON.stringify(body));
}

function feedResponse(requestUrl, newest) {
  const token = requestUrl.searchParams.get("pageToken");
  if (token && token !== (newest ? NEW_CURSOR : RANK_CURSOR)) return null;
  if (mode === "empty") {
    return newest
      ? {
          coins: [],
          headToken: null,
          liveSubject: "local.reconstruction.realtime-unavailable",
        }
      : { coins: [] };
  }
  const coins = token ? [coin(4)] : [coin(1), coin(2), coin(3)];
  const body = { coins };
  if (!token) body.nextPageToken = newest ? NEW_CURSOR : RANK_CURSOR;
  if (newest) {
    body.headToken = token ? null : HEAD_CURSOR;
    body.liveSubject = "local.reconstruction.realtime-unavailable";
  }
  if (mode === "duplicate") body.coins = [coin(1), coin(1)];
  return body;
}

const server = createServer((request, response) => {
  const requestUrl = new URL(request.url ?? "/", `http://${HOST}:${PORT}`);
  if (requestUrl.pathname === "/__health") {
    return sendJson(response, 200, { ok: true });
  }
  if (requestUrl.pathname === "/__control" && request.method === "POST") {
    let body = "";
    request.on("data", (chunk) => {
      body += chunk;
    });
    request.on("end", () => {
      const parsed = JSON.parse(body || "{}");
      mode = typeof parsed.mode === "string" ? parsed.mode : "normal";
      requests = [];
      sendJson(response, 200, { mode });
    });
    return;
  }
  if (requestUrl.pathname === "/__requests") {
    return sendJson(response, 200, { requests });
  }

  requests.push(`${request.method} ${requestUrl.pathname}${requestUrl.search}`);
  if (mode === "unavailable")
    return sendJson(response, 503, { error: "LOCAL_UNAVAILABLE" });
  if (mode === "malformed") {
    response.writeHead(200, {
      "content-type": "application/json",
      "x-reconstruction-data-source": SOURCE,
      "x-reconstruction-compatibility": COMPATIBILITY,
    });
    return response.end("{not-json");
  }
  if (mode === "wrong-content-type") {
    response.writeHead(200, {
      "content-type": "text/plain; charset=utf-8",
      "x-reconstruction-data-source": SOURCE,
      "x-reconstruction-compatibility": COMPATIBILITY,
    });
    return response.end(JSON.stringify({ coins: [coin(1)] }));
  }

  const headers = {};
  if (mode === "wrong-source")
    headers["x-reconstruction-data-source"] = "unknown";
  if (mode === "wrong-compatibility")
    headers["x-reconstruction-compatibility"] = "production";
  if (mode === "wrong-cache") headers["cache-control"] = "public, max-age=60";

  if (requestUrl.pathname === "/services/frontend/home-feed/new/count") {
    if (mode === "count-unavailable")
      return sendJson(response, 503, { error: "LOCAL_UNAVAILABLE" });
    if (mode === "count-malformed") {
      response.writeHead(200, {
        "content-type": "application/json",
        "cache-control": "no-store",
        "x-reconstruction-data-source": SOURCE,
        "x-reconstruction-compatibility": COMPATIBILITY,
      });
      return response.end("{not-json");
    }
    if (mode === "count-unproven")
      headers["x-reconstruction-data-source"] = "unknown";
    if (requestUrl.searchParams.get("since") !== HEAD_CURSOR) {
      return sendJson(response, 400, { error: "INVALID_CURSOR" }, headers);
    }
    return sendJson(
      response,
      200,
      { newCount: 0, capped: false, headToken: HEAD_CURSOR },
      headers,
    );
  }
  const newest = requestUrl.pathname === "/services/frontend/home-feed/new";
  const ranked = requestUrl.pathname === "/services/frontend/home-feed";
  if (newest || ranked) {
    const body = feedResponse(requestUrl, newest);
    return body
      ? sendJson(response, 200, body, headers)
      : sendJson(response, 400, { error: "INVALID_CURSOR" }, headers);
  }
  return sendJson(response, 404, { error: "NOT_FOUND" });
});

server.listen(PORT, HOST, () => {
  process.stdout.write(
    `native feed test server listening on http://${HOST}:${PORT}\n`,
  );
});

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => server.close(() => process.exit(0)));
}
