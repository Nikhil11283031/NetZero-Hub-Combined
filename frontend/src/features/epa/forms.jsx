import { useCallback, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useEpa } from './context.jsx';
import { useLoad, useSubmission } from './hooks.js';
import { lines } from './model.js';
import { PageTitle, Field, Panel, ErrorNotice, Loading, Empty, Icon } from '../../components/ui.jsx';

function FormFooter({ busy, label, basePath }) {
  return <div className="form-actions"><button className="btn btn-primary" type="submit" disabled={busy}>{busy ? 'Saving…' : label}<Icon name="arrow" size={17}/></button><Link className="text-link" to={basePath}>Cancel</Link></div>;
}
function FormAside({ process, title, children }) {
  return <aside className="form-aside"><span className="service-code">{process}</span><h2>{title}</h2>{children}<div className="aside-note">Use demonstration information only. Nothing entered here is sent to NSW EPA.</div></aside>;
}

export function ApplicationForm() {
  const { api, basePath } = useEpa(); const navigate = useNavigate();
  const [form, setForm] = useState({ applicant: '', premises: '', activity: '', consent_reference: '', fee_reference: '', documents: '' });
  const { busy, error, submit } = useSubmission();
  const bind = (key) => ({ value: form[key], onChange: (e) => setForm({ ...form, [key]: e.target.value }) });
  async function save(event) {
    event.preventDefault();
    const payload = { ...form, documents: lines(form.documents), consent_reference: form.consent_reference.trim() || null, fee_reference: form.fee_reference.trim() || null };
    await submit(payload, async (key) => {
      const item = await api.create('licensing', '/applications', payload, key);
      navigate(`${basePath}/cases/licensing/${item.id}`, { state: { notice: 'Application submitted. Your reference and progress are shown below.' } });
    });
  }
  return <><PageTitle eyebrow="EPA001 · NEW APPLICATION" title="Apply for a licence">Start a prototype environment protection licence application.</PageTitle><div className="form-layout"><Panel><form onSubmit={save}><ErrorNotice error={error}/><h2 className="form-section-title">Applicant and premises</h2><Field label="Applicant or organisation" required minLength={2} maxLength={150} autoComplete="organization" {...bind('applicant')}/><Field label="Premises address" required minLength={3} maxLength={300} autoComplete="street-address" {...bind('premises')}/><Field label="Proposed activity" textarea required minLength={3} maxLength={500} hint="Describe the activity for this demonstration application." {...bind('activity')}/>
      <h2 className="form-section-title separated">Supporting references</h2><p className="text-muted small">You can submit without these references to demonstrate the missing-information workflow.</p><div className="field-pair"><Field label="Consent reference" maxLength={200} {...bind('consent_reference')}/><Field label="Fee reference" maxLength={200} hint="Reference only; this prototype does not take payments." {...bind('fee_reference')}/></div><Field label="Document references" textarea hint="One reference per line, up to 20. References are stored as text; no files are uploaded." {...bind('documents')}/><FormFooter busy={busy} label="Submit application" basePath={basePath}/></form></Panel>
      <FormAside process="P1 · LICENCE APPLICATION" title="What happens next?"><ol><li>An officer checks your application.</li><li>You provide any missing information.</li><li>Environmental and suitability assessments are recorded.</li><li>A decision and outcome appear on your case.</li></ol></FormAside></div></>;
}

