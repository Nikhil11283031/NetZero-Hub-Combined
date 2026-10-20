import { defineConfig } from '@playwright/test';

// Run against a disposable local stack: these checks create demonstration records.
export default defineConfig({
  testDir: './tests/browser',
  workers: 1,
  timeout: 60000,
  reporter: 'list',
  use: {
    baseURL: process.env.TEST_BASE_URL || 'http://localhost:3000',
    viewport: { width: 1440, height: 1000 },
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    launchOptions: process.env.CHROMIUM_EXECUTABLE_PATH ? {
      executablePath: process.env.CHROMIUM_EXECUTABLE_PATH,
      args: ['--no-sandbox', '--disable-dev-shm-usage', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
    } : {},
  },
});
