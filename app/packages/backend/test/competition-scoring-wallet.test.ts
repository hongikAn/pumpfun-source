import { test } from 'node:test';
import assert from 'node:assert/strict';
import seed from '../src/competitions-seed.json' with { type: 'json' };
import { CompetitionStore, type RawCompetition } from '../src/competitions-store.js';
import { UserStore } from '../src/users-store.js';
import { buildApp } from './with-api-key.js';

const snapshotWallet = '11111111111111111111111111111112';
function competition(kind: 'person' | 'group' = 'person'): RawCompetition {
  return structuredClone(seed.find(row => row.kind === kind && row.entries.length > 0)) as RawCompetition;
}

for (const phase of ['live', 'ended'] as const) {
  test(`an explicit absent scoring wallet has rank zero on the ${phase} board`, async () => {
    const comp = competition();
    comp.phase = phase;
    comp.isFinal = phase === 'ended';
    comp.entries = comp.entries.slice(0, 3);
    const [absent, supplied, legacy] = comp.entries;
    Object.assign(absent, { walletAddress: null, pnlUsd: 1000 });
    Object.assign(supplied, { walletAddress: snapshotWallet, pnlUsd: 20 });
    legacy.pnlUsd = 10;
    const app = buildApp([], { competitionStore: new CompetitionStore([comp]) });
    try {
      const response = await app.inject(`/v1/competitions/${comp.id}`);
      assert.equal(response.statusCode, 200);
      const body = response.json();
      assert.deepEqual(body.leaderboard.entries.map((row: any) => [row.entryId, row.rank]),
        [[supplied.entryId, 1], [legacy.entryId, 2]]);
      assert.equal(body.leaderboard.totalRanked, 2);
      assert.equal(body.competition.participants, 3); // Registered, non-struck entries still count.
      const projected = phase === 'live' ? body.competition.top : body.competition.winners;
      assert.deepEqual(projected.map((row: any) => row.entryId), [supplied.entryId, legacy.entryId]);
      assert.equal(projected[0].walletAddress, snapshotWallet);
      const detail = (await app.inject(`/v1/competitions/${comp.id}/entries/${absent.entryId}`)).json();
      assert.equal(detail.entry.rank, 0);
      assert.equal(detail.entry.walletAddress, null);
      assert.equal(detail.members[0].walletAddress, null);
      assert.equal(detail.entry.struck, false);
      const buckets = (await app.inject('/v1/competitions')).json();
      const view = (phase === 'live' ? buckets.live : buckets.past)[0];
      assert.deepEqual((phase === 'live' ? view.top : view.winners).map((row: any) => row.entryId),
        [supplied.entryId, legacy.entryId]);
      const highlights = (await app.inject(`/v1/competitions/${comp.id}/highlights`)).json();
      assert.ok(highlights.rows.every((row: any) => row.entryId !== absent.entryId));
    } finally {
      await app.close();
    }
  });
}

test('a supplied person wallet remains the snapshot wallet instead of the current profile wallet', () => {
  const comp = competition();
  comp.entries = comp.entries.slice(0, 1);
  Object.assign(comp.entries[0], { walletAddress: snapshotWallet });
  const store = new CompetitionStore([comp]);
  const result = store.getByIdOrSlug(comp.id)!;
  assert.equal(result.leaderboard.entries[0].walletAddress, snapshotWallet);
  const detail = store.getEntryDetail(comp.id, comp.entries[0].entryId)!;
  assert.equal(detail.entry.walletAddress, snapshotWallet);
  assert.equal(detail.members[0].walletAddress, snapshotWallet);
});

test('a supplied wallet does not rank a pre-build board, but remains in its snapshot roster', () => {
  const comp = competition();
  comp.entries = comp.entries.slice(0, 1);
  Object.assign(comp.entries[0], { walletAddress: snapshotWallet, lastRefreshedAtMs: 0 });
  const store = new CompetitionStore([comp]);
  assert.deepEqual(store.getByIdOrSlug(comp.id)!.leaderboard.entries, []);
  const detail = store.getEntryDetail(comp.id, comp.entries[0].entryId)!;
  assert.equal(detail.entry.rank, 0);
  assert.equal(detail.entry.walletAddress, null);
  assert.equal(detail.members[0].walletAddress, snapshotWallet);
});

test('omitted scoring-wallet facts preserve legacy ranking even when profile hydration misses', () => {
  const comp = competition();
  const store = new CompetitionStore([comp], new UserStore([]));
  const entries = store.getByIdOrSlug(comp.id)!.leaderboard.entries;
  assert.equal(entries.length, comp.entries.filter(row => !row.struck).length);
  assert.ok(entries.every(row => row.rank > 0 && row.walletAddress === null));
});

test('the person-only snapshot field does not alter group ranking or member wallets', () => {
  const comp = competition('group');
  const before = new CompetitionStore([comp]).getEntryDetail(comp.id, comp.entries[0].entryId);
  for (const entry of comp.entries) Object.assign(entry, { walletAddress: null });
  const store = new CompetitionStore([comp]);
  assert.deepEqual(store.getEntryDetail(comp.id, comp.entries[0].entryId), before);
  assert.equal(store.getByIdOrSlug(comp.id)!.leaderboard.totalRanked, comp.entries.filter(row => !row.struck).length);
});
