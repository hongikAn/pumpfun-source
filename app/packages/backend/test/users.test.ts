import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import { buildApp } from './with-api-key.js';
import { UserStore, type User } from '../src/users-store.js';

/*──────────────────────────────────────────────────────────────
 * Helpers
 *────────────────────────────────────────────────────────────*/

/** The required keys that MUST be present on every user row (per the contract). */
const USER_REQUIRED_KEYS = ['address', 'username', 'profile_image', 'bio', 'followers', 'following', 'x_username'] as const;

/** All keys the contract allows on a user row. No extras permitted (additionalProperties: false). */
const USER_ALLOWED_KEYS = new Set([
  'address', 'userId', 'username', 'profile_image', 'header_image_url',
  'avatar_decoration', 'resolved_avatar_decoration', 'kind', 'member_count',
  'group_badges', 'bio', 'followers', 'following', 'last_username_update_timestamp',
  'x_username', 'wallet_label', 'is_pump_user', 'is_banned',
  'canonical_svm_wallet', 'canonical_evm_wallet', 'last_active_at',
]);

const GROUP_BADGE_REQUIRED_KEYS = ['group_id', 'username', 'profile_image_url', 'role'] as const;
const GROUP_BADGE_ALLOWED_KEYS = new Set(['group_id', 'username', 'profile_image_url', 'role']);

/** Assert that a user object conforms to the contract schema. */
function assertUserSchema(user: Record<string, unknown>, label = ''): void {
  const prefix = label ? `${label}: ` : '';
  // Required keys
  for (const key of USER_REQUIRED_KEYS) {
    assert.ok(key in user, `${prefix}missing required key "${key}"`);
  }
  // No extra keys
  for (const key of Object.keys(user)) {
    assert.ok(USER_ALLOWED_KEYS.has(key), `${prefix}unexpected key "${key}"`);
  }
  // Type checks for required fields
  assert.equal(typeof user.address, 'string', `${prefix}address should be string`);
  assert.ok(user.username === null || typeof user.username === 'string', `${prefix}username should be string|null`);
  assert.ok(user.profile_image === null || typeof user.profile_image === 'string', `${prefix}profile_image should be string|null`);
  assert.ok(user.bio === null || typeof user.bio === 'string', `${prefix}bio should be string|null`);
  assert.equal(typeof user.followers, 'number', `${prefix}followers should be number`);
  assert.equal(typeof user.following, 'number', `${prefix}following should be number`);
  assert.ok(user.x_username === null || typeof user.x_username === 'string', `${prefix}x_username should be string|null`);

  // Validate group_badges if present
  if ('group_badges' in user && Array.isArray(user.group_badges)) {
    for (const badge of user.group_badges as Record<string, unknown>[]) {
      for (const key of GROUP_BADGE_REQUIRED_KEYS) {
        assert.ok(key in badge, `${prefix}group_badge missing required key "${key}"`);
      }
      for (const key of Object.keys(badge)) {
        assert.ok(GROUP_BADGE_ALLOWED_KEYS.has(key), `${prefix}group_badge unexpected key "${key}"`);
      }
    }
  }
}

const OVERVIEW_REQUIRED_KEYS = [
  'address',
  'profile',
  'isPumpUser',
  'counts',
  'verified',
  'achievementBadgeIds',
  'banned',
  'createdCoinsCount',
  'degraded',
] as const;

const OVERVIEW_ALLOWED_KEYS = new Set([
  'address',
  'profile',
  'isPumpUser',
  'counts',
  'verified',
  'achievementBadgeIds',
  'banned',
  'createdCoinsCount',
  'viewer',
  'degraded',
]);

const DEGRADED_ENUM = new Set([
  'counts',
  'verified',
  'badges',
  'banned',
  'created_coins',
  'follows',
  'follows_you',
  'dm_eligible',
  'mutuals',
]);

