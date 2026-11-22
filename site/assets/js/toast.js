const VISIBLE_MS = 2000;
let toastEl = null;
let hideTimer = 0;

function ensureToast() {
  if (toastEl) return toastEl;
  toastEl = document.createElement('div');
  toastEl.id = 'toast';
  toastEl.setAttribute('role', 'status');
  toastEl.setAttribute('aria-live', 'polite');
  toastEl.innerHTML = '<svg aria-hidden="true" focusable="false"><use href="#i-check"/></svg><span class="toast-text"></span>';
  document.body.appendChild(toastEl);
  return toastEl;
}

/**
 * Show one message for 2 s; a new call replaces it and resets the timer.
 * @param {string} message
 * @param {{ variant?: 'status' | 'error' }} [options]
 */
export function showToast(message, { variant = 'status' } = {}) {
  const el = ensureToast();
  const isError = variant === 'error';
  el.classList.toggle('toast--error', isError);
  el.querySelector('use').setAttribute('href', isError ? '#i-flag' : '#i-check');
  el.querySelector('.toast-text').textContent = message;
  // Force a reflow so a repeat call restarts the fade-in.
  el.classList.remove('is-visible');
  void el.offsetWidth;
  el.classList.add('is-visible');
  clearTimeout(hideTimer);
  hideTimer = setTimeout(() => el.classList.remove('is-visible'), VISIBLE_MS);
}
