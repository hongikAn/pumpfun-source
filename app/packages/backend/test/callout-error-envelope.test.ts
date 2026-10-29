import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { buildApp } from "./with-api-key.js";
import { CalloutsStore } from "../src/callouts-store.js";
import { CalloutDiscussionsStore } from "../src/callout-discussions-store.js";
import { assertSchema } from "../src/schema-validator.js";

const spec = JSON.parse(readFileSync(
  new URL("../../../contracts/developer.openapi.json", import.meta.url), "utf8",
));
function app() {
  const common = { schemaVersion: 1, dataSource: "synthetic", observedAt: "2026-10-29T00:00:00.000Z" };
  const callouts = new CalloutsStore({
    ...common,
    authors: [{ authorId: "known", userName: "Known", profileImage: null,
      isVerified: false, verifiedBadgeVisible: false, accountKind: "person",
      xUsername: null, xFollowerCount: 0 }],
    callouts: [], updates: [],
  });
  const discussions = new CalloutDiscussionsStore({
    ...common, complete: true, calloutIds: [], authors: [], replies: [],
  }, callouts);
  return buildApp([], { calloutsStore: callouts, calloutDiscussionsStore: discussions });
}
const cases = [
  ["/callout/user/{userId}/mint/{coinMint}", "/callout/user/known/mint/m?quotesLimit=0&quotesLimit=0", 400, "CALLOUT_LOOKUP_QUERY_INVALID"],
  ["/callout/user/{userId}/mint/{coinMint}", "/callout/user/known/mint/m?quotesLimit=21", 400, "CALLOUT_LOOKUP_QUERY_INVALID"],
  ["/callout/user/{userId}/mint/{coinMint}", "/callout/user/known/mint/m?unsupported=1", 501, "CALLOUT_LOOKUP_QUERY_UNSUPPORTED"],
  ["/callout/user/{userId}/mint/{coinMint}", "/callout/user/known/mint/m?quotesLimit=1", 501, "CALLOUT_LOOKUP_QUERY_UNSUPPORTED"],
  ["/callout/user/{userId}/mint/{coinMint}", "/callout/user/unknown/mint/m", 501, "CALLOUT_LOOKUP_UNKNOWN"],
  ["/callout/list/{userId}", "/callout/list/known?limit=0", 400, "CALLOUT_LIST_QUERY_INVALID"],
  ["/callout/list/{userId}", "/callout/list/unknown", 501, "CALLOUT_LIST_AUTHOR_UNAVAILABLE"],
  ["/callout/list/{userId}", "/callout/list/known?window=daily", 501, "CALLOUT_LIST_WINDOW_UNAVAILABLE"],
  ["/callout/{calloutId}", "/callout/missing?unsupported=1", 501, "CALLOUT_QUERY_UNSUPPORTED"],
  ["/callout/{calloutId}/replies", "/callout/missing/replies?limit=0", 400, "CALLOUT_DISCUSSION_QUERY_INVALID"],
  ["/callout/{calloutId}/replies", "/callout/missing/replies", 501, "CALLOUT_DISCUSSION_UNAVAILABLE"],
  ["/callout/replies/{replyId}/chain", "/callout/replies/missing/chain?unsupported=1", 501, "CALLOUT_DISCUSSION_QUERY_UNSUPPORTED"],
  ["/callout/replies/{replyId}/chain", "/callout/replies/missing/chain", 501, "CALLOUT_DISCUSSION_REPLY_UNAVAILABLE"],
] as const;

for (const [operation, path, status, reason] of cases) {
  test(`callout error envelope: ${status} ${path}`, async () => {
    const server = app();
    try {
      const response = await server.inject({ url: `/v1${path}` });
      assert.equal(response.statusCode, status);
      const body = response.json();
      assert.equal(body.reason, reason);
      assert.equal(body.error, status === 400 ? "BAD_REQUEST" : "COMPATIBILITY_NOT_IMPLEMENTED");
      assert.equal(body.statusCode, response.statusCode);
      const contract = spec.paths[operation].get.responses[status] ?? spec.paths[operation].get.responses.default;
      const resolved = contract.$ref ? spec.components.responses[contract.$ref.split("/").at(-1)] : contract;
      assertSchema(body, resolved.content["application/json"].schema, "error response", spec);
      assert.equal(response.headers["x-reconstruction-data-source"], undefined);
    } finally {
      await server.close();
    }
  });
}
for (const [path, expected] of [
  ["/callout/missing", { callout: null }],
  ["/callout/list/known", { callouts: [], nextPageToken: "" }],
  ["/callout/user/known/mint/m", { callout: null, quotes: [] }],
] as const) {
  test(`callout success envelope remains unchanged: ${path}`, async () => {
    const server = app();
    try {
      const response = await server.inject({ url: `/v1${path}` });
      assert.equal(response.statusCode, 200);
      assert.deepEqual(response.json(), expected);
      assert.equal(response.headers["x-reconstruction-data-source"], "synthetic");
    } finally {
      await server.close();
    }
  });
}
test("callout API key rejection still precedes the native error path", async () => {
  const server = app();
  try {
    const response = await server.inject({ url: "/v1/callout/list/known?limit=0", headers: { authorization: "" } });
    assert.equal(response.statusCode, 401);
    assert.equal(response.json().statusCode, 401);
    assert.equal(response.json().error, "API_KEY_REQUIRED");
  } finally {
    await server.close();
  }
});
