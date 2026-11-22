import { save } from './storage.js';
import { t } from './i18n.js';

const DARK_QUERY = '(prefers-color-scheme: dark)';

function effectiveTheme() {
  const chosen = document.documentElement.dataset.theme;
  if (chosen === 'light' || chosen === 'dark') return chosen;
  return window.matchMedia(DARK_QUERY).matches ? 'dark' : 'light';
}

function syncToggle(btn) {
  const dark = effectiveTheme() === 'dark';
  // The label and icon describe the action: in dark mode the button offers light.
  const label = t(dark ? 'theme.toLight' : 'theme.toDark');
  if (label !== 'theme.toLight' && label !== 'theme.toDark') btn.setAttribute('aria-label', label);
  btn.querySelector('use').setAttribute('href', dark ? '#i-sun' : '#i-moon');
}

export function initTheme() {
  const btn = document.getElementById('theme-toggle');
  if (!btn) return;
  btn.addEventListener('click', () => {
    const next = effectiveTheme() === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    save('theme', next);
    syncToggle(btn);
  });
  document.addEventListener('langchange', () => syncToggle(btn));
  window.matchMedia(DARK_QUERY).addEventListener('change', () => syncToggle(btn));
  syncToggle(btn);
}