/** Assert that an overview object conforms to the contract schema. */
function assertOverviewSchema(overview: Record<string, unknown>, label = ''): void {
  const prefix = label ? `${label}: ` : '';
  for (const key of OVERVIEW_REQUIRED_KEYS) {
    assert.ok(key in overview, `${prefix}missing required key "${key}"`);
  }
  for (const key of Object.keys(overview)) {
    assert.ok(OVERVIEW_ALLOWED_KEYS.has(key), `${prefix}unexpected key "${key}"`);
  }
  assert.equal(typeof overview.address, 'string', `${prefix}address should be string`);
  assert.equal(typeof overview.isPumpUser, 'boolean', `${prefix}isPumpUser should be boolean`);

  // profile
  assert.ok(overview.profile !== null && typeof overview.profile === 'object', `${prefix}profile should be an object`);
  assertUserSchema(overview.profile as Record<string, unknown>, `${prefix}profile`);

  // counts
  assert.ok(overview.counts !== null && typeof overview.counts === 'object', `${prefix}counts should be an object`);
  const counts = overview.counts as Record<string, unknown>;
  assert.ok('followers' in counts, `${prefix}counts missing followers`);
  assert.ok('following' in counts, `${prefix}counts missing following`);
  for (const k of Object.keys(counts)) {
    assert.ok(k === 'followers' || k === 'following', `${prefix}unexpected key in counts "${k}"`);
  }
  assert.ok(counts.followers === null || typeof counts.followers === 'number', `${prefix}followers should be number|null`);
  assert.ok(counts.following === null || typeof counts.following === 'number', `${prefix}following should be number|null`);

  // verified
  assert.ok(overview.verified === null || typeof overview.verified === 'boolean', `${prefix}verified should be boolean|null`);

  // achievementBadgeIds
  assert.ok(overview.achievementBadgeIds === null || Array.isArray(overview.achievementBadgeIds), `${prefix}achievementBadgeIds should be array|null`);
  if (Array.isArray(overview.achievementBadgeIds)) {
    for (const id of overview.achievementBadgeIds) {
      assert.equal(typeof id, 'string', `${prefix}achievementBadgeId should be string`);
    }
  }

  // banned
  assert.ok(overview.banned === null || typeof overview.banned === 'boolean', `${prefix}banned should be boolean|null`);

  // createdCoinsCount
  assert.ok(overview.createdCoinsCount === null || typeof overview.createdCoinsCount === 'number', `${prefix}createdCoinsCount should be number|null`);

  // degraded
  assert.ok(Array.isArray(overview.degraded), `${prefix}degraded should be array`);
  for (const item of overview.degraded as string[]) {
    assert.ok(DEGRADED_ENUM.has(item), `${prefix}invalid degraded item "${item}"`);
  }
}

/** Assert that a verified response conforms to the contract schema. */
function assertVerifiedResponseSchema(body: Record<string, unknown>, requestedIds: string[], label = ''): void {
  const prefix = label ? `${label}: ` : '';
  assert.ok(body !== null && typeof body === 'object' && !Array.isArray(body), `${prefix}should be an object`);
  for (const id of requestedIds) {
    assert.ok(id in body, `${prefix}missing requested id "${id}" in response`);
    assert.equal(typeof body[id], 'boolean', `${prefix}value for id "${id}" should be boolean`);
  }
  for (const [key, val] of Object.entries(body)) {
    assert.equal(typeof val, 'boolean', `${prefix}key "${key}" value should be boolean`);
  }
}

/** Build a test app with a known seed. */
function buildTestApp() {
  const seed: User[] = [
    {
      address: 'AAA111',
      userId: 'uid-a',
      username: 'alice',
      profile_image: 'https://img/a.png',
      bio: 'Hello from Alice',
      followers: 100,
      following: 50,
      x_username: 'alice_x',
      wallet_label: '',
    },
    {
      address: 'BBB222',
      userId: 'uid-b',
      username: 'bob',
      profile_image: null,
      bio: null,
      followers: 200,
      following: 10,
      x_username: null,
      wallet_label: '',
    },
    {
      address: 'CCC333',
      userId: 'uid-c',
      username: null,
      profile_image: null,
      bio: null,
      followers: 50,
      following: 5,
      x_username: null,
      wallet_label: 'labeled-vault',
    },
    {
      address: 'DDD444',
      userId: 'uid-d',
      username: 'dave',
      profile_image: 'https://img/d.png',
      bio: 'Dave here',
      followers: 300,
      following: 30,
      x_username: 'dave_x',
      wallet_label: '',
    },
  ];
  const store = new UserStore(seed, ['AAA111', 'uid-a']);
  const app = buildApp([], { userStore: store });
  return { app, store, seed };
}

/*──────────────────────────────────────────────────────────────
 * GET /v1/users
 *────────────────────────────────────────────────────────────*/
