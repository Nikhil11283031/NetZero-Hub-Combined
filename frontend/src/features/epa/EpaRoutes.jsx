import { useEffect } from 'react';
import { Routes, Route, NavLink, Link, useLocation } from 'react-router-dom';
import { useEpa } from './context.jsx';
import { Icon, Empty } from '../../components/ui.jsx';
import { Dashboard, Cases, Licences, Analytics } from './pages.jsx';
import { ApplicationForm, IncidentForm, VariationForm } from './forms.jsx';
import CaseDetail from './CaseDetail.jsx';

export default function EpaRoutes({ embedded = false }) {
  const { profile, basePath, onSwitchProfile } = useEpa();
  const location = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [location.pathname]);
  const navigation = [
    ['', 'Overview', 'grid'], ['/cases', profile.role === 'officer' ? 'Case workspace' : 'My cases', 'file'],
    ['/licences', 'Licences', 'leaf'], ...(profile.role === 'officer' ? [['/analytics', 'Process activity', 'chart']] : []),
  ];
  const pages = <Routes>
    <Route index element={<Dashboard/>}/><Route path="cases" element={<Cases/>}/>
    <Route path="cases/:service/:caseId" element={<CaseDetail/>}/>
    <Route path="licences" element={<Licences/>}/>
    <Route path="licensing/applications/new" element={<ApplicationForm/>}/>
    <Route path="licensing/variations/new" element={<VariationForm/>}/>
    <Route path="incidents/new" element={<IncidentForm/>}/>
    <Route path="analytics" element={profile.role === 'officer' ? <Analytics/> : <Empty title="Officer access required">Process-wide logs are available to the officer account.</Empty>}/>
    <Route path="*" element={<Empty title="Page not found" action={<Link className="btn btn-primary" to={basePath}>Return to overview</Link>}>Check the address or return to your workspace.</Empty>}/>
  </Routes>;
  if (embedded) return <section className="epa-app epa-embedded" data-bs-theme="light" aria-label="NSW EPA services">
    <nav className="embedded-nav" aria-label="EPA navigation">{navigation.map(([path, label, icon]) => <NavLink key={path} to={basePath + path} end={path === ''}><Icon name={icon} size={17}/>{label}</NavLink>)}</nav>
    <div className="main-content">{pages}</div>
  </section>;
  return <div className="epa-app"><a className="skip-link" href="#main-content">Skip to content</a>
    <header className="topbar"><Link to={basePath} className="brand"><Icon size={28}/><span>NetZero<strong>Hub</strong></span></Link><span className="topbar-divider"/><span className="topbar-provider">NSW EPA services</span><span className="prototype-pill">University prototype</span></header>
    <aside className="sidebar"><div className="workspace-label">ENVIRONMENT WORKSPACE</div><nav aria-label="EPA navigation">{navigation.map(([path, label, icon]) => <NavLink key={path} to={basePath + path} end={path === ''}><Icon name={icon} size={20}/>{label}</NavLink>)}</nav>
      <div className="sidebar-footer"><div className="avatar">{profile.role === 'officer' ? 'EO' : 'AR'}</div><div><strong>{profile.name || profile.subject}</strong><span>{profile.role === 'officer' ? 'Officer workspace' : 'Personal workspace'}</span></div>{onSwitchProfile && <button onClick={onSwitchProfile} className="switch-profile">Switch demo account</button>}</div></aside>
    <div className="main-wrapper"><main id="main-content" className="main-content">{pages}</main><footer className="workspace-footer"><span>NetZero Hub · NSW EPA contribution</span><span>Educational prototype · No real submissions</span></footer></div>
  </div>;
}
