import { useId } from 'react';
import { Link } from 'react-router-dom';
import { STATES, FINAL_STATES, displayDate, titleFor, PROCESS } from '../features/epa/model.js';

export function Icon({ name = 'leaf', size = 22, ...props }) {
  const paths = {
    leaf: <><path d="M4 14C4 6 12 3 21 3c0 9-3 17-11 17-4 0-6-2-6-6Z"/><path d="m3 22 12-12"/></>,
    grid: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
    file: <><path d="M14 2H5v20h14V7Z"/><path d="M14 2v6h5M8 12h8M8 16h6"/></>,
    drop: <path d="M12 2c-2 4-8 10-8 14a8 8 0 0 0 16 0c0-4-6-10-8-14Z"/>,
    chart: <><path d="M3 3v18h19M7 16v-5M12 16V7M17 16v-8"/></>,
    arrow: <path d="M4 12h16m-6-6 6 6-6 6"/>,
    check: <path d="m5 12 4 4L20 5"/>,
    clock: <><circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 2"/></>,
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>{paths[name] || paths.file}</svg>;
}
export function PageTitle({ eyebrow, title, children, actions }) {
  return <div className="page-heading"><div>{eyebrow && <p className="eyebrow">{eyebrow}</p>}<h1>{title}</h1>{children && <p className="page-description">{children}</p>}</div>{actions && <div className="heading-actions">{actions}</div>}</div>;
}
export function ErrorNotice({ error, retry }) {
  if (!error) return null;
  return <div className="alert alert-danger" role="alert"><strong>Something needs your attention.</strong><div>{error.message || String(error)}</div>{retry && <button className="btn btn-sm btn-outline-danger mt-2" onClick={retry}>Try again</button>}</div>;
}
export function Loading() { return <div className="loading" role="status"><span className="spinner-border spinner-border-sm"/> Loading your EPA services…</div>; }
export function Empty({ title, children, action }) {
  return <div className="empty"><span className="empty-icon"><Icon name="file" size={28}/></span><h3>{title}</h3><p>{children}</p>{action}</div>;
}
export function Status({ value }) {
  const tone = ['APPROVED', 'ACTION_RECORDED', 'NO_FURTHER_ACTION'].includes(value) ? 'good' : value === 'AWAITING_INFORMATION' ? 'warning' : FINAL_STATES.has(value) ? 'neutral' : 'active';
  return <span className={`status status-${tone}`}><span className="status-dot"/>{STATES[value] || value}</span>;
}
export function Field({ label, hint, textarea, children, ...props }) {
  const id = useId(); const Control = textarea ? 'textarea' : 'input';
  return <div className="field"><label className="form-label" htmlFor={id}>{label}{props.required && <span className="required" aria-hidden="true"> *</span>}</label>
    {children ? <select id={id} className="form-select" aria-describedby={hint ? `${id}-hint` : undefined} {...props}>{children}</select>
      : <Control id={id} className="form-control" rows={textarea ? 4 : undefined} aria-describedby={hint ? `${id}-hint` : undefined} {...props}/>}
    {hint && <div className="form-text" id={`${id}-hint`}>{hint}</div>}</div>;
}
export function CaseTable({ items, basePath }) {
  if (!items.length) return <Empty title="No cases to show">Your submitted applications, variations and incident reports will appear here.</Empty>;
  return <div className="table-responsive"><table className="table case-table"><thead><tr><th>Case / reference</th><th>Service process</th><th>Status</th><th>Last updated</th><th><span className="visually-hidden">Open case</span></th></tr></thead>
    <tbody>{items.map((item) => <tr key={item.id}><td><Link className="case-name" to={`${basePath}/cases/${item.service}/${item.id}`}>{titleFor(item)}</Link><span className="reference">{item.id}</span></td><td>{PROCESS[item.process]}</td><td><Status value={item.state}/></td><td className="text-muted small">{displayDate(item.updated_at)}</td><td><Link className="icon-link" aria-label={`Open ${item.id}`} to={`${basePath}/cases/${item.service}/${item.id}`}><Icon name="arrow" size={19}/></Link></td></tr>)}</tbody></table></div>;
}
export function Panel({ title, description, children, className = '' }) {
  return <section className={`panel ${className}`}>{title && <div className="panel-heading"><h2>{title}</h2>{description && <p>{description}</p>}</div>}{children}</section>;
}