describe('GET /v1/users', () => {
  test('returns 200 with array of users conforming to schema', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>[];
      assert.ok(Array.isArray(body));
      assert.equal(body.length, 4);
      for (const user of body) {
        assertUserSchema(user);
      }
    } finally {
      await app.close();
    }
  });

  test('pagination with offset and limit', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users?offset=1&limit=2');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>[];
      assert.equal(body.length, 2);
      // Default insertion order: alice(0), bob(1), anon(2), dave(3)
      assert.equal(body[0].address, 'BBB222');
      assert.equal(body[1].address, 'CCC333');
    } finally {
      await app.close();
    }
  });

  test('offset past end returns empty array', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users?offset=100');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>[];
      assert.equal(body.length, 0);
    } finally {
      await app.close();
    }
  });

  test('negative offset clamps to 0 (documented assumption)', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users?offset=-2&limit=2');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>[];
      assert.equal(body.length, 2);
      assert.equal(body[0].address, 'AAA111');
    } finally {
      await app.close();
    }
  });

  test('negative limit returns empty array (documented assumption)', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users?limit=-5');
      assert.equal(r.statusCode, 200);
      assert.equal((r.json() as unknown[]).length, 0);
    } finally {
      await app.close();
    }
  });

  test('sort=followers&order=desc sorts descending', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users?sort=followers&order=desc');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>[];
      assert.equal(body.length, 4);
      assert.equal(body[0].address, 'DDD444'); // 300
      assert.equal(body[1].address, 'BBB222'); // 200
      assert.equal(body[2].address, 'AAA111'); // 100
      assert.equal(body[3].address, 'CCC333'); // 50
    } finally {
      await app.close();
    }
  });

  test('sort=followers&order=asc sorts ascending', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users?sort=followers&order=asc');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>[];
      assert.equal(body[0].address, 'CCC333'); // 50
      assert.equal(body[3].address, 'DDD444'); // 300
    } finally {
      await app.close();
    }
  });

  test('sort=username nulls sort last', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users?sort=username&order=asc');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>[];
      // alice, bob, dave come first in alpha order; null-username last
      assert.equal(body[0].username, 'alice');
      assert.equal(body[1].username, 'bob');
      assert.equal(body[2].username, 'dave');
      assert.equal(body[3].username, null);
    } finally {
      await app.close();
    }
  });

  test('sort+order combined with pagination', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users?sort=followers&order=desc&offset=1&limit=2');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>[];
      assert.equal(body.length, 2);
      assert.equal(body[0].address, 'BBB222'); // 200
      assert.equal(body[1].address, 'AAA111'); // 100
    } finally {
      await app.close();
    }
  });

  test('unrecognized sort key falls back to insertion order', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users?sort=nonexistent');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>[];
      assert.equal(body[0].address, 'AAA111');
      assert.equal(body[3].address, 'DDD444');
    } finally {
      await app.close();
    }
  });
});

/*──────────────────────────────────────────────────────────────
 * GET /v1/users/:id
 *────────────────────────────────────────────────────────────*/
describe('GET /v1/users/:id', () => {
  test('lookup by wallet address returns 200 with conforming schema', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users/AAA111');
      assert.equal(r.statusCode, 200);
      const user = r.json() as Record<string, unknown>;
      assertUserSchema(user, 'by-address');
      assert.equal(user.address, 'AAA111');
      assert.equal(user.username, 'alice');
    } finally {
      await app.close();
    }
  });

  test('lookup by userId returns 200 with conforming schema', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users/uid-b');
      assert.equal(r.statusCode, 200);
      const user = r.json() as Record<string, unknown>;
      assertUserSchema(user, 'by-userId');
      assert.equal(user.address, 'BBB222');
    } finally {
      await app.close();
    }
  });

  test('lookup miss returns 404', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users/NONEXISTENT');
      assert.equal(r.statusCode, 404);
      assert.equal(r.json().error, 'NOT_FOUND');
      assert.equal(r.json().statusCode, 404);
    } finally {
      await app.close();
    }
  });
});

/*──────────────────────────────────────────────────────────────
 * POST /v1/users/batch
 *────────────────────────────────────────────────────────────*/
