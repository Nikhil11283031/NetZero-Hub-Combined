import test from 'node:test';
import assert from 'node:assert/strict';
import { analyse, lines, duration } from '../../src/features/epa/model.js';

test('elapsed mean includes completed cases only; unfinished variants are retained', () => {
  const events = [
    { case_id: 'a', process: 'P1', seq: 1, task_id: 'A1', timestamp: '2026-01-01T00:00:00Z' },
    { case_id: 'a', process: 'P1', seq: 2, task_id: 'A11', timestamp: '2026-01-01T00:02:00Z' },
    { case_id: 'b', process: 'P1', seq: 3, task_id: 'A1', timestamp: '2026-01-01T00:00:00Z' },
    { case_id: 'b', process: 'P1', seq: 4, task_id: 'A2', timestamp: '2026-01-02T00:00:00Z' },
  ];
  const result = analyse(events, [{ id: 'a', process: 'P1', state: 'APPROVED' }, { id: 'b', process: 'P1', state: 'ASSESSMENT' }]);
  assert.equal(result.processes[0].mean, 120000);
  assert.equal(result.processes[0].completed, 1);
  assert.equal(result.variants.length, 2);
  assert.equal(result.processes[1].mean, null);
});
test('references handle Windows newlines and discard blank lines', () => assert.deepEqual(lines(' plan.pdf\r\n\r\n consent.pdf '), ['plan.pdf', 'consent.pdf']));
test('time formatting distinguishes no data from a zero duration', () => { assert.equal(duration(null), '—'); assert.equal(duration(0), '0 sec'); });
