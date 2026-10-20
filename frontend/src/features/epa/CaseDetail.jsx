import { useCallback, useRef, useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import { useEpa } from './context.jsx';
import { useLoad } from './hooks.js';
import { PROCESS, FINAL_STATES, displayDate, lines, titleFor } from './model.js';
import { PageTitle, Panel, Status, ErrorNotice, Loading, Empty, Field, Icon } from '../../components/ui.jsx';

function ActionForm({ title, description, label, action, fields = [], busy, onCommand, initial = {} }) {
  const [values, setValues] = useState(() => Object.fromEntries(fields.map((field) => [field.name, initial[field.name] ?? field.default ?? ''])));
  const submit = (event) => {
    event.preventDefault();
    const payload = {};
    for (const field of fields) {
      const value = values[field.name];
      if (field.optional && !String(value).trim()) continue;
      payload[field.name] = field.kind === 'boolean' ? value === 'true' : field.kind === 'lines' ? lines(value) : value.trim();
    }
    onCommand(action, payload);
  };
  return <form className="action-form" onSubmit={submit}><h3>{title}</h3>{description && <p className="small text-muted">{description}</p>}
    {fields.map((field) => <Field key={field.name} label={field.label} required={!field.optional}
      textarea={field.kind === 'lines' || field.kind === 'text'} hint={field.hint}
      maxLength={field.kind === 'boolean' ? undefined : field.maxLength || 2000}
      value={values[field.name]} onChange={(event) => setValues({ ...values, [field.name]: event.target.value })}>
      {field.kind === 'boolean' ? <>{!field.falseOnly && <option value="true">{field.yes || 'Yes'}</option>}<option value="false">{field.no || 'No'}</option></> : undefined}
    </Field>)}
    <button className="btn btn-primary" type="submit" disabled={Boolean(busy)}>{busy === action ? 'Saving…' : label || title}</button>
  </form>;
}

const rationale = { name: 'rationale', label: 'Rationale', kind: 'text' };
const passed = { name: 'passed', label: 'Assessment result', kind: 'boolean', default: 'true', yes: 'Pass', no: 'Fail' };

function Actions({ item, busy, onCommand }) {
  const { profile } = useEpa();
  const { process, state, data } = item;
  const officer = profile.role === 'officer';
  const shared = { busy, onCommand };
  if (FINAL_STATES.has(state)) return <div className="completed-note"><span className="service-icon"><Icon name="check"/></span><h3>This case is complete</h3><p>The recorded outcome and activity history remain available here.</p></div>;
  if (process === 'P1' && state === 'AWAITING_INFORMATION') {
    const expired = Date.now() >= Date.parse(data.information_due_at);
    return <><div className="alert alert-warning">Information due: <strong>{displayDate(data.information_due_at)}</strong>. The prototype uses a 30-day information window.</div>
      {!expired && <ActionForm {...shared} action="supply" title="Provide missing information" label="Send information" initial={{ documents: data.documents?.join('\n') || '', fee_reference: data.fee_reference || '', consent_reference: data.consent_reference || '' }} fields={[
        { name: 'documents', label: 'Document references', kind: 'lines', hint: 'One reference per line, up to 20. Text references only.' },
        { name: 'fee_reference', label: 'Fee reference', maxLength: 200 }, { name: 'consent_reference', label: 'Consent reference', maxLength: 200 },
      ]}/>}
      {expired && (officer ? <ActionForm {...shared} action="expire" title="Close incomplete application" fields={[rationale]}/> : <p>The information window has elapsed. An officer must close this case.</p>)}</>;
  }
  if (!officer) return <div className="waiting-note"><Icon name="clock" size={28}/><h3>Waiting for an officer</h3><p>Your case is saved. Check back for the next step or a recorded outcome.</p></div>;
  if (process === 'P1') {
    if (state === 'SUBMITTED') return <ActionForm {...shared} action="check" title="Check application completeness" description="The service checks the document, consent and fee references. Missing information opens a request to the applicant." label="Check completeness"/>;
    if (state === 'ASSESSMENT') {
      const both = data.environment && data.suitability;
      const canApprove = both && data.environment.passed && data.suitability.passed;
      return <>
        {!data.environment && <ActionForm {...shared} action="assess_environment" title="Environmental assessment" label="Record environmental assessment" fields={[passed, rationale]}/>}
        {!data.suitability && <ActionForm {...shared} action="assess_suitability" title="Suitability and consent" label="Record suitability assessment" fields={[passed, rationale]}/>}
        {both ? <ActionForm {...shared} action="decide" title="Record application decision" description={canApprove ? 'Both assessments passed. Record your decision and its rationale.' : 'An assessment failed. This application can only be refused.'} label="Record decision" fields={[
          { name: 'approved', label: 'Decision', kind: 'boolean', default: 'false', yes: 'Approve', no: 'Refuse', falseOnly: !canApprove }, rationale,
          { name: 'conditions', label: 'Licence conditions', kind: 'lines', optional: true, hint: 'One per line. Applies to approval only; leave blank for the prototype default.' },
        ]}/> : <p className="small text-muted">Both assessments must be recorded before a decision can be made.</p>}
      </>;
    }
  }
  if (process === 'P2') {
    if (state === 'SUBMITTED') return <ActionForm {...shared} action="verify" title="Verify licence eligibility" description="Checks that the licence is active and still has the version captured when this request was submitted." label="Verify eligibility"/>;
    if (!data.assessment) return <ActionForm {...shared} action="assess" title="Assess proposed conditions" label="Record variation assessment" fields={[passed, rationale]}/>;
    return <ActionForm {...shared} action="decide" title="Record variation decision" label="Record decision" fields={[
      { name: 'approved', label: 'Decision', kind: 'boolean', default: 'false', yes: 'Approve', no: 'Refuse', falseOnly: !data.assessment.passed }, rationale,
    ]}/>;
  }
  if (process === 'P3') {
    if (state === 'SUBMITTED') return <ActionForm {...shared} action="triage" title="Triage risk and jurisdiction" label="Record triage" initial={{ emergency: String(data.emergency || false) }} fields={[
      { name: 'emergency', label: 'Immediate threat?', kind: 'boolean', default: 'false' },
      { name: 'epa_jurisdiction', label: 'Within EPA jurisdiction for this scenario?', kind: 'boolean', default: 'true' },
    ]}/>;
    return <>
      {!data.evidence && <ActionForm {...shared} action="collect_evidence" title="Record investigation evidence" label="Save evidence summary" fields={[{ name: 'summary', label: 'Evidence summary', kind: 'text' }]}/>}
      {!data.licence_context && <ActionForm {...shared} action="review_licence" title="Review licence context" description={data.licence_id ? `Retrieves current conditions for ${data.licence_id} from the licensing service.` : 'No licence was supplied. This step records that fact for the investigation.'} label="Review licence context"/>}
      {data.evidence && data.licence_context ? <ActionForm {...shared} action="conclude" title="Conclude investigation" label="Record investigation outcome" fields={[
        { name: 'substantiated', label: 'Incident substantiated?', kind: 'boolean', default: 'false', yes: 'Yes — record action', no: 'No — no further action' }, rationale,
      ]}/> : <p className="small text-muted">Evidence collection and licence review must both finish before the case can be concluded.</p>}
    </>;
  }
  return <p>No action is available in this state.</p>;
}

function Details({ item }) {
  const { data, process } = item;
  const rows = process === 'P1' ? [['Applicant', data.applicant], ['Premises', data.premises], ['Activity', data.activity], ['Consent reference', data.consent_reference], ['Fee reference', data.fee_reference], ['Document references', data.documents]]
    : process === 'P2' ? [['Licence', data.licence_id], ['Licence version at submission', data.licence_version], ['Proposed conditions', data.proposed_conditions], ['Reason for change', data.rationale]]
      : [['Category', data.category], ['Location', data.location], ['Observed', displayDate(data.observed_at)], ['Description', data.description], ['Licence reference', data.licence_id], ['Immediate threat reported', data.emergency ? 'Yes' : 'No']];
  return <dl className="detail-list">{rows.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{Array.isArray(value) ? value.length ? <ul>{value.map((entry, i) => <li key={i}>{entry}</li>)}</ul> : 'Not supplied' : value || 'Not supplied'}</dd></div>)}</dl>;
}

