# Native local Home Feed frontend integration

This note documents the opt-in, read-only connection between the existing
offline Home Feed and the local Home Feed backend proposed by PR #700. It does
not establish production Pump.fun compatibility.

## Dependency and provenance

- Existing offline frontend: PR #556. Its hash-bound synthetic posts remain the
  default `/` view.
- Local backend contract: PR #700 at reviewed head
  `c0b3b57c031ddfca88792be56634e577abc23c39`. The backend defines the three
  local reads, response projections, opaque cursors, synthetic seed, provenance
  headers, and `local-unqualified` compatibility label.
- Captured website contract attribution: PR #686. It establishes the original
  request chain and `frontend-api-v3.pump.fun` origin, but does not make this
  local backend production-compatible.
- Captured UI evidence and the original offline design boundary remain in
  [`HOME-FEED-EVIDENCE.md`](HOME-FEED-EVIDENCE.md).

The backend records are deliberately synthetic. The frontend always displays
“Synthetic local callout data” and “Not live Pump.fun activity.” It does not
combine callout records with the separate synthetic post model.

## Opt-in and transport boundary

The local callout tab is present only when the **server process** has:

```sh
PUMP_LOCAL_HOME_FEED=enabled
```

No `NEXT_PUBLIC_` variable is used. The destination is the fixed loopback URL
`http://127.0.0.1:3001`; an environment variable, browser query parameter, or
request header cannot replace it. The browser requests only the local Next
server. Next performs bounded server-side GET requests with a two-second
timeout, `cache: no-store`, omitted credentials, and no caller headers.

The adapter never falls back to Pump.fun, another origin, or invented rows. A
missing backend, non-200 response, invalid cursor, malformed JSON, wrong content
type, wrong provenance header, wrong compatibility header, or invalid response
shape produces an explicit unavailable state.

## Accepted local response surface

The adapter consumes only:

- `GET /services/frontend/home-feed?pageSize=3[&pageToken=…]`
- `GET /services/frontend/home-feed/new?pageSize=3[&pageToken=…]`
- `GET /services/frontend/home-feed/new/count?since=…`

A successful response must include:

- `X-Reconstruction-Data-Source: synthetic-home-feed-local-v1`
- `X-Reconstruction-Compatibility: local-unqualified`
- JSON content type
- HTTP 200

Validation bounds arrays, safe strings, canonical timestamps, finite
non-negative numbers, supported chains and asset classes, null image/wallet
fields, unverified author state, unique callout identities, local unavailable
realtime subject, cursor shape, and the 25-row count cap. React performs normal
text escaping; captured HTML is never rendered.

The UI displays the backend-supplied coin name, symbol, chain, projected asset
class, author, thesis, callout timestamp, local market-cap values, local cost
basis, and local multiple. It does not display a remote image, live price,
volume, liquidity, wallet balance, follower count, verified identity, or
production rank.

## Pagination and snapshot behavior

Ranked and newest pages use separate URL-backed views. Cursors remain opaque:
the frontend bounds and forwards them but does not decode or manufacture their
contents. A maximum 20-entry local cursor trail supports Previous and browser
Back/Forward navigation without an unbounded request loop. The first page has no
cursor, the second has a cursor with an empty trail, and page 22 has 20 saved prior
cursors. At that boundary, if the backend still supplies a next token, the UI does
not emit a page 23 link that its own parser would reject. It explains the local
navigation limit, retains Previous and offers a reset to the first page of the
**same ordering**. This is not a claim that the dataset ended: real end-of-list
text is reserved for responses without a next token. Unsupported externally
supplied histories still fail closed. Switching ordering resets the cursor namespace.

The default CLI seed has only eight visible ranked records and does not normally
reach this bound. The existing documented `buildApp([], { homeFeedStore })` test
injection accepts a `HomeFeedStore` with up to 500 validated synthetic records; no
new runtime dataset loader, default seed, source marker or backend capability is
introduced by the navigation correction.

The first newest page supplies a local `headToken`. That exact token is passed
to `/new/count`; the resulting value is labelled as a local snapshot count.
`liveSubject` is validated only as the backend's explicit realtime-unavailable
sentinel. No WebSocket, polling loop, or realtime claim is implemented.

## Verification

Unit and bounded loopback tests:

```sh
pnpm test:feed
pnpm --filter @pump-reconstruction/frontend test:browser:native-feed
```

The browser suite starts an isolated loopback server and verifies the success,
empty, unavailable, malformed JSON, wrong content type, wrong provenance,
wrong compatibility, duplicate identity, cursor, pagination, history,
new-count, keyboard, network, and six responsive viewport cases.