describe('POST /v1/users/batch', () => {
  test('returns 201 with matching users', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject({
        method: 'POST',
        url: '/v1/users/batch',
        payload: { addresses: ['AAA111', 'CCC333'] },
      });
      assert.equal(r.statusCode, 201);
      const body = r.json() as Record<string, unknown>[];
      assert.ok(Array.isArray(body));
      assert.equal(body.length, 2);
      for (const user of body) {
        assertUserSchema(user, 'batch');
      }
      assert.equal(body[0].address, 'AAA111');
      assert.equal(body[1].address, 'CCC333');
    } finally {
      await app.close();
    }
  });

  test('missing addresses are omitted from response', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject({
        method: 'POST',
        url: '/v1/users/batch',
        payload: { addresses: ['AAA111', 'MISSING', 'BBB222'] },
      });
      assert.equal(r.statusCode, 201);
      const body = r.json() as Record<string, unknown>[];
      assert.equal(body.length, 2);
      assert.equal(body[0].address, 'AAA111');
      assert.equal(body[1].address, 'BBB222');
    } finally {
      await app.close();
    }
  });

  test('empty addresses returns empty array', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject({
        method: 'POST',
        url: '/v1/users/batch',
        payload: { addresses: [] },
      });
      assert.equal(r.statusCode, 201);
      const body = r.json() as Record<string, unknown>[];
      assert.equal(body.length, 0);
    } finally {
      await app.close();
    }
  });

  test('missing addresses field returns 400', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject({
        method: 'POST',
        url: '/v1/users/batch',
        payload: {},
      });
      assert.equal(r.statusCode, 400);
    } finally {
      await app.close();
    }
  });

  test('more than 100 addresses returns 400 (contract maxItems)', async () => {
    const { app } = buildTestApp();
    try {
      const addresses = Array.from({ length: 101 }, (_, i) => `ADDR${i}`);
      const r = await app.inject({
        method: 'POST',
        url: '/v1/users/batch',
        payload: { addresses },
      });
      assert.equal(r.statusCode, 400);
      const body = r.json() as Record<string, unknown>;
      assert.equal(body.error, 'TOO_MANY_ADDRESSES');
    } finally {
      await app.close();
    }
  });

  test('exactly 100 addresses is accepted', async () => {
    const { app } = buildTestApp();
    try {
      const addresses = Array.from({ length: 100 }, (_, i) => `ADDR${i}`);
      const r = await app.inject({
        method: 'POST',
        url: '/v1/users/batch',
        payload: { addresses },
      });
      assert.equal(r.statusCode, 201);
    } finally {
      await app.close();
    }
  });

  test('forceFetch is accepted and ignored', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject({
        method: 'POST',
        url: '/v1/users/batch',
        payload: { addresses: ['AAA111'], forceFetch: true },
      });
      assert.equal(r.statusCode, 201);
      const body = r.json() as Record<string, unknown>[];
      assert.equal(body.length, 1);
    } finally {
      await app.close();
    }
  });
});

/*──────────────────────────────────────────────────────────────
 * GET /v1/users/username-exists/:username
 *────────────────────────────────────────────────────────────*/
describe('GET /v1/users/username-exists/:username', () => {
  test('existing username returns { exists_flag: true }', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users/username-exists/alice');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>;
      assert.equal(body.exists_flag, true);
      // Schema conformance: only exists_flag, additionalProperties: false
      assert.deepEqual(Object.keys(body), ['exists_flag']);
    } finally {
      await app.close();
    }
  });

  test('non-existing username returns { exists_flag: false }', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users/username-exists/nobody_here');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>;
      assert.equal(body.exists_flag, false);
    } finally {
      await app.close();
    }
  });

  test('case-insensitive username check', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users/username-exists/ALICE');
      assert.equal(r.statusCode, 200);
      assert.equal(r.json().exists_flag, true);
    } finally {
      await app.close();
    }
  });
});

/*──────────────────────────────────────────────────────────────
 * Regression: existing behavior preserved
 *────────────────────────────────────────────────────────────*/