function Reviews({ data }) {
  const reviews = [['Environmental assessment', data.environment], ['Suitability assessment', data.suitability], ['Variation assessment', data.assessment]];
  return <>{reviews.filter(([, value]) => value).map(([name, value]) => <div className="review-result" key={name}><strong>{name}<span className={`status ${value.passed ? 'status-good' : 'status-warning'}`}>{value.passed ? 'Passed' : 'Failed'}</span></strong><p>{value.rationale}</p></div>)}
    {data.evidence && <div className="review-result"><strong>Evidence collected</strong><p>{data.evidence.summary}</p></div>}
    {data.licence_context && <div className="review-result"><strong>Licence context review</strong><p>{data.licence_context.summary}</p>{data.licence_context.licence && <><p className="small">{data.licence_context.licence.id} · version {data.licence_context.licence.version}</p><ul>{data.licence_context.licence.conditions.map((condition, i) => <li key={i}>{condition}</li>)}</ul></>}</div>}
  </>;
}

export default function CaseDetail() {
  const { service, caseId } = useParams(); const { api, basePath } = useEpa(); const location = useLocation();
  const [busy, setBusy] = useState(null); const lock = useRef(false);
  const [error, setError] = useState(null); const [notice, setNotice] = useState(location.state?.notice || '');
  const load = useLoad(useCallback(async (signal) => {
    const [item, events] = await Promise.all([api.case(service, caseId, signal), api.events(service, caseId, signal)]);
    return { item, events };
  }, [api, service, caseId]));
  const refresh = () => { setError(null); load.reload(); };
  async function command(action, values) {
    if (lock.current) return;
    lock.current = true; setBusy(action); setError(null); setNotice('');
    try {
      await api.command(service, load.data.item, action, values);
      setNotice('Your action was saved. The case and activity history have been updated.'); load.reload();
    } catch (cause) { setError(cause); }
    finally { lock.current = false; setBusy(null); }
  }
  if (load.loading) return <Loading/>;
  if (load.error) return <><Link className="back-link" to={`${basePath}/cases`}>← Back to cases</Link><ErrorNotice error={load.error} retry={refresh}/></>;
  if (!load.data) return <Empty title="Case unavailable"/>;
  const { item, events } = load.data;
  const outcome = item.data.decision_rationale || item.data.outcome;
  return <><Link className="back-link" to={`${basePath}/cases`}>← Back to cases</Link><PageTitle eyebrow={`${PROCESS[item.process]} · ${item.id}`} title={titleFor(item)} actions={<button className="btn btn-outline-primary" disabled={Boolean(busy)} onClick={refresh}>Refresh case</button>}/>
    <div className="case-meta"><Status value={item.state}/><span>Case version {item.version}</span><span>Updated {displayDate(item.updated_at)}</span></div>
    {notice && <div className="alert alert-success" role="status">{notice}</div>}<ErrorNotice error={error}/>{error?.status === 409 && <p className="small">If another action changed this case, refresh it before trying again.</p>}
    {outcome && <div className="outcome"><p className="eyebrow">RECORDED OUTCOME</p><p>{outcome}</p>{item.process === 'P1' && item.data.licence_id && <Link to={`${basePath}/licences`}>View licence {item.data.licence_id} <Icon name="arrow" size={16}/></Link>}</div>}
    <div className="case-layout"><div><Panel title="Case details"><Details item={item}/><Reviews data={item.data}/></Panel><Panel title="Activity history" description={`${events.length} completed activities · All times shown in your browser's local timezone.`}><ol className="timeline">{events.map((event) => <li key={event.seq}><span className="timeline-dot"><Icon name="check" size={12}/></span><div><strong>{event.activity}</strong><span>{event.task_id} · {event.resource}</span><time dateTime={event.timestamp}>{displayDate(event.timestamp)}</time></div></li>)}</ol></Panel></div><Panel title="Next steps" className="actions-panel"><Actions key={`${item.id}-${item.version}`} item={item} busy={busy} onCommand={command}/></Panel></div>
  </>;
}
