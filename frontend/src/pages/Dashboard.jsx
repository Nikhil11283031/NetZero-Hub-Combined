import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, getToken } from '../api.js';
import { Icon as EpaIcon } from '../components/ui.jsx';
import { createApi } from '../features/epa/api.js';
import { FINAL_STATES } from '../features/epa/model.js';

const Icon = ({ children }) => (
  <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor"
       strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    {children}
  </svg>
);

const icons = {
  recycling: (
    <Icon>
      <path d="M21 12a9 9 0 0 1-15.5 6.2M3 12A9 9 0 0 1 18.5 5.8" />
      <path d="M18.5 2v4h-4M5.5 22v-4h4" />
    </Icon>
  ),
  licence: <EpaIcon name="leaf" size={25} />,
  incident: (
    <Icon>
      <path d="M12 3 2 20h20L12 3z" />
      <path d="M12 10v4M12 17.5v.01" />
    </Icon>
  ),
  solar: (
    <Icon>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </Icon>
  ),
};

// All services are served by the shared portal on the same origin.
const cards = [
  {
    key: 'recycling',
    color: 'green',
    title: 'Recycling Collections',
    text: 'View your collection bookings, confirmed dates, and booking references.',
    viewLabel: 'View Collections',
    viewTo: '/bookings',
    newLabel: 'New Collection',
    newTo: '/book',
  },
  {
    key: 'licence',
    color: 'leaf',
    title: 'Environment Protection Licence',
    text: 'Track your licence applications, with status updates and reference numbers.',
    viewLabel: 'View Licences',
    viewTo: '/epa/licences',
    newLabel: 'New Application',
    newTo: '/epa/licensing/applications/new',
  },
  {
    key: 'incident',
    color: 'red',
    title: 'Pollution Incident Reports',
    text: 'Follow your pollution incident reports through investigation, with status updates.',
    viewLabel: 'View Reports',
    viewTo: '/epa/cases',
    newLabel: 'Report Incident',
    newTo: '/epa/incidents/new',
  },
  {
    key: 'solar',
    color: 'amber',
    title: 'Solar Installations',
    text: 'Follow your solar installation request from site assessment through to completion.',
    viewLabel: 'View Installations',
    viewTo: '/solar',
    newLabel: 'New Request',
    newTo: '/solar/new',
  },
];

// Decide whether an EPA case is a pollution incident (everything else counts as a licence).
// If your counts look wrong, this is the one line to adjust.
const isIncident = (item) =>
  /incident|pollution/i.test(
    String(item.type ?? item.kind ?? item.case_type ?? item.category ?? item.service ?? item.reference ?? '')
  );

// Recycling and solar counts come from Django; EPA counts come from both EPA APIs.
export default function Dashboard() {
  const [counts, setCounts] = useState(null);

  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    api('/dashboard/')
      .then((data) => {
        if (!active) return;
        setCounts((previous) => ({
          ...previous,
          recycling: data.recycling_count ?? 0,
          solar: data.solar_count ?? 0,
        }));
      })
      .catch(() => {});
    createApi({ token: getToken(), authScheme: 'Token' }).allCases(controller.signal)
      .then((cases) => {
        if (!active) return;
        const open = cases.filter((item) => !FINAL_STATES.has(item.state));
        setCounts((previous) => ({
          ...previous,
          incident: open.filter(isIncident).length,
          licence: open.filter((item) => !isIncident(item)).length,
        }));
      })
      .catch(() => {});
    return () => { active = false; controller.abort(); };
  }, []);

  return (
    <main className="dash">
      <section className="dash-main">
        <h1>My Services Dashboard</h1>
        <p className="dash-sub">
          Quickly access your collections, licence applications, pollution reports, and solar
          installation requests in one place.
        </p>

        <div className="dash-grid">
          {cards.map((c) => (
            <article key={c.key} className="dash-card">
              <div className="dash-card__top">
                <span className={`dash-icon dash-icon--${c.color}`}>{icons[c.key]}</span>
              </div>
              <div className="dash-card__title">
                <h2>{c.title}</h2>
                <span className="dash-count" aria-label={`${counts?.[c.key] ?? 'Unknown number of'} active records`}>
                  {counts?.[c.key] ?? '–'}
                </span>
              </div>
              <p>{c.text}</p>
              <div className="dash-actions">
                <Link to={c.viewTo} className="btn btn--primary">{c.viewLabel}</Link>
                <Link to={c.newTo} className="btn btn--secondary">{c.newLabel}</Link>
              </div>
            </article>
          ))}
        </div>

        <p className="dash-note">
          If pollution poses immediate danger to life or safety, call emergency services on 000.
        </p>
      </section>

      <footer className="dash-footer">
        <p>&copy; 2026 NetZero Hub. All rights reserved.</p>
      </footer>
    </main>
  );
}