describe('regression: existing behavior', () => {
  test('unknown route returns 501 COMPATIBILITY_NOT_IMPLEMENTED', async () => {
    const app = buildApp();
    try {
      const r = await app.inject('/v1/some/unknown/route');
      assert.equal(r.statusCode, 501);
      assert.equal(r.json().error, 'COMPATIBILITY_NOT_IMPLEMENTED');
    } finally {
      await app.close();
    }
  });

  test('/health returns ok', async () => {
    const app = buildApp();
    try {
      const r = await app.inject('/health');
      assert.equal(r.statusCode, 200);
      assert.equal(r.json().status, 'ok');
    } finally {
      await app.close();
    }
  });

  test('/__reconstruction/openapi.json serves the spec', async () => {
    const app = buildApp();
    try {
      const r = await app.inject('/__reconstruction/openapi.json');
      assert.equal(r.statusCode, 200);
      assert.ok(r.headers['content-type']?.toString().includes('application/json'));
      const body = r.json();
      assert.equal(body.openapi, '3.0.0');
    } finally {
      await app.close();
    }
  });

  test('/__reconstruction/status returns fixture count and spec hash', async () => {
    const app = buildApp();
    try {
      const r = await app.inject('/__reconstruction/status');
      assert.equal(r.statusCode, 200);
      const body = r.json();
      assert.equal(typeof body.fixtureCount, 'number');
      assert.equal(typeof body.specificationSha256, 'string');
    } finally {
      await app.close();
    }
  });

  test('fixture replay still works for non-user routes', async () => {
    const app = buildApp([
      { method: 'GET', path: '/v1/coins', query: { limit: '1' }, status: 200, body: [{ mint: 'test' }], source: 'test' },
    ]);
    try {
      const r = await app.inject('/v1/coins?limit=1');
      assert.equal(r.statusCode, 200);
      assert.deepEqual(r.json(), [{ mint: 'test' }]);
    } finally {
      await app.close();
    }
  });
});

/*──────────────────────────────────────────────────────────────
 * Schema conformance on the default seed store
 *────────────────────────────────────────────────────────────*/
describe('schema conformance with default seed', () => {
  test('GET /v1/users returns all seed users with valid schema', async () => {
    const app = buildApp();
    try {
      const r = await app.inject('/v1/users');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>[];
      assert.ok(body.length >= 1, 'at least one user in seed');
      for (const user of body) {
        assertUserSchema(user, 'default-seed');
      }
    } finally {
      await app.close();
    }
  });

  test('GET /v1/users/:id with first seed address', async () => {
    const app = buildApp();
    try {
      // First, get the list to know an address
      const list = (await app.inject('/v1/users')).json() as Record<string, unknown>[];
      const addr = list[0].address as string;
      const r = await app.inject(`/v1/users/${addr}`);
      assert.equal(r.statusCode, 200);
      assertUserSchema(r.json(), 'default-seed-single');
    } finally {
      await app.close();
    }
  });

  test('POST /v1/users/batch with default seed addresses', async () => {
    const app = buildApp();
    try {
      const list = (await app.inject('/v1/users')).json() as Record<string, unknown>[];
      const addresses = list.map(u => u.address as string);
      const r = await app.inject({
        method: 'POST',
        url: '/v1/users/batch',
        payload: { addresses },
      });
      assert.equal(r.statusCode, 201);
      const body = r.json() as Record<string, unknown>[];
      assert.equal(body.length, addresses.length);
      for (const user of body) {
        assertUserSchema(user, 'default-seed-batch');
      }
    } finally {
      await app.close();
    }
  });

  test('GET /v1/users/search-v2 returns default seed users conforming to schema', async () => {
    const app = buildApp();
    try {
      const r = await app.inject('/v1/users/search-v2?includeLabelledWallets=true');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>[];
      assert.ok(body.length >= 1, 'at least one user in seed');
      for (const user of body) {
        assertUserSchema(user, 'default-seed-search');
      }
    } finally {
      await app.close();
    }
  });

  test('GET /v1/users/:id/overview with first seed address returns conforming schema', async () => {
    const app = buildApp();
    try {
      const list = (await app.inject('/v1/users')).json() as Record<string, unknown>[];
      const addr = list[0].address as string;
      const r = await app.inject(`/v1/users/${addr}/overview`);
      assert.equal(r.statusCode, 200);
      assertOverviewSchema(r.json(), 'default-seed-overview');
    } finally {
      await app.close();
    }
  });

  test('POST /v1/profiles/verified with default seed addresses', async () => {
    const app = buildApp();
    try {
      const list = (await app.inject('/v1/users')).json() as Record<string, unknown>[];
      const addresses = list.map(u => u.address as string);
      const r = await app.inject({
        method: 'POST',
        url: '/v1/profiles/verified',
        payload: { ids: addresses },
      });
      assert.equal(r.statusCode, 201);
      const body = r.json() as Record<string, unknown>;
      assertVerifiedResponseSchema(body, addresses, 'default-seed-verified');
      // Alice is first seed user, verified=true
      assert.equal(body[addresses[0]], true);
    } finally {
      await app.close();
    }
  });
});