export function VariationForm() {
  const { api, basePath } = useEpa(); const navigate = useNavigate(); const [params] = useSearchParams();
  const [form, setForm] = useState({ licence_id: params.get('licence') || '', proposed_conditions: '', rationale: '' });
  const load = useLoad(useCallback((signal) => api.licences(signal), [api]));
  const { busy, error, submit } = useSubmission();
  const bind = (key) => ({ value: form[key], onChange: (e) => setForm({ ...form, [key]: e.target.value }) });
  const selected = load.data?.find((item) => item.id === form.licence_id);
  async function save(event) {
    event.preventDefault();
    const payload = { ...form, proposed_conditions: lines(form.proposed_conditions) };
    await submit(payload, async (key) => {
      const item = await api.create('licensing', '/variations', payload, key);
      navigate(`${basePath}/cases/licensing/${item.id}`, { state: { notice: 'Variation request submitted.' } });
    });
  }
  return <><PageTitle eyebrow="EPA001 · LICENCE MANAGEMENT" title="Request a licence variation">Propose a new set of conditions for an existing prototype licence.</PageTitle><ErrorNotice error={load.error} retry={load.reload}/>{load.loading ? <Loading/> : !load.data?.length ? <Panel><Empty title="An approved licence is needed" action={<Link className="btn btn-primary" to={`${basePath}/licensing/applications/new`}>Start an application</Link>}>Complete the application workflow before requesting a variation.</Empty></Panel> : <div className="form-layout"><Panel><form onSubmit={save}><ErrorNotice error={error}/><Field label="Licence" required {...bind('licence_id')}><option value="">Select a licence</option>{load.data.map((item) => <option key={item.id} value={item.id}>{item.id} · version {item.version}</option>)}</Field>{selected && <div className="current-conditions"><strong>Current conditions</strong><ul>{selected.conditions.map((condition, i) => <li key={i}>{condition}</li>)}</ul></div>}<Field label="Proposed conditions" textarea required hint="One condition per line, up to 20; each up to 200 characters. This becomes the full replacement set if approved." {...bind('proposed_conditions')}/><Field label="Reason for the change" textarea required minLength={3} maxLength={1000} {...bind('rationale')}/><FormFooter busy={busy} label="Submit variation" basePath={basePath}/></form></Panel><FormAside process="P2 · LICENCE VARIATION" title="Keep the licence current"><p>An officer checks eligibility, assesses the change and records a decision.</p><p>If another variation changes the licence first, this request may need to be submitted again against the latest version.</p></FormAside></div>}</>;
}

export function IncidentForm() {
  const { api, basePath } = useEpa(); const navigate = useNavigate();
  const [form, setForm] = useState({ category: '', location: '', description: '', observed_at: '', licence_id: '', emergency: false });
  const { busy, error, submit } = useSubmission();
  const bind = (key) => ({ value: form[key], onChange: (e) => setForm({ ...form, [key]: e.target.value }) });
  async function save(event) {
    event.preventDefault();
    // datetime-local is interpreted in the user's browser timezone, then sent as UTC.
    const payload = { ...form, observed_at: new Date(form.observed_at).toISOString(), licence_id: form.licence_id.trim() || null };
    await submit(payload, async (key) => {
      const item = await api.create('incidents', '/incidents', payload, key);
      navigate(`${basePath}/cases/incidents/${item.id}`, { state: { notice: 'Demonstration incident recorded. No report has been sent to an authority.' } });
    });
  }
  return <><PageTitle eyebrow="EPA002 · NEW REPORT" title="Report a pollution incident">Record a demonstration incident for triage and investigation.</PageTitle><div className="alert alert-warning"><strong>For immediate danger, call 000.</strong> This university prototype is not a real reporting channel and does not notify emergency services or NSW EPA.</div><div className="form-layout"><Panel><form onSubmit={save}><ErrorNotice error={error}/><div className="field-pair"><Field label="Pollution category" required {...bind('category')}><option value="">Select a category</option>{['air', 'water', 'land', 'noise', 'waste', 'other'].map((category) => <option key={category} value={category}>{category[0].toUpperCase() + category.slice(1)}</option>)}</Field><Field label="Date and time observed" type="datetime-local" required hint="Enter your local time; it will be stored with a timezone." {...bind('observed_at')}/></div><Field label="Incident location" required minLength={3} maxLength={300} {...bind('location')}/><Field label="What did you observe?" textarea required minLength={10} maxLength={2000} {...bind('description')}/><Field label="Prototype licence reference (optional)" maxLength={200} hint="If known, copy the reference from the Licences page. The investigator can look up its current conditions." {...bind('licence_id')}/><label className="checkbox-row"><input className="form-check-input" type="checkbox" checked={form.emergency} onChange={(e) => setForm({ ...form, emergency: e.target.checked })}/><span>This demonstration scenario involves an immediate threat.</span></label><FormFooter busy={busy} label="Submit demonstration report" basePath={basePath}/></form></Panel><FormAside process="P3 · INCIDENT INVESTIGATION" title="Follow the investigation"><ol><li>An officer records risk and jurisdiction.</li><li>The investigator collects evidence and reviews licence context.</li><li>The outcome is recorded and the case is closed.</li></ol><p>Emergency and referral scenarios follow separate paths.</p></FormAside></div></>;
}
