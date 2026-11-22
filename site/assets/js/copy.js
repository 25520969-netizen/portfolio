import { showToast } from './toast.js';
import { t } from './i18n.js';

const COPIED_ICON_MS = 2000;
const resetTimers = new WeakMap();

function setIcon(btn, id) {
  const use = btn.querySelector('use');
  if (use) use.setAttribute('href', id);
}

function markCopied(btn) {
  setIcon(btn, '#i-check');
  clearTimeout(resetTimers.get(btn));
  resetTimers.set(btn, setTimeout(() => setIcon(btn, '#i-copy'), COPIED_ICON_MS));
}

function selectText(el) {
  const range = document.createRange();
  range.selectNodeContents(el);
  const selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
}

async function copyFrom(btn) {
  const source = document.getElementById(btn.dataset.copy);
  if (!source) return;
  try {
    if (!navigator.clipboard) throw new Error('Clipboard API unavailable');
    await navigator.clipboard.writeText(source.textContent.trim());
    markCopied(btn);
    showToast(t('toast.copied'));
  } catch (error) {
    console.warn('Copy failed; selecting the address instead.', error);
    selectText(source);
    showToast(t('toast.copyFail'), { variant: 'error' });
  }
}

export function initCopy() {
  document.querySelectorAll('button[data-copy]').forEach((btn) => {
    btn.addEventListener('click', () => copyFrom(btn));
  });
}