/*──────────────────────────────────────────────────────────────
 * GET /v1/users/search-v2
 *────────────────────────────────────────────────────────────*/
describe('GET /v1/users/search-v2', () => {
  test('returns 200 with matching users conforming to schema', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users/search-v2');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>[];
      assert.ok(Array.isArray(body));
      // CCC333 has wallet_label so excluded by default (includeLabelledWallets: false)
      assert.equal(body.length, 3);
      for (const user of body) {
        assertUserSchema(user, 'search-v2');
      }
      assert.equal(body[0].address, 'AAA111');
      assert.equal(body[1].address, 'BBB222');
      assert.equal(body[2].address, 'DDD444');
    } finally {
      await app.close();
    }
  });

  test('searchTerm filter matches username (case-insensitive)', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users/search-v2?searchTerm=ALICE');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>[];
      assert.equal(body.length, 1);
      assert.equal(body[0].username, 'alice');
      assertUserSchema(body[0]);
    } finally {
      await app.close();
    }
  });

  test('searchTerm filter matches address', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users/search-v2?searchTerm=BBB222');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>[];
      assert.equal(body.length, 1);
      assert.equal(body[0].address, 'BBB222');
    } finally {
      await app.close();
    }
  });

  test('searchTerm filter matches userId', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users/search-v2?searchTerm=uid-d');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>[];
      assert.equal(body.length, 1);
      assert.equal(body[0].address, 'DDD444');
    } finally {
      await app.close();
    }
  });

  test('searchTerm filter matches x_username', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users/search-v2?searchTerm=alice_x');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>[];
      assert.equal(body.length, 1);
      assert.equal(body[0].address, 'AAA111');
    } finally {
      await app.close();
    }
  });

  test('empty searchTerm returns all non-labelled users', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users/search-v2?searchTerm=');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>[];
      assert.equal(body.length, 3);
    } finally {
      await app.close();
    }
  });

  test('includeLabelledWallets=true includes labelled wallets', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users/search-v2?includeLabelledWallets=true');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>[];
      assert.equal(body.length, 4);
      assert.ok(body.some(u => u.address === 'CCC333'));
      for (const user of body) {
        assertUserSchema(user);
      }
    } finally {
      await app.close();
    }
  });

  test('includeLabelledWallets=false excludes labelled wallets', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users/search-v2?includeLabelledWallets=false');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>[];
      assert.equal(body.length, 3);
      assert.ok(!body.some(u => u.address === 'CCC333'));
    } finally {
      await app.close();
    }
  });

  test('pagination with offset and limit', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users/search-v2?includeLabelledWallets=true&offset=1&limit=2');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>[];
      assert.equal(body.length, 2);
      assert.equal(body[0].address, 'BBB222');
      assert.equal(body[1].address, 'CCC333');
    } finally {
      await app.close();
    }
  });

  test('offset past end returns empty array', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users/search-v2?offset=100');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>[];
      assert.equal(body.length, 0);
    } finally {
      await app.close();
    }
  });

  test('negative offset clamps to 0 (documented assumption)', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users/search-v2?offset=-5&limit=2');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>[];
      assert.equal(body.length, 2);
      assert.equal(body[0].address, 'AAA111');
    } finally {
      await app.close();
    }
  });

  test('negative limit returns empty array (documented assumption)', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users/search-v2?limit=-3');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>[];
      assert.equal(body.length, 0);
    } finally {
      await app.close();
    }
  });

  test('sorting with followers desc', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users/search-v2?includeLabelledWallets=true&sort=followers&order=desc');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>[];
      assert.equal(body.length, 4);
      assert.equal(body[0].address, 'DDD444'); // 300
      assert.equal(body[1].address, 'BBB222'); // 200
      assert.equal(body[2].address, 'AAA111'); // 100
      assert.equal(body[3].address, 'CCC333'); // 50
    } finally {
      await app.close();
    }
  });

  test('route ordering: search-v2 does not get captured by /v1/users/:id', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users/search-v2');
      assert.equal(r.statusCode, 200);
      const body = r.json();
      assert.ok(Array.isArray(body), 'response must be an array, not an object or 404');
    } finally {
      await app.close();
    }
  });
});

/*──────────────────────────────────────────────────────────────
 * GET /v1/users/:id/overview
 *────────────────────────────────────────────────────────────*/
