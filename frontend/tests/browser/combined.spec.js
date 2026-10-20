import { test, expect } from '@playwright/test';
import { randomUUID } from 'node:crypto';
import { mkdir } from 'node:fs/promises';
import { join } from 'node:path';

const residentPassword = process.env.TEST_RESIDENT_PASSWORD || 'Resident927!Local';
const officerPassword = process.env.TEST_OFFICER_PASSWORD || 'Provider927!Local';
const prefix = '/api/v1/epa/';

async function photo(page, name) {
  if (!process.env.QA_SCREENSHOTS_DIR) return;
  await mkdir(process.env.QA_SCREENSHOTS_DIR, { recursive: true });
  await page.screenshot({ path: join(process.env.QA_SCREENSHOTS_DIR, name + '.png'), fullPage: true });
}

test('shared login, dashboard links, application submission and mobile navigation', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/login');
  await page.getByLabel('Username', { exact: true }).fill('resident');
  await page.getByLabel('Password', { exact: true }).fill(residentPassword);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  const card = page.locator('article.dash-card').filter({ hasText: 'Environment Protection' });
  await expect(card.locator('.dash-icon svg')).toBeVisible();
  await expect(card.locator('.dash-icon')).toHaveCSS('color', 'rgb(35, 95, 71)');
  await expect(card.getByRole('link', { name: 'View Requests' })).toHaveAttribute('href', '/epa/cases');
  await expect(card.getByRole('link', { name: 'New Request', exact: true })).toHaveAttribute('href', '/epa');
  await photo(page, 'dashboard-desktop');
  await card.getByRole('link', { name: 'View Requests' }).click();
  await expect(page.getByRole('heading', { level: 1, name: 'My cases' })).toBeVisible();
  await page.reload();
  await expect(page.getByRole('heading', { level: 1, name: 'My cases' })).toBeVisible();
  await page.getByRole('link', { name: 'Dashboard', exact: true }).click();
  await card.getByRole('link', { name: 'New Request', exact: true }).click();
  await expect(page.getByRole('heading', { level: 1, name: 'Environmental services' })).toBeVisible();
  await photo(page, 'epa-overview-desktop');
  await page.getByRole('link', { name: 'Start an application', exact: true }).click();
  await page.getByLabel('Applicant or organisation').fill('Browser demonstration company');
  await page.getByLabel('Premises address').fill('Synthetic test site');
  await page.getByLabel('Proposed activity').fill('Demonstration resource recovery');
  await page.getByRole('button', { name: 'Submit application' }).click();
  await expect(page).toHaveURL(/\/epa\/cases\/licensing\/P1-/);
  await expect(page.getByText('Application submitted. Your reference and progress are shown below.')).toBeVisible();
  await page.getByRole('link', { name: 'Dashboard', exact: true }).click();
  await expect(card.locator('.dash-count')).not.toHaveText('–');
  expect(Number(await card.locator('.dash-count').textContent())).toBeGreaterThan(0);

  // Other providers remain usable after loading the scoped EPA styles.
  await page.getByRole('link', { name: 'View Collections' }).click();
  await expect(page).toHaveURL(/\/bookings$/);
  await expect(page.getByText('Your recycling collection bookings.', { exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Dashboard', exact: true }).click();
  await page.getByRole('link', { name: 'View Installations' }).click();
  await expect(page).toHaveURL(/\/solar$/);
  await expect(page.getByRole('heading', { level: 1 })).toContainText('Solar');

  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole('link', { name: 'Dashboard', exact: true }).click();
  await card.getByRole('link', { name: 'New Request', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Environmental services', exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await photo(page, 'epa-overview-mobile');
  await page.getByRole('link', { name: 'My cases', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'My cases', exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await photo(page, 'epa-cases-mobile');
  await page.getByRole('button', { name: 'Sign out' }).click();
  await page.goto('/epa/cases');
  await expect(page).toHaveURL(/\/home$/);
  expect(errors).toEqual([]);
});

test('shared identity and HTTP composition complete all three EPA processes', async ({ request }) => {
  async function json(method, path, token, data, status = 200) {
    const response = await request[method](path, {
      headers: token ? { Authorization: `Token ${token}`, 'Idempotency-Key': randomUUID() } : {}, data,
    });
    expect(response.status(), await response.text()).toBe(status);
    return response.json();
  }
  const resident = await json('post', '/api/v1/auth/login/', null, { username: 'resident', password: residentPassword });
  const officer = await json('post', '/api/v1/auth/login/', null, { username: 'provider_admin', password: officerPassword });
  expect(resident.user.epa_role).toBe('client');
  expect(officer.user.epa_role).toBe('officer');
  const name = 'test_' + randomUUID().replaceAll('-', '').slice(0, 15);
  const outsider = await json('post', '/api/v1/auth/register/', null, {
    username: name, email: `${name}@example.test`, password: randomUUID() + '!aA7',
    epa_role: 'officer', is_staff: true,
  }, 201);
  expect(outsider.user.epa_role).toBe('client');

  async function act(service, item, action, values = {}) {
    return json('post', `${prefix}${service}/cases/${item.id}/commands`, officer.token,
      { expected_version: item.version, action, values });
  }
  let app = await json('post', prefix + 'licensing/applications', resident.token, {
    applicant: 'HTTP integration demo', premises: 'Synthetic site', activity: 'Resource recovery',
    documents: ['test-plan.pdf'], fee_reference: 'DEMO', consent_reference: 'DEMO',
  }, 201);
  expect(app.owner).toBe(`django:${resident.user.id}`);
  const forbidden = await request.get(`${prefix}licensing/cases/${app.id}`, { headers: { Authorization: `Token ${outsider.token}` } });
  expect(forbidden.status()).toBe(403);
  const denied = await request.post(`${prefix}licensing/cases/${app.id}/commands`, {
    headers: { Authorization: `Token ${resident.token}` }, data: { expected_version: app.version, action: 'check', values: {} },
  });
  expect(denied.status()).toBe(403);
  app = await act('licensing', app, 'check');
  for (const action of ['assess_environment', 'assess_suitability']) {
    app = await act('licensing', app, action, { passed: true, rationale: 'Synthetic check passed' });
  }
  app = await act('licensing', app, 'decide', { approved: true, rationale: 'Synthetic approval' });
  expect(app.state).toBe('APPROVED');
  const licence = app.data.licence_id;
  let variation = await json('post', prefix + 'licensing/variations', resident.token, {
    licence_id: licence, proposed_conditions: ['Updated demonstration condition'], rationale: 'Synthetic change',
  }, 201);
  variation = await act('licensing', variation, 'verify');
  variation = await act('licensing', variation, 'assess', { passed: true, rationale: 'Synthetic assessment' });
  variation = await act('licensing', variation, 'decide', { approved: true, rationale: 'Synthetic decision' });
  const updated = await json('get', prefix + 'licensing/licences/' + licence, resident.token);
  expect(updated.version).toBe(2);
  let incident = await json('post', prefix + 'incidents/incidents', resident.token, {
    category: 'water', location: 'Synthetic site', description: 'Synthetic pollution observation for integration testing',
    observed_at: new Date().toISOString(), licence_id: licence,
  }, 201);
  incident = await act('incidents', incident, 'triage', { emergency: false, epa_jurisdiction: true });
  incident = await act('incidents', incident, 'collect_evidence', { summary: 'Synthetic test evidence' });
  incident = await act('incidents', incident, 'review_licence');
  expect(incident.data.licence_context.match).toBe(true);
  expect(incident.data.licence_context.licence.version).toBe(2);
  incident = await act('incidents', incident, 'conclude', { substantiated: true, rationale: 'Synthetic conclusion' });
  expect(incident.state).toBe('ACTION_RECORDED');
  for (const service of ['licensing', 'incidents']) {
    for (const format of ['csv', 'xes']) {
      const response = await request.get(`${prefix}${service}/events/export?format=${format}`, { headers: { Authorization: `Token ${officer.token}` } });
      expect(response.status()).toBe(200);
      expect(await response.text()).toContain(format === 'csv' ? 'case_id' : '<log');
    }
  }
  await request.post('/api/v1/auth/logout/', { headers: { Authorization: `Token ${outsider.token}` } });
  const revoked = await request.get(prefix + 'licensing/me', { headers: { Authorization: `Token ${outsider.token}` } });
  expect(revoked.status()).toBe(401);
  const legacy = await request.get(prefix + 'licensing/me', { headers: { Authorization: 'Bearer demo-officer-token' } });
  expect(legacy.status()).toBe(401);
});
