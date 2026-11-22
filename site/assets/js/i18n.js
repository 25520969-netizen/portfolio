import { save } from './storage.js';

export const LANGS = ['en', 'vi'];

const BASE_URL = 'https://25520969-netizen.github.io/portfolio/';
const CANONICAL = { en: BASE_URL, vi: BASE_URL + '?lang=vi' };
const OG_LOCALE = { en: 'en_US', vi: 'vi_VN' };
const HTML_KEYS = new Set(['vr.b2']);
const dictionaries = new Map();
let current = {};
let fallback = {};
let warned = false;

/** @returns {'en' | 'vi'} */
export function currentLang() {
  return document.documentElement.lang === 'vi' ? 'vi' : 'en';
}

/** @param {string} key @returns {string} */
export function t(key) {
  return current[key] ?? fallback[key] ?? key;
}

function warnOnce(error) {
  if (warned) return;
  warned = true;
  console.warn('Could not load translations; showing English.', error);
}

async function loadDict(lang) {
  if (!dictionaries.has(lang)) {
    const response = await fetch(`assets/i18n/${lang}.json`);
    if (!response.ok) throw new Error(`${lang}.json: HTTP ${response.status}`);
    dictionaries.set(lang, await response.json());
  }
  return dictionaries.get(lang);
}

function applyDictionary() {
  document.querySelectorAll('[data-i18n]').forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
  document.querySelectorAll('[data-i18n-html]').forEach((el) => {
    const key = el.dataset.i18nHtml;
    if (HTML_KEYS.has(key)) el.innerHTML = t(key);
  });
  document.querySelectorAll('[data-i18n-attr]').forEach((el) => {
    el.dataset.i18nAttr.split(';').forEach((pair) => {
      const [attr, key] = pair.split(':');
      if (attr && key) el.setAttribute(attr.trim(), t(key.trim()));
    });
  });
}

function setMeta(selector, attr, value) {
  const el = document.querySelector(selector);
  if (el) el.setAttribute(attr, value);
}

function applyHead(lang) {
  document.title = t('meta.title');
  setMeta('meta[name="description"]', 'content', t('meta.desc'));
  setMeta('meta[property="og:locale"]', 'content', OG_LOCALE[lang]);
  setMeta('meta[property="og:url"]', 'content', CANONICAL[lang]);
  let canonical = document.querySelector('link[rel="canonical"]');
  if (!canonical) {
    canonical = document.createElement('link');
    canonical.rel = 'canonical';
    document.head.appendChild(canonical);
  }
  canonical.href = CANONICAL[lang];
}

function writeLangToUrl(lang) {
  const url = new URL(location.href);
  url.searchParams.set('lang', lang);
  history.replaceState(null, '', url);
}

/**
 * Swap all text to `lang` in place, keeping scroll position and hash.
 * @param {'en' | 'vi'} lang
 */
export async function setLang(lang, { persist = true, updateUrl = true } = {}) {
  if (!LANGS.includes(lang)) return;
  let dict;
  try {
    [dict, fallback] = await Promise.all([loadDict(lang), loadDict('en')]);
  } catch (error) {
    warnOnce(error);
    return;
  }
  const y = window.scrollY;
  current = dict;
  document.documentElement.lang = lang;
  applyDictionary();
  applyHead(lang);
  document.querySelectorAll('[data-lang]').forEach((btn) => {
    btn.setAttribute('aria-pressed', String(btn.dataset.lang === lang));
  });
  document.documentElement.classList.remove('i18n-pending');
  if (persist) save('lang', lang);
  if (updateUrl) writeLangToUrl(lang);
  window.scrollTo({ top: y, behavior: 'instant' });
  document.dispatchEvent(new CustomEvent('langchange', { detail: { lang } }));
}

function dropInvalidLangParam() {
  const url = new URL(location.href);
  const value = url.searchParams.get('lang');
  if (value !== null && !LANGS.includes(value)) {
    url.searchParams.delete('lang');
    history.replaceState(null, '', url);
  }
}

async function fallbackToEnglish(error) {
  warnOnce(error);
  document.documentElement.lang = 'en';
  document.documentElement.classList.remove('i18n-pending');
}

export async function initI18n() {
  dropInvalidLangParam();
  document.querySelectorAll('[data-lang]').forEach((btn) => {
    btn.addEventListener('click', () => setLang(btn.dataset.lang));
  });
  const lang = currentLang();
  try {
    if (lang === 'vi') {
      await setLang('vi', { persist: false, updateUrl: false });
      if (currentLang() !== 'vi') throw new Error('vi dictionary unavailable');
      return;
    }
    fallback = current = await loadDict('en');
    applyHead('en');
    document.querySelectorAll('[data-lang]').forEach((btn) => {
      btn.setAttribute('aria-pressed', String(btn.dataset.lang === 'en'));
    });
  } catch (error) {
    await fallbackToEnglish(error);
  }
}
