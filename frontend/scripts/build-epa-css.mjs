// Preserve Bootstrap's licence and scope every selector to the EPA workspace.
// Recycling and solar keep their existing CSS; no global Bootstrap reset is added.
import { readFile, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import postcss from 'postcss';

const require = createRequire(import.meta.url);
const source = require.resolve('bootstrap/dist/css/bootstrap.css');
const css = postcss.parse(await readFile(source, 'utf8'), { from: source });
css.walkRules((rule) => {
  for (let parent = rule.parent; parent; parent = parent.parent) {
    if (parent.type === 'atrule' && /keyframes$/i.test(parent.name)) return;
  }
  rule.selectors = rule.selectors.map((selector) => {
    if (selector === ':root' || selector === 'body' || selector === 'html') return '.epa-app';
    if (selector.startsWith('[data-bs-theme=')) return `.epa-app${selector}`;
    return `.epa-app ${selector}`;
  });
});
css.walkComments((comment) => {
  if (/sourceMappingURL/.test(comment.text)) comment.remove();
});
await writeFile(new URL('../src/features/epa/bootstrap-scoped.css', import.meta.url), css.toString());
console.log('EPA-only Bootstrap styles generated.');
