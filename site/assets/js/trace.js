const REDUCED_MOTION = '(prefers-reduced-motion: reduce)';
const EASE = 'cubic-bezier(.2,.7,.2,1)';
const START_DELAY_MS = 200;
const SEGMENT_MS = 600;
const NODE_COUNT = 4;
const HOLD_MS = 200;
const FADE_MS = 200;
const TOTAL_MS = START_DELAY_MS + (NODE_COUNT - 1) * SEGMENT_MS + HOLD_MS + FADE_MS;

let animation = null;
let timers = [];
let onResize = null;

function clearRun(trace) {
  animation?.cancel();
  animation = null;
  timers.forEach(clearTimeout);
  timers = [];
  if (onResize) window.removeEventListener('resize', onResize);
  onResize = null;
  trace.classList.remove('is-done');
  trace.querySelectorAll('.node').forEach((node) => node.classList.remove('is-active'));
}

/** End state: every node active, dot gone, `.is-done` set. */
function completeRun(trace) {
  clearRun(trace);
  trace.querySelectorAll('.node').forEach((node) => node.classList.add('is-active'));
  trace.classList.add('is-done');
}

function nodeCentres(track) {
  const origin = track.getBoundingClientRect();
  return [...track.querySelectorAll(':scope > .node')].map((node) => {
    const box = node.getBoundingClientRect();
    return { x: box.left - origin.left + box.width / 2, y: box.top - origin.top + box.height / 2 };
  });
}

function buildKeyframes(points) {
  const at = (ms) => ms / TOTAL_MS;
  const move = (p) => `translate(${p.x}px, ${p.y}px)`;
  const stops = [
    [0, points[0], 1], [START_DELAY_MS, points[0], 1],
    [START_DELAY_MS + SEGMENT_MS, points[1], 1],
    [START_DELAY_MS + 2 * SEGMENT_MS, points[2], 1],
    [START_DELAY_MS + 3 * SEGMENT_MS, points[3], 1],
    [START_DELAY_MS + 3 * SEGMENT_MS + HOLD_MS, points[3], 1],
    [TOTAL_MS, points[3], 0],
  ];
  return stops.map(([ms, p, opacity]) => ({ offset: at(ms), transform: move(p), opacity, easing: EASE }));
}

export function playTrace() {
  const trace = document.querySelector('.trace');
  const track = trace?.querySelector('.trace-track');
  const dot = trace?.querySelector('.trace-dot');
  if (!trace || !track || !dot) return;
  clearRun(trace);
  if (window.matchMedia(REDUCED_MOTION).matches) {
    completeRun(trace);
    return;
  }
  const nodes = [...track.querySelectorAll(':scope > .node')];
  const finish = () => completeRun(trace);
  animation = dot.animate(buildKeyframes(nodeCentres(track)), { duration: TOTAL_MS, fill: 'forwards' });
  nodes.forEach((node, i) => {
    timers.push(setTimeout(() => node.classList.add('is-active'), START_DELAY_MS + i * SEGMENT_MS));
  });
  timers.push(setTimeout(finish, TOTAL_MS));
  onResize = finish;
  window.addEventListener('resize', onResize);
}

export function initTrace() {
  document.querySelector('.trace-replay')?.addEventListener('click', playTrace);
  document.fonts.ready.then(playTrace);
}
