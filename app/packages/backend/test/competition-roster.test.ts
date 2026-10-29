import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { buildApp } from './with-api-key.js';
import { CompetitionStore, type RawCompetition } from '../src/competitions-store.js';
import { assertSchema, type SchemaNode, type SchemaRoot } from '../src/schema-validator.js';

const seeds = JSON.parse(readFileSync(new URL('../src/competitions-seed.json', import.meta.url), 'utf8')) as RawCompetition[];
const spec = JSON.parse(readFileSync(new URL('../../../contracts/developer.openapi.json', import.meta.url), 'utf8'));
const detailSchema = spec.paths['/competitions/{id}/entries/{entryId}'].get.responses['200'].content['application/json'].schema as SchemaNode;

function person(phase: RawCompetition['phase'], built = false): RawCompetition {
  const comp = structuredClone(seeds.find(row => row.kind === 'person' && row.phase === 'live')!);
  Object.assign(comp, {
    phase, isFinal: phase === 'ended', joinable: phase === 'registration',
    registrationOpensAt: '2026-10-28T00:00:00Z',
    registrationClosesAt: '2026-10-31T00:00:00Z',
    startsAt: '2026-10-30T00:00:00Z', endsAt: '2026-11-01T00:00:00Z',
  });
  comp.entries = comp.entries.map(entry => ({
    ...entry, registeredAt: '2026-10-29T00:00:00Z',
    pnlUsd: 0, realizedPnlUsd: 0, unrealizedPnlUsd: 0, buySpendSol: 0,
    membersFresh: built ? 1 : 0,
    lastRefreshedAtMs: built ? Date.parse('2026-10-30T01:00:00Z') : 0,
    positions: [], highlightTokens: [],
  }));
  return comp;
}

async function readEntry(comp: RawCompetition) {
  const app = buildApp([], { competitionStore: new CompetitionStore([comp]) });
  try {
    const response = await app.inject(`/v1/competitions/${comp.id}/entries/${comp.entries[0].entryId}`);
    assert.equal(response.statusCode, 200);
    const json = response.json();
    assertSchema(json, detailSchema, 'entry snapshot roster', spec as SchemaRoot);
    return json;
  } finally {
    await app.close();
  }
}

for (const phase of ['upcoming', 'registration'] as const) {
  test(`${phase} person detail has no snapshot roster before startsAt`, async () => {
    const comp = person(phase);
    const json = await readEntry(comp);
    assert.equal(json.entry.rank, 0);
    assert.equal(json.entry.walletAddress, null);
    assert.deepEqual({ memberCount: json.entry.memberCount, members: json.members }, { memberCount: 0, members: [] });
    const app = buildApp([], { competitionStore: new CompetitionStore([comp]) });
    try {
      const response = await app.inject(`/v1/competitions/${comp.id}`);
      assert.equal(response.statusCode, 200);
      const board = response.json();
      assert.equal(board.competition.entriesCount, comp.entries.length);
      assert.equal(board.competition.participants, comp.entries.filter(entry => !entry.struck).length);
      assert.equal(board.leaderboard.builtAtMs, 0);
      assert.deepEqual(board.leaderboard.entries, []);
    } finally {
      await app.close();
    }
  });
}

test('live person keeps its snapshot roster before the first board build', async () => {
  const comp = person('live');
  const json = await readEntry(comp);
  assert.equal(json.entry.rank, 0);
  assert.equal(json.entry.walletAddress, null);
  assert.equal(json.entry.memberCount, 1);
  assert.equal(json.members.length, 1);
  assert.equal(json.members[0].userId, comp.entries[0].participantId);
  assert.ok(json.members[0].walletAddress);
  assert.equal(json.members[0].lastRefreshedAtMs, 0);
  assert.equal(json.members[0].fresh, false);
});

for (const phase of ['live', 'ended'] as const) {
  test(`${phase} built person retains its sole member`, async () => {
    const comp = person(phase, true);
    const json = await readEntry(comp);
    assert.equal(json.entry.memberCount, 1);
    assert.equal(json.members.length, 1);
    assert.equal(json.members[0].walletAddress, json.entry.walletAddress);
    assert.equal(json.members[0].lastRefreshedAtMs, comp.entries[0].lastRefreshedAtMs);
  });
}

test('live walletless and struck people retain their snapshot member', async () => {
  for (const condition of ['walletless', 'struck'] as const) {
    const comp = person('live', true);
    if (condition === 'walletless') comp.entries[0].walletAddress = null;
    else comp.entries[0].struck = true;
    const json = await readEntry(comp);
    assert.equal(json.entry.rank, 0);
    assert.equal(json.entry.memberCount, 1);
    assert.equal(json.members.length, 1);
    if (condition === 'walletless') assert.equal(json.members[0].walletAddress, null);
    else assert.ok(json.members[0].walletAddress);
  }
});

test('supplied group snapshot members are retained', async () => {
  const comp = structuredClone(seeds.find(row => row.kind === 'group')!);
  const json = await readEntry(comp);
  assert.equal(json.entry.memberCount, comp.entries[0].members!.length);
  assert.equal(json.members.length, comp.entries[0].members!.length);
  assert.deepEqual(json.members.map((member: { userId: string }) => member.userId).sort(), comp.entries[0].members!.map(member => member.userId).sort());
});
