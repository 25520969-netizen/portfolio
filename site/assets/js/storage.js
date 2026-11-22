// Safe localStorage access. Keys are prefixed because github.io origins are shared.
const PREFIX = 'vhk.';

/** @param {string} key @returns {string | null} */
export function load(key) {
  try {
    return localStorage.getItem(PREFIX + key);
  } catch (error) {
    return null;
  }
}

/** @param {string} key @param {string} value */
export function save(key, value) {
  try {
    localStorage.setItem(PREFIX + key, value);
  } catch (error) {
    // Storage can be blocked (private mode, site data off); the choice just won't persist.
  }
}
