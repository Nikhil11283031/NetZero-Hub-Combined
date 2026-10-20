export class ApiError extends Error {
  constructor(message, status = 0) { super(message); this.name = 'ApiError'; this.status = status; }
}

export function errorMessage(body, status) {
  const detail = body?.detail;
  if (Array.isArray(detail)) return detail.map((item) => `${(item.loc || []).filter((s) => s !== 'body').join('.')}: ${item.msg}`).join('; ');
  if (typeof detail === 'string') return detail;
  return `The service returned an error (${status}). Please try again.`;
}

export function createApi({ token, authScheme = 'Bearer', licensingUrl = '/api/v1/epa/licensing', incidentsUrl = '/api/v1/epa/incidents', fetchImpl = fetch }) {
  const bases = { licensing: licensingUrl.replace(/\/$/, ''), incidents: incidentsUrl.replace(/\/$/, '') };
  async function request(service, path, { method = 'GET', body, key, signal, raw = false } = {}) {
    if (!bases[service]) throw new ApiError('Unknown EPA service');
    const headers = { Accept: raw ? '*/*' : 'application/json', Authorization: `${authScheme} ${token}` };
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (key) headers['Idempotency-Key'] = key;
    let response;
    try {
      const timeout = AbortSignal.timeout(15000);
      response = await fetchImpl(bases[service] + path, { method, headers,
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: signal ? AbortSignal.any([signal, timeout]) : timeout });
    } catch (error) {
      if (signal?.aborted) throw error;
      throw new ApiError('Cannot reach the service. Check that both backends are running, then retry.');
    }
    if (!response.ok) {
      const data = await response.json().catch(() => null);
      throw new ApiError(errorMessage(data, response.status), response.status);
    }
    return raw ? response.blob() : response.json();
  }
  return {
    request,
    cases: (service, signal) => request(service, '/cases', { signal }),
    case: (service, id, signal) => request(service, `/cases/${encodeURIComponent(id)}`, { signal }),
    events: (service, id, signal) => request(service, id ? `/cases/${encodeURIComponent(id)}/events` : '/events', { signal }),
    licences: (signal) => request('licensing', '/licences', { signal }),
    create: (service, path, payload, key) => request(service, path, { method: 'POST', body: payload, key }),
    command: (service, item, action, values) => request(service, `/cases/${encodeURIComponent(item.id)}/commands`,
      { method: 'POST', body: { expected_version: item.version, action, values } }),
    export: (service, format) => request(service, `/events/export?format=${format}`, { raw: true }),
    async allCases(signal) {
      const lists = await Promise.all(['licensing', 'incidents'].map(async (service) =>
        (await request(service, '/cases', { signal })).map((item) => ({ ...item, service }))));
      return lists.flat().sort((a, b) => (b.updated_at || '').localeCompare(a.updated_at || ''));
    },
  };
}
