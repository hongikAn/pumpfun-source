import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { buildApp } from './with-api-key.js';
import { LeaderboardStore, type RawLeaderboardEntry } from '../src/leaderboard-store.js';
import { UserStore, SYNTHETIC_SEED, DATA_SOURCE } from '../src/users-store.js';

const spec = JSON.parse(readFileSync(new URL('../../../contracts/developer.openapi.json', import.meta.url), 'utf8'));
const alice = SYNTHETIC_SEED[0];
function row(userId: string | null): RawLeaderboardEntry {
  return {
    userId, walletAddress: alice.address,
    pnlSol: 2, pnlUsd: 20, pnlPercent: 25, buySpendSol: 8,
    realizedPnlSol: 1, realizedPnlUsd: 10,
    unrealizedPnlSol: 1, unrealizedPnlUsd: 10,
    lastRefreshedAtMs: 1759276800000, positions: [],
  };
}

for (const [label, input, expected] of [
  ['missing profile', 'not-in-registry', null],
  ['known canonical id', alice.userId, alice.userId],
  ['known address alias', alice.address, alice.address],
  ['wallet-only row', null, null],
] as const) {
  test(`leaderboard identity hydration: ${label}`, async t => {
    assert.equal(spec.paths['/pnl-leaderboard'].get.responses['200'].content['application/json']
      .schema.properties.entries.items.properties.userId.description, 'Null when the profile lookup missed');
    const facts = row(input);
    const leaderboardStore = new LeaderboardStore({ daily: [facts], weekly: [facts], monthly: [facts] },
      new UserStore([alice]));
    // A separate app store must not supply a different registry to this board.
    const app = buildApp([], { leaderboardStore, userStore: new UserStore([]) });
    t.after(() => app.close());
    for (const period of ['daily', 'weekly', 'monthly']) {
      const response = await app.inject(`/v1/pnl-leaderboard?period=${period}`);
      assert.equal(response.statusCode, 200);
      assert.equal(response.headers['x-reconstruction-data-source'], DATA_SOURCE);
      const entry = response.json().entries[0];
      assert.equal(entry.userId, expected);
      assert.equal(entry.walletAddress, facts.walletAddress);
      assert.equal(entry.pnlUsd, facts.pnlUsd);
      assert.equal(entry.rank, 1);
      assert.equal(entry.username, expected === null ? null : alice.username);
      assert.equal(entry.profileImage, expected === null ? null : alice.profile_image);
      assert.equal(entry.xUsername, expected === null ? null : alice.x_username);
      if (expected === null) {
        assert.equal(entry.isVerified, false);
        assert.equal(entry.verifiedBadgeVisible, false);
      }
    }
  });
}