PR #700 integration is tested separately so its commits are not copied into
this frontend branch. In a worktree containing PR #700 plus this frontend diff:

```sh
pnpm --filter @pump-reconstruction/backend build
pnpm --filter @pump-reconstruction/backend start
PUMP_LOCAL_HOME_FEED=enabled pnpm --filter @pump-reconstruction/frontend \
  exec next dev --turbopack --hostname 127.0.0.1 --port 3012
pnpm --filter @pump-reconstruction/frontend test:browser:native-feed-real
```

The reviewed PR #700 head passed both real-backend browser cases: ranked pages
contained 3, 3, and 2 visible records; newest pagination and the pinned zero
count matched the backend; browser traffic stayed on the Next origin.

## Unqualified behavior

- Production Pump.fun data, ranking, cursor bytes, request compatibility, and
  authenticated personalization.
- Current prices, markets, balances, users, follow graph, realtime delivery,
  mutations, wallet access, signing, or trading.
- Original visual parity and production error wording.

The Home/feed ledger remains at its existing 3/3 source and 3/4 completion
milestones. This integration adds a tested local read path but does not satisfy
the pending original-visual-consistency milestone or qualify a production API.

## Cursor-history boundary regression (2026-10-29)

On unchanged main app tree `667ee19b0ac2ef091995950c1f88a8fda94ea045`, both
ranked and newest flows can advance normally through 22 pages of an injected
500-record store at the existing page size 3. Each displayed next link forwards
the actual backend-issued opaque token. After 66 rows, the old renderer appends a
21st history entry and links to page 23, where `parseNativeFeedNavigation` rejects
it. This is a maintained local integration defect, not a newly inferred original
pagination rule or a problem with the existing 20-entry bound.

`node --test tests/native_feed_history.test.mjs` is included by the existing
root MJS wildcard. It invokes the ordinary pinned tsx loader, not its IPC CLI,
with the existing frontend JSX config. Four child cases use the actual Fastify
GET handlers through `app.inject`, response validator, maintained component,
React server renderer, Next Link and navigation parser. Ranked/newest 500-record
cases cover the boundary, exact Previous/forward roundtrip, same-order reset,
continued backend availability, unchanged rejection of oversized history, and
true-end priority when no next token exists. Two default-seed controls retain the
existing terminal behavior. No token is fabricated or decoded by the frontend.

These are deterministic synthetic route/SSR integration checks: no listening
server, network request, captured JavaScript execution, real user data or wallet
operation runs. Server-rendered link attributes are inspected, not browser clicks.
Native browser Back/Forward, hydration, focus, responsive layout and visual parity
remain separate and are not established by these tests. The isolated DOM tooling
used for other private reviews is not a new repository dependency here.

Candidate verification: the same four child cases produce two boundary failures
and two unchanged-default passes on the exact baseline; all four pass after the
correction. The automatic wrapper passes in the root MJS suite (292 tests), all
139 root TypeScript tests and 588 backend tests pass, and full SDK/backend/Next
production build and all three package typechecks pass. The 698-object evidence
check, progress freshness check and all 79 Python tests pass. Required repository
root checks pass on authenticated inputs: nine static captures and six synthetic
comparator controls, with no native execution. No browser execution or new
screenshots were performed; the existing browser receipts remain historical,
not validation of this correction.

A separate private ancestry composition with the then-open feed filter-context
PR807 (`0a714c2f599cb45ef0dd84cf5e7cde021e78d4ae`) and query-validation PR895
(`c9e036f8b90e019484890a015c8c602743bc9abc`) merges without conflicts. Its exact
application delta is these five paths plus their four backend paths. All four
route/SSR cases and 593 backend tests pass on that composition; backend typecheck
also passes. This is not an actual GitHub merge, a browser result, or a request to
include the other authors' changes in this correction.

## Same-order cursor recovery (2026-10-29)

The first-page recovery link retains a valid selected local ordering when a
cursor is rejected by the local backend or fails URL validation. A malformed
cursor in Local newest therefore returns to the first newest page, including its
head-bound count request. Unknown or repeated ordering parameters still fail
closed and offer the ranked first page. This corrects the local integration; it
does not establish the original site's error policy or production cursor rules.

The focused native-feed browser suite passes all 12 cases, including two new
newest recovery cases and an invalid-ordering control. The backend-rejected case
failed on the unchanged source because recovery linked to Local ranked. These
checks use the existing loopback fixture server and make no production requests.