describe('GET /v1/users/:id/overview', () => {
  for (const flag of [undefined, false, true]) {
    test(`profile presence determines isPumpUser when the row flag is ${String(flag)}`, async () => {
      const user: User = {
        address: 'labelled-wallet', userId: 'labelled-user', username: null,
        profile_image: null, bio: null, followers: 0, following: 0, x_username: null,
        wallet_label: 'Synthetic labelled wallet',
        ...(flag === undefined ? {} : { is_pump_user: flag }),
      };
      const store = new UserStore([user]);
      const app = buildApp([], { userStore: store });
      try {
        for (const id of [user.address, user.userId!]) {
          const response = await app.inject(`/v1/users/${id}/overview`);
          assert.equal(response.statusCode, 200);
          const body = response.json();
          assertOverviewSchema(body);
          assert.deepEqual(body.profile, user);
          assert.equal(body.isPumpUser, body.profile !== null);
        }
        // The aggregate's presence flag does not rewrite the stored/raw profile field.
        assert.deepEqual(store.getById(user.address), user);
        assert.deepEqual((await app.inject(`/v1/users/${user.address}`)).json(), user);
      } finally { await app.close(); }
    });
  }

  test('lookup by wallet address returns 200 with conforming schema', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users/AAA111/overview');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>;
      assertOverviewSchema(body, 'by-address-overview');
      assert.equal(body.address, 'AAA111');
      assert.equal(body.verified, true);
      assert.equal(body.isPumpUser, true);
      assert.deepEqual(body.counts, { followers: 100, following: 50 });
      assert.deepEqual(body.achievementBadgeIds, []);
      assert.equal(body.banned, false);
      assert.equal(body.createdCoinsCount, 0);
      assert.deepEqual(body.degraded, []);
      const profile = body.profile as Record<string, unknown>;
      assert.equal(profile.address, 'AAA111');
      assert.equal(profile.username, 'alice');
    } finally {
      await app.close();
    }
  });

  test('lookup by userId returns 200 with conforming schema', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users/uid-b/overview');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>;
      assertOverviewSchema(body, 'by-userId-overview');
      assert.equal(body.address, 'uid-b'); // id as sent
      assert.equal(body.verified, false);
      const profile = body.profile as Record<string, unknown>;
      assert.equal(profile.address, 'BBB222');
      assert.equal(profile.username, 'bob');
    } finally {
      await app.close();
    }
  });

  test('lookup miss returns 404 NOT_FOUND', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users/NONEXISTENT/overview');
      assert.equal(r.statusCode, 404);
      assert.deepEqual(r.json(), { statusCode: 404, error: 'NOT_FOUND' });
    } finally {
      await app.close();
    }
  });

  test('overview does not get captured by /v1/users/:id', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject('/v1/users/AAA111/overview');
      assert.equal(r.statusCode, 200);
      const body = r.json() as Record<string, unknown>;
      assert.ok('profile' in body, 'must be overview object containing profile');
    } finally {
      await app.close();
    }
  });
});

/*──────────────────────────────────────────────────────────────
 * POST /v1/profiles/verified
 *────────────────────────────────────────────────────────────*/
