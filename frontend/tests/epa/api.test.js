import test from 'node:test';
import assert from 'node:assert/strict';
import { createApi, ApiError } from '../../src/features/epa/api.js';

test('creation sends identity, idempotency key and JSON to the configured service', async () => {
  let captured;
  const api = createApi({ token: 'test', licensingUrl: '/custom/licensing/', fetchImpl: async (...args) => { captured = args; return new Response('{"id":"a"}'); } });
  assert.deepEqual(await api.create('licensing', '/applications', { applicant: 'Demo' }, 'same-key'), { id: 'a' });
  assert.equal(captured[0], '/custom/licensing/applications');
  assert.equal(captured[1].headers.Authorization, 'Bearer test');
  assert.equal(captured[1].headers['Idempotency-Key'], 'same-key');
  assert.equal(captured[1].method, 'POST');
});
test('stale-version errors retain their status for recovery in the UI', async () => {
  const api = createApi({ token: 'test', fetchImpl: async () => new Response('{"detail":"Stale version; reload before retrying"}', { status: 409 }) });
  await assert.rejects(api.command('licensing', { id: 'a', version: 3 }, 'check', {}), (e) => e instanceof ApiError && e.status === 409 && /reload/.test(e.message));
});
test('validation errors explain the affected fields', async () => {
  const api = createApi({ token: 'test', fetchImpl: async () => new Response(JSON.stringify({ detail: [{ loc: ['body', 'documents', 0], msg: 'Too long' }] }), { status: 422 }) });
  await assert.rejects(api.cases('licensing'), /documents.0: Too long/);
});
test('a non-JSON proxy outage produces a readable error', async () => {
  const api = createApi({ token: 'test', fetchImpl: async () => new Response('Bad gateway', { status: 502 }) });
  await assert.rejects(api.cases('incidents'), (e) => e.status === 502 && /service/.test(e.message));
});
