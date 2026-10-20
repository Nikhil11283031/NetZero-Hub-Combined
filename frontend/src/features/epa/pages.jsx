import { useCallback, useState } from 'react';
import { Link } from 'react-router-dom';
import { useEpa } from './context.jsx';
import { useLoad } from './hooks.js';
import { FINAL_STATES, PROCESS, STATES, titleFor, analyse, duration } from './model.js';
import { Icon, PageTitle, ErrorNotice, Loading, Empty, CaseTable, Panel } from '../../components/ui.jsx';

export function Dashboard() {
  const { api, profile, basePath } = useEpa();
  const load = useLoad(useCallback((signal) => api.allCases(signal), [api]));
  const items = load.data || [];
  const open = items.filter((item) => !FINAL_STATES.has(item.state));
  const needInfo = items.filter((item) => item.state === 'AWAITING_INFORMATION');
  return <><PageTitle eyebrow="YOUR ENVIRONMENT WORKSPACE" title={profile.role === 'officer' ? 'EPA officer overview' : 'Environmental services'}>Manage your applications, follow progress and keep every case in view.</PageTitle>
    <section className="welcome-banner"><div><span className="banner-label">NSW ENVIRONMENT PROTECTION AUTHORITY</span><h2>A clearer path from<br/>request to outcome.</h2><p>Two connected services for licensing and pollution reports.</p><Link className="btn btn-lime" to={`${basePath}/licensing/applications/new`}>Start an application <Icon name="arrow" size={17}/></Link></div><div className="banner-art" aria-hidden="true"><div className="art-ring ring-one"/><div className="art-ring ring-two"/><div className="art-leaf"><Icon size={92}/></div><span className="art-caption">ENVIRONMENT<br/>IN FOCUS</span></div></section>
    <ErrorNotice error={load.error} retry={load.reload}/>
    <div className="metric-grid">{[['All cases', load.data ? items.length : '—', 'file'], ['In progress', load.data ? open.length : '—', 'clock'], ['Information needed', load.data ? needInfo.length : '—', 'file'], ['Completed', load.data ? items.length - open.length : '—', 'check']].map(([label, value, icon]) => <div className="metric" key={label}><span className="metric-label">{label}<Icon name={icon} size={18}/></span><strong>{value}</strong><span>{profile.role === 'officer' ? 'Across the EPA workspace' : 'For your account'}</span></div>)}</div>
    <div className="section-heading"><h2>Available services</h2><span>NSW EPA · 2 services</span></div>
    <div className="service-grid"><article className="service-card"><div className="service-card-top"><span className="service-icon"><Icon name="file" size={25}/></span><span className="service-code">EPA001</span></div><h3>Environment protection licences</h3><p>Apply for a prototype licence, supply requested information and manage licence variations.</p><div className="service-links"><Link to={`${basePath}/licensing/applications/new`}>Apply for a licence <Icon name="arrow" size={18}/></Link><Link className="secondary-link" to={`${basePath}/licences`}>View licences</Link></div></article>
      <article className="service-card"><div className="service-card-top"><span className="service-icon blue"><Icon name="drop" size={25}/></span><span className="service-code">EPA002</span></div><h3>Pollution incident reports</h3><p>Record a demonstration incident and follow its triage, investigation and outcome.</p><div className="service-links"><Link to={`${basePath}/incidents/new`}>Create an incident report <Icon name="arrow" size={18}/></Link><Link className="secondary-link" to={`${basePath}/cases?process=P3`}>View reports</Link></div></article></div>
    <Panel title="Recent cases" description="The latest activity on your accessible cases."><div className="panel-action"><Link to={`${basePath}/cases`}>View all cases <Icon name="arrow" size={16}/></Link></div>{load.loading ? <Loading/> : <CaseTable items={items.slice(0, 5)} basePath={basePath}/>}</Panel>
  </>;
}

export function Cases() {
  const { api, profile, basePath } = useEpa();
  const [search, setSearch] = useState('');
  const [process, setProcess] = useState(() => new URLSearchParams(window.location.search).get('process') || '');
  const [state, setState] = useState('');
  const load = useLoad(useCallback((signal) => api.allCases(signal), [api]));
  const items = (load.data || []).filter((item) => (!process || item.process === process) && (!state || item.state === state)
    && `${item.id} ${titleFor(item)}`.toLowerCase().includes(search.toLowerCase()));
  return <><PageTitle eyebrow="APPLICATIONS & REPORTS" title={profile.role === 'officer' ? 'Case workspace' : 'My cases'} actions={<button className="btn btn-outline-primary" onClick={load.reload}>Refresh</button>}>Open a case to see its details, completed steps and next actions.</PageTitle>
    <Panel><div className="filter-row"><label className="search-field">Search cases<input className="form-control" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Reference, applicant or location"/></label><label>Process<select className="form-select" value={process} onChange={(e) => setProcess(e.target.value)}><option value="">All processes</option>{Object.entries(PROCESS).map(([key, value]) => <option value={key} key={key}>{value}</option>)}</select></label><label>Status<select className="form-select" value={state} onChange={(e) => setState(e.target.value)}><option value="">All statuses</option>{Object.entries(STATES).map(([key, value]) => <option value={key} key={key}>{value}</option>)}</select></label></div>
      <ErrorNotice error={load.error} retry={load.reload}/>{load.loading ? <Loading/> : <CaseTable items={items} basePath={basePath}/>}<div className="table-footer">{items.length} matching {items.length === 1 ? 'case' : 'cases'}</div></Panel></>;
}

