export const PROCESS = { P1: 'Licence application', P2: 'Licence variation', P3: 'Pollution incident' };
export const STATES = {
  SUBMITTED: 'Submitted', AWAITING_INFORMATION: 'Information needed', ASSESSMENT: 'Under assessment',
  APPROVED: 'Approved', REFUSED: 'Refused', INCOMPLETE_CLOSED: 'Closed · incomplete', INVALID: 'Ineligible',
  INVESTIGATION: 'Under investigation', EMERGENCY_GUIDANCE: 'Emergency guidance', REFERRED: 'Referred',
  ACTION_RECORDED: 'Action recorded', NO_FURTHER_ACTION: 'No further action',
};
export const FINAL_STATES = new Set(['APPROVED', 'REFUSED', 'INCOMPLETE_CLOSED', 'INVALID', 'EMERGENCY_GUIDANCE', 'REFERRED', 'ACTION_RECORDED', 'NO_FURTHER_ACTION']);
export const lines = (value) => value.split(/\r?\n/).map((s) => s.trim()).filter(Boolean);
export const titleFor = (item) => item.data.applicant || item.data.location || item.data.licence_id;
export function displayDate(value) {
  if (!value) return '—';
  return new Intl.DateTimeFormat('en-AU', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));
}
export function duration(milliseconds) {
  if (milliseconds == null) return '—';
  if (milliseconds < 60000) return `${Math.round(milliseconds / 1000)} sec`;
  if (milliseconds < 3600000) return `${(milliseconds / 60000).toFixed(1)} min`;
  return `${(milliseconds / 3600000).toFixed(1)} hr`;
}
export function analyse(events, cases) {
  const traces = new Map();
  for (const event of events) {
    const trace = traces.get(event.case_id) || [];
    trace.push(event); traces.set(event.case_id, trace);
  }
  const processes = Object.keys(PROCESS).map((process) => {
    const selected = cases.filter((item) => item.process === process);
    const completed = selected.filter((item) => FINAL_STATES.has(item.state));
    const durations = completed.map((item) => {
      const trace = traces.get(item.id) || [];
      const stamps = trace.map((e) => Date.parse(e.timestamp)).filter(Number.isFinite);
      return stamps.length ? Math.max(...stamps) - Math.min(...stamps) : null;
    }).filter((value) => value !== null);
    return { process, cases: selected.length, completed: completed.length,
      mean: durations.length ? durations.reduce((a, b) => a + b, 0) / durations.length : null };
  });
  const variants = new Map();
  for (const trace of traces.values()) {
    trace.sort((a, b) => a.seq - b.seq);
    const process = trace[0].process;
    const path = trace.map((event) => event.task_id).join(' → ');
    const key = `${process}:${path}`;
    const old = variants.get(key) || { process, path, count: 0 };
    old.count += 1; variants.set(key, old);
  }
  return { processes, variants: [...variants.values()].sort((a, b) => b.count - a.count), eventCount: events.length };
}
