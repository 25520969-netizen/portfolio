import { t } from './i18n.js';

const SECTION_ROOT_MARGIN = '-80px 0px -60% 0px';
const DESKTOP_QUERY = '(min-width: 768px)';

function initScrolledHairline() {
  const sentinel = document.getElementById('top-sentinel');
  const header = document.querySelector('.site-header');
  if (!sentinel || !header || !('IntersectionObserver' in window)) return;
  new IntersectionObserver(([entry]) => {
    header.classList.toggle('is-scrolled', !entry.isIntersecting);
  }).observe(sentinel);
}

function initActiveLink() {
  if (!('IntersectionObserver' in window)) return;
  const links = [...document.querySelectorAll('.nav-link')];
  const observer = new IntersectionObserver((entries) => {
    entries.filter((e) => e.isIntersecting).forEach((entry) => {
      links.forEach((link) => {
        if (link.getAttribute('href') === `#${entry.target.id}`) link.setAttribute('aria-current', 'true');
        else link.removeAttribute('aria-current');
      });
    });
  }, { rootMargin: SECTION_ROOT_MARGIN });
  document.querySelectorAll('section[id]').forEach((section) => observer.observe(section));
}

function initMobileMenu() {
  const toggle = document.getElementById('menu-toggle');
  const menu = document.getElementById('mobile-menu');
  if (!toggle || !menu) return;

  const isOpen = () => !menu.hidden;
  const syncToggle = () => {
    toggle.setAttribute('aria-expanded', String(isOpen()));
    const label = t(isOpen() ? 'menu.close' : 'menu.open');
    if (label !== 'menu.close' && label !== 'menu.open') toggle.setAttribute('aria-label', label);
    toggle.querySelector('use').setAttribute('href', isOpen() ? '#i-close' : '#i-menu');
  };
  const open = () => {
    menu.hidden = false;
    syncToggle();
    menu.querySelector('a').focus();
  };
  const close = ({ restoreFocus = true } = {}) => {
    menu.hidden = true;
    syncToggle();
    if (restoreFocus) toggle.focus({ preventScroll: true });
  };

  toggle.addEventListener('click', () => (isOpen() ? close() : open()));
  menu.addEventListener('click', (event) => {
    if (event.target.closest('a')) close();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && isOpen()) close();
  });
  window.matchMedia(DESKTOP_QUERY).addEventListener('change', (event) => {
    if (event.matches && isOpen()) close({ restoreFocus: false });
  });
  document.addEventListener('langchange', syncToggle);
  syncToggle();
}

export function initNav() {
  initScrolledHairline();
  initActiveLink();
  initMobileMenu();
}
