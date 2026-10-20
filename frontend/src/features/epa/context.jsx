import { createContext, useContext, useMemo } from 'react';
import { createApi } from './api.js';

const Context = createContext(null);
// The group portal supplies its authenticated profile and API URLs here.
// This provider does not create a router or implement a second login system.
export function EpaProvider({ profile, authScheme = 'Bearer', licensingUrl, incidentsUrl, basePath = '/epa', onSwitchProfile, children }) {
  const api = useMemo(() => createApi({ token: profile.token, authScheme, licensingUrl, incidentsUrl }), [profile.token, authScheme, licensingUrl, incidentsUrl]);
  const value = useMemo(() => ({ profile, api, basePath, onSwitchProfile }), [profile, api, basePath, onSwitchProfile]);
  return <Context.Provider value={value}>{children}</Context.Provider>;
}
export function useEpa() {
  const context = useContext(Context);
  if (!context) throw new Error('Wrap EPA pages in EpaProvider.');
  return context;
}