export function Licences() {
  const { api, basePath } = useEpa();
  const load = useLoad(useCallback((signal) => api.licences(signal), [api]));
  return <><PageTitle eyebrow="EPA001 · LICENCE MANAGEMENT" title="Licences" actions={<Link className="btn btn-primary" to={`${basePath}/licensing/applications/new`}>New application</Link>}>Approved prototype licences and their current recorded conditions.</PageTitle>
    <ErrorNotice error={load.error} retry={load.reload}/>{load.loading ? <Loading/> : !load.data?.length ? <Panel><Empty title="No licences yet" action={<Link className="btn btn-primary" to={`${basePath}/licensing/applications/new`}>Start an application</Link>}>A licence appears after an officer approves an application.</Empty></Panel> : <div className="licence-grid">{load.data.map((licence) => <Panel key={licence.id}><div className="licence-heading"><span className="service-icon"><Icon name="leaf"/></span><span className="status status-good">{licence.active ? 'Active' : 'Inactive'}</span></div><h2 className="licence-reference">{licence.id}</h2><p className="text-muted small">Version {licence.version} · Prototype licence</p><h3 className="small-heading">Current conditions</h3><ul className="condition-list">{licence.conditions.map((condition, index) => <li key={index}>{condition}</li>)}</ul><div className="form-actions"><Link className="btn btn-outline-primary" to={`${basePath}/licensing/variations/new?licence=${encodeURIComponent(licence.id)}`}>Request variation</Link><Link className="text-link" to={`${basePath}/cases/licensing/${licence.source_case}`}>Source application</Link></div></Panel>)}</div>}</>;
}

export function Analytics() {
  const { api } = useEpa();
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState(null);
  const load = useLoad(useCallback(async (signal) => {
    const [cases, licenceEvents, incidentEvents] = await Promise.all([api.allCases(signal), api.events('licensing', null, signal), api.events('incidents', null, signal)]);
    return analyse([...licenceEvents, ...incidentEvents], cases);
  }, [api]));
  async function download(service, format) {
    setExporting(true); setError(null);
    try {
      const blob = await api.export(service, format);
      const url = URL.createObjectURL(blob); const link = document.createElement('a');
      link.href = url; link.download = `epa-${service}-live-events.${format}`; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (cause) { setError(cause); }
    finally { setExporting(false); }
  }
  return <><PageTitle eyebrow="EXECUTION LOGS & ANALYTICS" title="Process activity" actions={<button className="btn btn-outline-primary" onClick={load.reload}>Refresh</button>}>Inspect activity generated by this running prototype and export it for process mining.</PageTitle><ErrorNotice error={load.error || error} retry={load.reload}/>
    <div className="info-note"><Icon name="chart"/><p>These are your live demonstration events. Elapsed times reflect this local session, including pauses between actions. They do not measure real EPA processing times or individual task effort.</p></div>
    {load.loading ? <Loading/> : load.data && <><div className="metric-grid analytics-metrics"><div className="metric"><span className="metric-label">Recorded events</span><strong>{load.data.eventCount}</strong><span>Across both services</span></div>{load.data.processes.map((item) => <div className="metric" key={item.process}><span className="metric-label">{PROCESS[item.process]}</span><strong>{item.cases}</strong><span>{item.completed} completed · Mean {duration(item.mean)}</span></div>)}</div>
      <Panel title="Observed process variants" description="Task sequences seen so far, including unfinished cases. A completed case can contain several events from one command.">{!load.data.variants.length ? <Empty title="No events yet">Complete a workflow to create data for this view.</Empty> : <div className="table-responsive"><table className="table"><thead><tr><th>Process</th><th>Observed sequence</th><th>Cases</th></tr></thead><tbody>{load.data.variants.map((item) => <tr key={item.process + item.path}><td>{item.process}</td><td className="trace-path">{item.path}</td><td>{item.count}</td></tr>)}</tbody></table></div>}</Panel></>}
    <Panel title="Export event logs" description="CSV for inspection; XES for a process-mining tool. Licensing contains P1 and P2. Incidents contains P3."><div className="export-grid">{['licensing', 'incidents'].map((service) => <div key={service}><h3>{service === 'licensing' ? 'Licensing service' : 'Incident service'}</h3><div className="button-row">{['csv', 'xes'].map((format) => <button key={format} className="btn btn-outline-primary" disabled={exporting} onClick={() => download(service, format)}>Download {service} {format.toUpperCase()}</button>)}</div></div>)}</div></Panel>
  </>;
}
