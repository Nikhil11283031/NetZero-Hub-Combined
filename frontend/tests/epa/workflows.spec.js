import { test, expect } from '@playwright/test';
import { mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const C = { Authorization: 'Bearer demo-client-token' };
const O = { Authorization: 'Bearer demo-officer-token' };
const base = '/api/v1/epa/';
const evidence = resolve('../results/frontend');
mkdirSync(evidence, { recursive: true });

async function login(page, role = 'Applicant / reporter') {
  await page.goto('/demo-access');
  await page.getByRole('button', { name: new RegExp(role.replace('/', '\\/')) }).click();
  await expect(page).toHaveURL(/\/epa$/);
  await expect(page.locator('.metric').first()).toBeVisible();
}
async function goOfficer(page, path) { await login(page, 'EPA officer'); await page.goto(path); }
function form(page, title) { return page.locator('form').filter({ has: page.getByRole('heading', { name: title, exact: true }) }); }
async function assess(page, title, button, pass = 'true') {
  const target = form(page, title);
  await target.getByLabel('Assessment result').selectOption(pass);
  await target.getByLabel('Rationale').fill('Synthetic assessment recorded for the university demonstration.');
  await target.getByRole('button', { name: button, exact: true }).click();
  await expect(target).toHaveCount(0);
}
async function createApplication(request, data = {}) {
  const response = await request.post(base + 'licensing/applications', { headers: { ...C, 'Idempotency-Key': crypto.randomUUID() }, data: {
    applicant: 'Browser test company', premises: 'Synthetic demonstration site', activity: 'Resource recovery',
    documents: ['site-plan-demo.pdf'], fee_reference: 'DEMO-FEE', consent_reference: 'DEMO-CONSENT', ...data,
  } });
  expect(response.ok()).toBeTruthy(); return response.json();
}
async function command(request, item, action, values = {}, service = 'licensing') {
  const response = await request.post(`${base}${service}/cases/${item.id}/commands`, { headers: O,
    data: { expected_version: item.version, action, values } });
  expect(response.ok(), await response.text()).toBeTruthy(); return response.json();
}

test('complete applicant → officer → variation → incident workflow through React', async ({ page }) => {
  const jsErrors = []; page.on('pageerror', (error) => jsErrors.push(error.message));
  await login(page);
  await page.getByRole('link', { name: 'Apply for a licence', exact: true }).click();
  await page.getByLabel('Applicant or organisation').fill('Green Coast Demonstration Pty Ltd');
  await page.getByLabel('Premises address').fill('12 Example Road, Wollongong NSW');
  await page.getByLabel('Proposed activity').fill('Synthetic resource recovery facility for coursework.');
  await page.getByRole('button', { name: 'Submit application', exact: true }).click();
  await expect(page).toHaveURL(/\/cases\/licensing\/P1-/);
  const appPath = new URL(page.url()).pathname;
  const appId = appPath.split('/').at(-1); const licence = `NZ-${appId}`;
  await goOfficer(page, appPath);
  await page.getByRole('button', { name: 'Check completeness', exact: true }).click();
  await expect(page.locator('.case-meta')).toContainText('Information needed');
  await login(page); await page.goto(appPath);
  await page.getByLabel('Document references').fill('site-plan-demo.pdf\nimpact-summary-demo.pdf');
  await page.getByLabel('Fee reference').fill('DEMO-FEE-001');
  await page.getByLabel('Consent reference').fill('DEMO-CONSENT-001');
  await page.getByRole('button', { name: 'Send information', exact: true }).click();
  await expect(page.locator('.case-meta')).toContainText('Submitted');
  await goOfficer(page, appPath);
  await page.getByRole('button', { name: 'Check completeness', exact: true }).click();
  await assess(page, 'Environmental assessment', 'Record environmental assessment');
  await assess(page, 'Suitability and consent', 'Record suitability assessment');
  await page.getByRole('combobox', { name: /^Decision/ }).selectOption('true');
  await page.getByLabel('Rationale').fill('Both assessments passed in this synthetic scenario.');
  await page.getByLabel('Licence conditions').fill('Keep a weekly demonstration inspection record.');
  await page.getByRole('button', { name: 'Record decision', exact: true }).click();
  await expect(page.locator('.case-meta')).toContainText('Approved');
  await login(page); await page.goto(`/epa/licensing/variations/new?licence=${licence}`);
  await page.getByLabel('Proposed conditions').fill('Keep a daily demonstration inspection record.');
  await page.getByLabel('Reason for the change').fill('Increase the frequency for the demonstration.');
  await page.getByRole('button', { name: 'Submit variation', exact: true }).click();
  await expect(page).toHaveURL(/\/cases\/licensing\/P2-/); const variationPath = new URL(page.url()).pathname;
  await goOfficer(page, variationPath);
  await page.getByRole('button', { name: 'Verify eligibility', exact: true }).click();
  await assess(page, 'Assess proposed conditions', 'Record variation assessment');
  await page.getByRole('combobox', { name: /^Decision/ }).selectOption('true');
  await page.getByLabel('Rationale').fill('The proposed change is accepted in the demonstration.');
  await page.getByRole('button', { name: 'Record decision', exact: true }).click();
  await expect(page.locator('.case-meta')).toContainText('Approved');
  await login(page); await page.goto('/epa/incidents/new');
  await page.getByLabel('Pollution category').selectOption('water');
  await page.getByLabel('Date and time observed').fill('2026-10-08T10:30');
  await page.getByLabel('Incident location').fill('Synthetic stream beside the demonstration site');
  await page.getByLabel('What did you observe?').fill('A synthetic discoloured discharge was observed for testing only.');
  await page.getByLabel('Prototype licence reference').fill(licence);
  await page.getByRole('button', { name: 'Submit demonstration report', exact: true }).click();
  await expect(page).toHaveURL(/\/cases\/incidents\/P3-/); const incidentPath = new URL(page.url()).pathname;
  await goOfficer(page, incidentPath);
  await page.getByRole('button', { name: 'Record triage', exact: true }).click();
  await page.getByLabel('Evidence summary').fill('Synthetic observation and sample notes recorded.');
  await page.getByRole('button', { name: 'Save evidence summary', exact: true }).click();
  await page.getByRole('button', { name: 'Review licence context', exact: true }).click();
  await expect(page.locator('.review-result')).toContainText([/Evidence collected/, /version 2/]);
  await page.getByLabel('Incident substantiated?').selectOption('true');
  await page.getByLabel('Rationale').fill('Demonstration action recorded; no real enforcement action taken.');
  await page.getByRole('button', { name: 'Record investigation outcome', exact: true }).click();
  await expect(page.locator('.case-meta')).toContainText('Action recorded');
  await page.screenshot({ path: resolve(evidence, 'incident-workflow.png'), fullPage: true });
  await page.goto('/epa'); await expect(page.getByRole('heading', { name: 'EPA officer overview' })).toBeVisible();
  await page.screenshot({ path: resolve(evidence, 'dashboard-desktop.png'), fullPage: true });
  expect(jsErrors).toEqual([]);
});

test('another applicant cannot read a case or its event history', async ({ page, request }) => {
  const item = await createApplication(request);
  await login(page, 'Another applicant'); await page.goto(`/epa/cases/licensing/${item.id}`);
  await expect(page.getByRole('alert')).toContainText('belongs to another user');
  await page.goto('/epa/cases'); await expect(page.getByText('No cases to show')).toBeVisible();
  const response = await request.get(`${base}licensing/cases/${item.id}/events`, { headers: { Authorization: 'Bearer demo-other-token' } });
  expect(response.status()).toBe(403);
});

test('concurrent change reports a conflict and refresh recovers the case', async ({ page, request }) => {
  const item = await createApplication(request);
  await goOfficer(page, `/epa/cases/licensing/${item.id}`);
  await expect(page.getByRole('button', { name: 'Check completeness', exact: true })).toBeVisible();
  await command(request, item, 'check');
  await page.getByRole('button', { name: 'Check completeness', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Stale version');
  await page.getByRole('button', { name: 'Refresh case', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Environmental assessment', exact: true })).toBeVisible();
});

test('failed assessment only offers refusal and a double click creates one case', async ({ page, request }) => {
  await login(page); await page.goto('/epa/licensing/applications/new');
  await page.getByLabel('Applicant or organisation').fill('Double click demonstration');
  await page.getByLabel('Premises address').fill('Synthetic location');
  await page.getByLabel('Proposed activity').fill('Synthetic activity');
  let submissions = 0;
  page.on('request', (req) => { if (req.method() === 'POST' && req.url().endsWith('/applications')) submissions += 1; });
  await page.getByRole('button', { name: 'Submit application', exact: true }).dblclick();
  await expect(page).toHaveURL(/\/cases\/licensing\/P1-/); expect(submissions).toBe(1);
  let item = await createApplication(request);
  item = await command(request, item, 'check');
  item = await command(request, item, 'assess_environment', { passed: false, rationale: 'Synthetic failure.' });
  item = await command(request, item, 'assess_suitability', { passed: true, rationale: 'Synthetic pass.' });
  await goOfficer(page, `/epa/cases/licensing/${item.id}`);
  await expect(page.getByRole('combobox', { name: /^Decision/ }).locator('option')).toHaveCount(1);
  await page.getByLabel('Rationale').fill('Environmental assessment failed in the synthetic scenario.');
  await page.getByRole('button', { name: 'Record decision', exact: true }).click();
  await expect(page.locator('.case-meta')).toContainText('Refused');
});

test('officer can download real CSV and XES event files', async ({ page }) => {
  await login(page, 'EPA officer'); await page.goto('/epa/analytics');
  await expect(page.getByRole('heading', { name: 'Observed process variants' })).toBeVisible();
  for (const format of ['CSV', 'XES']) {
    const pending = page.waitForEvent('download');
    await page.getByRole('button', { name: `Download licensing ${format}` }).click();
    const download = await pending; expect(download.suggestedFilename()).toBe(`epa-licensing-live-events.${format.toLowerCase()}`);
    const stream = await download.createReadStream(); let contents = ''; for await (const chunk of stream) contents += chunk;
    expect(contents).toContain(format === 'CSV' ? 'case_id,process,task_id' : '<trace>');
  }
});

test('mobile form works and service outage is explained', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 }); await login(page);
  const dashboardSize = await page.evaluate(() => ({ width: window.innerWidth, scroll: document.documentElement.scrollWidth,
    overflow: [...document.querySelectorAll('body *')].filter((el) => el.getBoundingClientRect().right > window.innerWidth).map((el) => ({ tag: el.tagName, className: el.className, right: el.getBoundingClientRect().right })).slice(0, 20) }));
  expect(dashboardSize.scroll, JSON.stringify(dashboardSize)).toBeLessThanOrEqual(dashboardSize.width);
  await page.screenshot({ path: resolve(evidence, 'dashboard-mobile.png'), fullPage: true });
  await page.goto('/epa/incidents/new');
  await expect(page.getByLabel('Incident location')).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  await page.route('**/api/v1/epa/incidents/cases', (route) => route.fulfill({ status: 503, contentType: 'application/json', body: '{"detail":"Incident service temporarily unavailable"}' }));
  await page.goto('/epa'); await expect(page.getByRole('alert')).toContainText('Incident service temporarily unavailable');
});