describe('POST /v1/profiles/verified', () => {
  test('returns 201 with verified status mapping', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject({
        method: 'POST',
        url: '/v1/profiles/verified',
        payload: { ids: ['AAA111', 'BBB222'] },
      });
      assert.equal(r.statusCode, 201);
      const body = r.json() as Record<string, unknown>;
      assertVerifiedResponseSchema(body, ['AAA111', 'BBB222']);
      assert.equal(body['AAA111'], true);
      assert.equal(body['BBB222'], false);
    } finally {
      await app.close();
    }
  });

  test('lookup by userId maps to verified status', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject({
        method: 'POST',
        url: '/v1/profiles/verified',
        payload: { ids: ['uid-a', 'uid-b'] },
      });
      assert.equal(r.statusCode, 201);
      const body = r.json() as Record<string, unknown>;
      assertVerifiedResponseSchema(body, ['uid-a', 'uid-b']);
      assert.equal(body['uid-a'], true);
      assert.equal(body['uid-b'], false);
    } finally {
      await app.close();
    }
  });

  test('id with no user maps to false', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject({
        method: 'POST',
        url: '/v1/profiles/verified',
        payload: { ids: ['NONEXISTENT_USER'] },
      });
      assert.equal(r.statusCode, 201);
      const body = r.json() as Record<string, unknown>;
      assertVerifiedResponseSchema(body, ['NONEXISTENT_USER']);
      assert.equal(body['NONEXISTENT_USER'], false);
    } finally {
      await app.close();
    }
  });

  test('mixed batch with verified, unverified, and unknown ids', async () => {
    const { app } = buildTestApp();
    try {
      const ids = ['AAA111', 'BBB222', 'UNKNOWN_USER'];
      const r = await app.inject({
        method: 'POST',
        url: '/v1/profiles/verified',
        payload: { ids },
      });
      assert.equal(r.statusCode, 201);
      const body = r.json() as Record<string, unknown>;
      assertVerifiedResponseSchema(body, ids);
      assert.equal(body['AAA111'], true);
      assert.equal(body['BBB222'], false);
      assert.equal(body['UNKNOWN_USER'], false);
    } finally {
      await app.close();
    }
  });

  test('duplicate ids in request body map correctly', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject({
        method: 'POST',
        url: '/v1/profiles/verified',
        payload: { ids: ['AAA111', 'AAA111'] },
      });
      assert.equal(r.statusCode, 201);
      const body = r.json() as Record<string, unknown>;
      assertVerifiedResponseSchema(body, ['AAA111']);
      assert.equal(body['AAA111'], true);
    } finally {
      await app.close();
    }
  });

  test('validation error: missing body returns 400', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject({
        method: 'POST',
        url: '/v1/profiles/verified',
        payload: {},
      });
      assert.equal(r.statusCode, 400);
      assert.equal(r.json().error, 'IDS_REQUIRED');
      assert.equal(r.json().statusCode, 400);
    } finally {
      await app.close();
    }
  });

  test('validation error: empty ids array returns 400 (minItems: 1)', async () => {
    const { app } = buildTestApp();
    try {
      const r = await app.inject({
        method: 'POST',
        url: '/v1/profiles/verified',
        payload: { ids: [] },
      });
      assert.equal(r.statusCode, 400);
      const body = r.json() as Record<string, unknown>;
      assert.equal(body.error, 'EMPTY_IDS');
      assert.equal(body.minItems, 1);
    } finally {
      await app.close();
    }
  });

  test('validation error: 201 ids returns 400 (maxItems: 200)', async () => {
    const { app } = buildTestApp();
    try {
      const ids = Array.from({ length: 201 }, (_, i) => `id-${i}`);
      const r = await app.inject({
        method: 'POST',
        url: '/v1/profiles/verified',
        payload: { ids },
      });
      assert.equal(r.statusCode, 400);
      const body = r.json() as Record<string, unknown>;
      assert.equal(body.error, 'TOO_MANY_IDS');
      assert.equal(body.maxItems, 200);
    } finally {
      await app.close();
    }
  });

  test('validation error: an id longer than 64 characters returns 400 (maxLength: 64)', async () => {
    const { app } = buildTestApp();
    try {
      const ids = ['AAA111', 'a'.repeat(65)];
      const r = await app.inject({
        method: 'POST',
        url: '/v1/profiles/verified',
        payload: { ids },
      });
      assert.equal(r.statusCode, 400);
      const body = r.json() as Record<string, unknown>;
      assert.equal(body.error, 'INVALID_ID');
      assert.equal(body.maxLength, 64);
    } finally {
      await app.close();
    }
  });

  test('boundary: exactly 200 ids is accepted', async () => {
    const { app } = buildTestApp();
    try {
      const ids = Array.from({ length: 200 }, (_, i) => `id-${i}`);
      const r = await app.inject({
        method: 'POST',
        url: '/v1/profiles/verified',
        payload: { ids },
      });
      assert.equal(r.statusCode, 201);
      const body = r.json() as Record<string, unknown>;
      assert.equal(Object.keys(body).length, 200);
    } finally {
      await app.close();
    }
  });

  test('boundary: id of exactly 64 characters is accepted', async () => {
    const { app } = buildTestApp();
    try {
      const ids = ['a'.repeat(64)];
      const r = await app.inject({
        method: 'POST',
        url: '/v1/profiles/verified',
        payload: { ids },
      });
      assert.equal(r.statusCode, 201);
      const body = r.json() as Record<string, unknown>;
      assert.equal(body['a'.repeat(64)], false);
    } finally {
      await app.close();
    }
  });
});
