import { useEffect, useRef, useState, useCallback } from 'react';

// Callers memoise the loader; abort protects against old requests and profile switches.
export function useLoad(loader) {
  const [version, setVersion] = useState(0);
  const [state, setState] = useState({ data: null, loading: true, error: null });
  useEffect(() => {
    const controller = new AbortController();
    setState({ data: null, loading: true, error: null });
    Promise.resolve().then(() => loader(controller.signal)).then(
      (data) => { if (!controller.signal.aborted) setState({ data, loading: false, error: null }); },
      (error) => { if (!controller.signal.aborted) setState({ data: null, loading: false, error }); },
    );
    return () => controller.abort();
  }, [loader, version]);
  const reload = useCallback(() => setVersion((v) => v + 1), []);
  return { ...state, reload };
}
export function useSubmission() {
  const pending = useRef(false);
  const identity = useRef(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const submit = async (payload, callback) => {
    if (pending.current) return;
    pending.current = true; setBusy(true); setError(null);
    const fingerprint = JSON.stringify(payload);
    if (identity.current?.fingerprint !== fingerprint) identity.current = { fingerprint, key: crypto.randomUUID() };
    try { await callback(identity.current.key); }
    catch (cause) { setError(cause); }
    finally { pending.current = false; setBusy(false); }
  };
  return { submit, busy, error };
}
