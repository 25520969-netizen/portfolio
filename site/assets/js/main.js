import { initI18n } from './i18n.js';
import { initTheme } from './theme.js';
import { initNav } from './nav.js';
import { initCopy } from './copy.js';
import { initTrace } from './trace.js';
import { initReveal } from './reveal.js';

/** Run one initializer so a failure in it cannot stop the others. */
async function safely(name, init) {
  try {
    await init();
  } catch (error) {
    console.error(`${name} failed`, error);
  }
}

async function main() {
  await safely('i18n', initI18n);
  await safely('theme', initTheme);
  await safely('nav', initNav);
  await safely('copy', initCopy);
  await safely('trace', initTrace);
  await safely('reveal', initReveal);
}

main();
