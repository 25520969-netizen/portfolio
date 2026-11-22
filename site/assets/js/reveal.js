const THRESHOLD = 0.1;

export function initReveal() {
  if (!('IntersectionObserver' in window)) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const hashTarget = location.hash ? document.getElementById(location.hash.slice(1)) : null;
  const observer = new IntersectionObserver((entries) => {
    entries.filter((e) => e.isIntersecting).forEach((entry) => {
      entry.target.classList.add('is-visible');
      observer.unobserve(entry.target);
    });
  }, { threshold: THRESHOLD });
  document.querySelectorAll('section:not(.hero)').forEach((section) => {
    section.classList.add('reveal');
    if (section === hashTarget) section.classList.add('is-visible');
    else observer.observe(section);
  });
}
