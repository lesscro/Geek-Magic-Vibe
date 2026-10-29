// GeekMagic backoffice: vanilla ES module, no build step.
// i18n: English is the source language; <lang>.json maps English text to its translation.
const LANG = ((await (await fetch('/api/config')).json()).language) || 'en';
const LOCALE = LANG === 'fr' ? 'fr-FR' : 'en-US';
const DICT = LANG === 'en' ? {} : await (await fetch(`/i18n/${LANG}.json`)).json();
const t = (key, vars) => {
  let s = DICT[key] ?? key;
  for (const [k, v] of Object.entries(vars || {})) s = s.replaceAll(`{${k}}`, v);
  return s;
};
document.documentElement.lang = LANG;
document.querySelectorAll('[data-i18n]').forEach((el) => { el.textContent = t(el.dataset.i18n); });
document.querySelectorAll('[data-i18n-aria]').forEach((el) => el.setAttribute('aria-label', t(el.dataset.i18nAria)));
document.querySelectorAll('[data-i18n-title]').forEach((el) => el.setAttribute('title', t(el.dataset.i18nTitle)));

const $ = (s, el = document) => el.querySelector(s);

// replaceChildren ignores null/false (otherwise the DOM prints "null")
const _replaceChildren = Element.prototype.replaceChildren;
Element.prototype.replaceChildren = function (...kids) {
  return _replaceChildren.apply(this, kids.flat(9).filter((k) => k != null && k !== false));
};

/* ------------------------------------------------------------------ helpers */

const SVG_TAGS = new Set(['svg', 'circle', 'text', 'path', 'g', 'rect']);
function h(tag, attrs = {}, ...kids) {
  const isSvg = SVG_TAGS.has(tag);
  const el = isSvg ? document.createElementNS('http://www.w3.org/2000/svg', tag) : document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (isSvg && !k.startsWith('on')) el.setAttribute(k, v);
    else if (k === 'class') el.className = v;
    else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else if (k === 'html') el.innerHTML = v;
    else if (k in el && k !== 'list') el[k] = v;
    else el.setAttribute(k, v === true ? '' : v);
  }
  for (const kid of kids.flat(9)) {
    if (kid == null || kid === false) continue;
    el.append(kid.nodeType ? kid : document.createTextNode(kid));
  }
  return el;
}
const svgIcon = (name, cls = '') => {
  const s = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  s.setAttribute('class', `ic ${cls}`);
  s.setAttribute('aria-hidden', 'true');
  s.innerHTML = `<use href="#i-${name}"/>`;
  return s;
};
const api = async (path, opts) => {
  const r = await fetch(path, opts);
  if (!r.ok) {
    let msg = r.statusText;
    try { msg = (await r.json()).detail || msg; } catch { /* body is not JSON */ }
    throw new Error(msg);
  }
  return r.json();
};
const debounce = (fn, ms = 300) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };
const clone = (o) => JSON.parse(JSON.stringify(o));
const fmtNum = (v, d) => v.toLocaleString(LOCALE, { minimumFractionDigits: d, maximumFractionDigits: d });
const fmtMo = (b) => fmtNum(b / 1048576, 1);
const fmtPrice = (v) => (v >= 1000 ? Math.round(v).toLocaleString(LOCALE) : fmtNum(v, v >= 1 ? 2 : 4));
const mins = (t) => { const [a, b] = t.split(':').map(Number); return a * 60 + b; };

const KIND = {
  clock:   { label: t('Clock'), one: t('Clock'), icon: 'clock',   color: '#ffc247', sub: t('HTC Sense style') },
  weather: { label: t('Weather'),   one: t('Weather'),   icon: 'weather', color: '#4f93ff', sub: t('Scene of the day') },
  crypto:  { label: t('Crypto'), one: 'Crypto',  icon: 'coin',    color: '#56e1c9', sub: t('One card per token') },
};
const SCENE_LABEL = {
  city: t('Lively city'), cafe: t('Café terrace'), market: t('Market'), bridge: t('Bridge and couple'), park: t('Park and walkers'),
  playground: t('Playground'), picnic: t('Picnic'), lake: t('Lake and angler'), mountains: t('Mountains'), farm: t('Farm'),
  harbor: t('Harbor and lighthouse'), beach: t('Beach'),
};
const MOMENTS = [['AURORE', t('Dawn')], ['MATIN', t('Morning')], ['APRES-MIDI', t('Afternoon')], ['CREPUSCULE', t('Dusk')], ['NUIT', t('Night')]];
const CONDS = [['SUN', t('Sunny')], ['PARTLY', t('Partly cloudy')], ['CLOUD', t('Overcast')], ['RAIN', t('Rain')], ['STORM', t('Storm')], ['SNOW', t('Snow')], ['FOG', t('Fog')]];
const SEASONS = [['SPRING', t('Spring')], ['SUMMER', t('Summer')], ['AUTUMN', t('Autumn')], ['WINTER', t('Winter')]];
const EFFECT_LABEL = { random: t('Random'), fade: t('Fade'), slide_left: t('Slide left'), slide_right: t('Slide right'), slide_up: t('Slide up'), slide_down: t('Slide down'), zoom: 'Zoom', wipe: t('Wipe'), dissolve: t('Dissolve'), iris: 'Iris' };
const ZONES = ['Europe/Paris', 'Europe/London', 'Europe/Brussels', 'Europe/Zurich', 'Europe/Madrid', 'Europe/Lisbon', 'Atlantic/Reykjavik', 'America/New_York', 'America/Montreal', 'America/Los_Angeles', 'America/Sao_Paulo', 'Africa/Casablanca', 'Asia/Dubai', 'Asia/Tokyo', 'Australia/Sydney', 'Pacific/Noumea', 'Indian/Reunion'];

/* ------------------------------------------------------------------- state */

const state = {
  cfg: null, saved: '', status: null, meta: null, route: 'overview',
  sel: { overview: null, crypto: null, weather: { loc: null, scene: null, moment: null, cond: null, season: null, temp: null } },
  nonce: Date.now(),
};
const dirty = () => JSON.stringify(state.cfg) !== state.saved;

function planOf(cfg) {
  const out = []; let pos = 1;
  for (const kind of cfg.schedule.order) {
    if (!cfg.schedule[kind].enabled) continue;
    let items = [];
    if (kind === 'clock') items = [{ key: 'clock', label: t('Clock') }];
    if (kind === 'weather') items = cfg.weather.locations.filter((l) => l.enabled).map((l) => ({ key: l.id, label: l.city }));
    if (kind === 'crypto') items = cfg.crypto.tokens.filter((t) => t.enabled).map((t) => ({ key: t.pair, label: t.pair.split('/')[0] }));
    for (const it of items) out.push({ kind, ...it, pos: pos++ });
  }
  return out;
}

function previewUrl(e, extra = {}) {
  const q = new URLSearchParams(extra);
  if (e.kind === 'crypto') { q.set('pair', e.key); return `/api/preview/crypto?${q}`; }
  if (e.kind === 'weather') { q.set('loc', e.key); return `/api/preview/weather?${q}`; }
  return `/api/preview/clock?${q}`;
}

/* ----------------------------------------------------------------- toasts */

let snackTimer;
function snack(msg, { err = false, actions = [], ms = 4200 } = {}) {
  const el = $('#snack');
  el.className = `snack show${err ? ' err' : ''}`;
  el.replaceChildren(h('span', {}, msg), ...actions.map((a) => h('button', { class: `btn ${a.ghost ? 'btn-ghost' : ''}`, type: 'button', onclick: a.run }, a.label)));
  clearTimeout(snackTimer);
  if (ms) snackTimer = setTimeout(() => { if (!dirty()) el.classList.remove('show'); else syncDirtyBar(); }, ms);
}
function syncDirtyBar() {
  if (dirty()) {
    snack(t('Unsaved changes'), {
      ms: 0,
      actions: [
        { label: t('Cancel'), ghost: true, run: () => { state.cfg = JSON.parse(state.saved); touch(true); } },
        { label: t('Save'), run: save },
      ],
    });
  } else if ($('#snack .btn-ghost')) $('#snack').classList.remove('show');
}
async function save() {
  try {
    state.cfg = await api('/api/config', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(state.cfg) });
    state.saved = JSON.stringify(state.cfg);
    state.nonce = Date.now();
    touch(true);
    snack(t('Configuration saved'), { actions: [{ label: t('Send to screen'), run: () => sendNow() }], ms: 6000 });
    refreshStatus();
  } catch (e) { snack(e.message, { err: true, ms: 6000 }); }
}

/* ---------------------------------------------------------------- send */

async function sendNow(kinds) {
  if (dirty()) await save();
  const sheet = $('#sheet');
  sheet.hidden = false;
  const log = h('pre', {}, t('Preparing…'));
  const bar = h('div', { class: 'bar' }, h('i'));
  sheet.replaceChildren(h('div', { class: 'row' }, h('div', { class: 'grow' }, h('h3', {}, t('Sending to the screen')), h('p', { class: 'faint' }, t('Generating the GIFs then transferring, allow about a minute'))), h('button', { class: 'icon-btn', type: 'button', 'aria-label': t('Close'), onclick: () => { sheet.hidden = true; } }, svgIcon('x'))), bar, log);
  try {
    await api('/api/send', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(kinds ? { kinds } : {}) });
  } catch (e) { log.textContent = e.message; bar.classList.add('done'); return; }
  const timer = setInterval(async () => {
    const st = await api('/api/status');
    log.textContent = (st.send.log || []).join('\n') || t('Preparing…');
    log.scrollTop = log.scrollHeight;
    if (!st.send.running) {
      clearInterval(timer);
      bar.classList.add('done');
      state.status = st; renderChrome();
      snack(st.send.ok ? t('The screen is up to date') : t('Sending failed, see the details'), { err: !st.send.ok });
      if (st.send.ok) setTimeout(() => { sheet.hidden = true; }, 3500);
    }
  }, 900);
}

/* -------------------------------------------------------------- components */

function sw(checked, onChange, label) {
  const input = h('input', { type: 'checkbox', checked, 'aria-label': label, onchange: (e) => onChange(e.target.checked) });
  return h('span', { class: 'switch' }, input, h('i'));
}
function range({ label, min, max, step = 1, value, fmt = (v) => v, onInput }) {
  const out = h('b', {}, fmt(value));
  const inp = h('input', { type: 'range', min, max, step, value, 'aria-label': label });
  const fill = () => inp.style.setProperty('--fill', `${((inp.value - min) / (max - min)) * 100}%`);
  fill();
  inp.addEventListener('input', () => { out.textContent = fmt(+inp.value); fill(); onInput(+inp.value); });
  return h('div', { class: 'range' }, h('div', { class: 'range-top' }, h('span', { class: 'label' }, label), out), inp);
}
function chips(options, current, onPick, { allowNone = false } = {}) {
  return h('div', { class: 'chips', role: 'group' }, options.map(([v, l]) => h('button', {
    class: 'chip', type: 'button', 'aria-pressed': String(current === v),
    onclick: () => onPick(allowNone && current === v ? null : v),
  }, current === v ? svgIcon('check') : null, l)));
}
function bezel(src, { alt, replay, loading } = {}) {
  const img = h('img', { src, alt, width: 240, height: 240 });
  const screen = h('div', { class: 'screen loading' }, img, h('div', { class: 'busy' }, t('Generating…')));
  img.addEventListener('load', () => screen.classList.remove('loading'));
  img.addEventListener('error', () => { screen.classList.remove('loading'); });
  const el = h('div', { class: 'bezel' }, screen);
  el.setImage = (s) => { screen.classList.add('loading'); img.src = s; };
  return el;
}
function placeSearch({ placeholder, fetcher, render, onPick, min = 2 }) {
  const input = h('input', { class: 'input', type: 'search', placeholder, autocomplete: 'off', 'aria-label': placeholder });
  const pop = h('div', { class: 'pop', hidden: true });
  const wrap = h('div', { class: 'search' }, svgIcon('search', 'ic-s'), input, pop);
  const run = debounce(async () => {
    const q = input.value.trim();
    if (q.length < min) { pop.hidden = true; return; }
    try {
      const res = await fetcher(q);
      pop.replaceChildren(...(res.length ? res.map((r) => h('button', { type: 'button', onclick: () => { onPick(r); input.value = ''; pop.hidden = true; } }, render(r))) : [h('div', { class: 'empty' }, t('No results'))]));
      pop.hidden = false;
    } catch (e) { pop.replaceChildren(h('div', { class: 'empty' }, e.message)); pop.hidden = false; }
  }, 280);
  input.addEventListener('input', run);
  input.addEventListener('keydown', (e) => { if (e.key === 'Escape') pop.hidden = true; });
  document.addEventListener('click', (e) => { if (!wrap.contains(e.target)) pop.hidden = true; });
  return wrap;
}

function sortable(container, { itemSel, gripSel, onMove }) {
  container.querySelectorAll(gripSel).forEach((grip) => {
    grip.addEventListener('pointerdown', (ev) => {
      const item = grip.closest(itemSel);
      const items = [...container.querySelectorAll(itemSel)];
      const from = items.indexOf(item);
      const rects = items.map((i) => i.getBoundingClientRect());
      const startY = ev.clientY;
      grip.setPointerCapture(ev.pointerId);
      item.classList.add('drag');
      const move = (e) => { item.style.transform = `translateY(${e.clientY - startY}px) scale(1.015)`; };
      const up = (e) => {
        grip.removeEventListener('pointermove', move); grip.removeEventListener('pointerup', up);
        item.classList.remove('drag'); item.style.transform = '';
        const y = e.clientY;
        let to = rects.findIndex((r) => y < r.top + r.height / 2);
        if (to === -1) to = items.length - 1;
        if (to !== from) onMove(from, to);
      };
      grip.addEventListener('pointermove', move); grip.addEventListener('pointerup', up);
    });
  });
}
const moveItem = (arr, from, to) => { const [x] = arr.splice(from, 1); arr.splice(to, 0, x); };

/* schedule: 24 h timeline + time slot editor */
function segs(slots) {
  const out = [];
  for (const [a, b] of slots) {
    const s = mins(a), e = mins(b);
    if (s < e) out.push([s, e]); else { out.push([s, 1440]); out.push([0, e]); }
  }
  return out;
}
function timeline(kinds = state.cfg.schedule.order) {
  const now = state.status ? new Date(state.status.now) : new Date();
  const nowMin = now.getHours() * 60 + now.getMinutes();
  const rows = kinds.map((k) => {
    const sc = state.cfg.schedule[k];
    const track = h('div', { class: 'tl-track', role: 'img', 'aria-label': `${KIND[k].label}: ${sc.enabled ? sc.slots.map((s) => s.join(t(' to '))).join(', ') : t('disabled')}` },
      sc.enabled ? segs(sc.slots).map(([s, e]) => h('i', { class: 'tl-seg', style: `left:${(s / 1440) * 100}%;width:${((e - s) / 1440) * 100}%;--c:${KIND[k].color}` })) : null,
      h('i', { class: 'tl-now', style: `left:${(nowMin / 1440) * 100}%` }));
    return h('div', { class: 'tl-row' }, h('span', { class: 'muted' }, KIND[k].label), track);
  });
  return h('div', {}, h('div', { class: 'tl' }, rows),
    h('div', { class: 'tl-ticks' }, h('span'), h('div', {}, ['0:00', '6:00', '12:00', '18:00', '24:00'].map((t) => h('span', {}, t)))));
}
function slotEditor(kind) {
  const sc = state.cfg.schedule[kind];
  const wrap = h('div', { class: 'stack' });
  const draw = () => {
    wrap.replaceChildren(
      h('div', {}, sc.slots.map((s, i) => h('div', { class: 'slot' },
        h('input', { class: 'input', type: 'time', value: s[0], 'aria-label': t('Start'), onchange: (e) => { s[0] = e.target.value || '00:00'; touch(); } }),
        h('span', {}, t('to')),
        h('input', { class: 'input', type: 'time', value: s[1] === '24:00' ? '23:59' : s[1], 'aria-label': t('End'), onchange: (e) => { s[1] = e.target.value || '00:00'; touch(); } }),
        h('button', { class: 'icon-btn danger', type: 'button', 'aria-label': t('Delete this time slot'), disabled: sc.slots.length < 2, onclick: () => { sc.slots.splice(i, 1); touch(true); } }, svgIcon('trash')))),
      ),
      h('div', { class: 'chips' },
        h('button', { class: 'chip', type: 'button', onclick: () => { sc.slots.push(['18:00', '23:00']); touch(true); } }, svgIcon('plus'), t('Add a time slot')),
        [[t('All day'), [['00:00', '24:00']]], [t('Daytime 7:00 to 22:00'), [['07:00', '22:00']]], [t('Evening'), [['18:00', '23:30']]]].map(([l, v]) =>
          h('button', { class: 'chip', type: 'button', onclick: () => { sc.slots = clone(v); touch(true); } }, l))));
  };
  draw();
  return wrap;
}

/* ---------------------------------------------------------- avatars & lists */

const hue = (s) => [...s].reduce((a, c) => (a * 31 + c.charCodeAt(0)) % 360, 7);
function coinAvatar(sym, ring) {
  const hh = hue(sym);
  return h('span', { class: 'avatar', style: `background:linear-gradient(140deg,hsl(${hh} 85% 62%),hsl(${(hh + 40) % 360} 80% 50%));--ring:${ring || '#56e1c9'}` }, sym.slice(0, 4));
}
function entryAvatar(e) {
  if (e.kind === 'crypto') return coinAvatar(e.label, KIND.crypto.color);
  const url = e.kind === 'weather' ? `/api/preview/weather?loc=${encodeURIComponent(e.key)}&fmt=png&frame=6&n=${state.nonce}` : `/api/preview/clock?fmt=png&n=${Math.floor(state.nonce / 60000)}`;
  return h('span', { class: 'avatar', style: `--ring:${KIND[e.kind].color}` }, h('img', { src: url, alt: '', loading: 'lazy' }));
}

/* ---------------------------------------------------------- side panel */

function renderSide() {
  const cfg = state.cfg, plan = planOf(cfg), order = cfg.schedule.order, st = state.status;
  const wrap = h('div', { class: 'enter' });
  wrap.append(
    h('h2', {}, 'Rotation'),
    h('p', { class: 'sub' }, t('The order in which the screen cycles through its cards.')),
    h('div', { style: 'margin-top:22px' }, range({
      label: t('Duration per card'), min: 4, max: 60, value: cfg.crypto.cycle, fmt: (v) => `${v} s`,
      onInput: (v) => { cfg.crypto.cycle = v; touch(); },
    })),
  );
  const list = h('div', { class: 'list', style: 'margin-top:26px' });
  order.forEach((kind, gi) => {
    const items = plan.filter((p) => p.kind === kind);
    const active = st ? st.active[kind] : true;
    const on = cfg.schedule[kind].enabled;
    list.append(h('section', { class: `item${on ? '' : ' off'}`, 'data-g': kind, style: 'align-items:flex-start;flex-wrap:wrap' },
      h('button', { class: 'grip', type: 'button', 'aria-label': t('Move {name}', { name: KIND[kind].label }) }, svgIcon('grip', 'ic-fill')),
      h('div', { class: 'grow' },
        h('div', { class: 'row' },
          h('span', { class: 'faint', style: 'color:var(--amber);font-family:var(--font-display);font-weight:700' }, items.length ? String(items[0].pos).padStart(2, '0') : '--'),
          h('b', {}, KIND[kind].label),
          !on ? h('span', { class: 'pill' }, t('Disabled')) : active ? h('span', { class: 'pill ok' }, t('Shown')) : h('span', { class: 'pill warn' }, t('Outside time slot'))),
        h('small', {}, on ? `${items.length} ${t(items.length > 1 ? 'cards' : 'card')} · ${KIND[kind].sub}` : t('Removed from rotation'))),
      h('div', { class: 'row', style: 'gap:2px' },
        h('button', { class: 'icon-btn', type: 'button', 'aria-label': t('Move {name} up', { name: KIND[kind].label }), disabled: gi === 0, onclick: () => { moveItem(order, gi, gi - 1); touch(true); } }, svgIcon('up')),
        h('button', { class: 'icon-btn', type: 'button', 'aria-label': t('Move {name} down', { name: KIND[kind].label }), disabled: gi === order.length - 1, onclick: () => { moveItem(order, gi, gi + 1); touch(true); } }, svgIcon('down'))),
      items.length ? h('ul', { class: `seq${on && active ? '' : ' dim'}`, style: 'flex-basis:100%;padding-left:36px' }, items.map((e) =>
        h('li', {}, entryAvatar(e), h('span', {}, e.label), h('span', { class: 'pos' }, String(e.pos).padStart(2, '0'))))) : null));
  });
  wrap.append(list);
  sortable(list, { itemSel: '[data-g]', gripSel: '.grip', onMove: (f, t) => { moveItem(order, f, t); touch(true); } });
  $('#side').replaceChildren(wrap);
}

/* ------------------------------------------------------------------ pages */

const PAGES = {
  overview: { eyebrow: 'Cockpit', title: t('Overview') },
  crypto: { eyebrow: t('Markets'), title: t('Crypto') },
  weather: { eyebrow: t('Sky and scenery'), title: t('Weather') },
  clock: { eyebrow: t('HTC Sense style'), title: t('Clock') },
  screen: { eyebrow: t('Hardware'), title: t('Screen and schedule') },
};

function pageOverview() {
  const cfg = state.cfg, st = state.status, plan = planOf(cfg);
  const dev = st?.device;
  const nextIn = st?.last_refresh ? Math.max(0, Math.round(cfg.device.refresh_minutes - (Date.now() / 1000 - st.last_refresh) / 60)) : null;
  const stat = (cls, big, small, label) => h('div', { class: `stat ${cls}` }, h('b', {}, big, small ? h('small', {}, small) : null), h('span', {}, label));
  const sel = plan.find((p) => `${p.kind}:${p.key}` === state.sel.overview) || plan[0];
  const view = h('div', { class: 'enter' });
  view.append(h('div', { class: 'stats' },
    stat(dev ? (dev.online ? 'ok' : 'ko') : '', dev ? (dev.online ? t('Online') : t('Offline')) : '…', '', t('Screen {ip}', { ip: cfg.device.ip })),
    stat('', dev?.free ? fmtMo(dev.free) : '–', t(' MB'), t('Free memory')),
    stat('', String(plan.length), '', t('Cards in rotation')),
    stat('', nextIn == null ? '–' : String(nextIn), ' min', t('Next refresh'))));
  const left = h('div', { class: 'stack' },
    h('section', { class: 'card' }, h('div', { class: 'card-head' }, h('div', {}, h('h2', {}, t('Daily schedule')), h('p', { class: 'faint' }, t('When each card is visible on the screen'))), h('a', { class: 'btn btn-ghost btn-s', href: '#/screen' }, t('Adjust'))), timeline()),
    memoryCard());
  let prev;
  const right = h('section', { class: 'card sticky' },
    h('div', { class: 'card-head' }, h('div', {}, h('h2', {}, t('On the screen')), h('p', { class: 'faint' }, t('Faithful preview, pixel for pixel')))),
    prev = sel ? bezel(previewUrl(sel, { n: state.nonce }), { alt: t('Preview {name}', { name: sel.label }) }) : h('div', { class: 'empty-state' }, h('b', {}, t('No card')), t('Enable a card to see it here.')),
    h('div', { class: 'preview-actions' }, h('div', { class: 'chips' }, plan.slice(0, 12).map((p) => h('button', {
      class: 'chip', type: 'button', 'aria-pressed': String(sel && p.kind === sel.kind && p.key === sel.key),
      onclick: () => { state.sel.overview = `${p.kind}:${p.key}`; renderView(); },
    }, p.label)))));
  view.append(h('div', { class: 'grid-2' }, left, right));
  return view;
}

function memoryCard() {
  const dev = state.status?.device;
  const total = dev?.total || 1, free = dev?.free || 0, used = total - free;
  const C = 2 * Math.PI * 64;
  const frac = Math.min(1, used / total);
  const donut = h('svg', { class: 'donut', viewBox: '0 0 168 168', role: 'img', 'aria-label': t('Memory used: {pct}%', { pct: Math.round(frac * 100) }) },
    h('circle', { class: 'bg', cx: 84, cy: 84, r: 64 }),
    h('circle', { class: 'fg', cx: 84, cy: 84, r: 64, 'stroke-dasharray': `0 ${C}` }),
    h('text', { x: 84, y: 90 }, dev?.online ? `${Math.round(frac * 100)}%` : '–'),
    h('text', { class: 's', x: 84, y: 112 }, t('used')));
  requestAnimationFrame(() => $('.fg', donut)?.setAttribute('stroke-dasharray', `${C * frac} ${C}`));
  const files = (dev?.files || []);
  return h('section', { class: 'card' },
    h('div', { class: 'card-head' }, h('div', {}, h('h2', {}, t('Screen memory')), h('p', { class: 'faint' }, t('The GIFs stored on the GeekMagic')))),
    h('div', { class: 'row', style: 'gap:28px;align-items:center;flex-wrap:wrap' }, donut,
      h('div', { class: 'grow' },
        h('p', {}, h('b', { style: 'font-family:var(--font-display);font-size:24px' }, dev?.online ? `${fmtMo(free)} ${t('MB')}`: '–'), h('span', { class: 'muted' }, dev?.online ? t(' free of {total} MB', { total: fmtMo(total) }) : t(' screen unreachable'))),
        h('div', { class: 'files', style: 'margin-top:14px' }, files.map((f) => h('span', { class: 'pill' }, f))))));
}

/* --- crypto */
function pageCrypto() {
  const cfg = state.cfg, toks = cfg.crypto.tokens;
  if (!state.sel.crypto || !toks.find((t) => t.pair === state.sel.crypto)) state.sel.crypto = toks[0]?.pair || null;
  const view = h('div', { class: 'enter' });
  const quotes = {};
  const list = h('div', { class: 'list' });
  const drawList = () => {
    list.replaceChildren(...toks.map((tok, i) => {
      const sym = tok.pair.split('/')[0];
      const q = quotes[tok.pair];
      return h('div', { class: `item${tok.enabled ? '' : ' off'}${state.sel.crypto === tok.pair ? ' sel' : ''}`, 'data-i': i },
        h('button', { class: 'grip', type: 'button', 'aria-label': t('Move {name}', { name: sym }) }, svgIcon('grip', 'ic-fill')),
        coinAvatar(sym, 'var(--teal)'),
        h('button', { class: 'grow', type: 'button', style: 'background:none;border:0;text-align:left;padding:0;color:inherit', onclick: () => { state.sel.crypto = tok.pair; renderView(); } },
          h('b', {}, sym, h('span', { class: 'faint' }, ' / USDT')),
          h('small', { class: q ? (q.change >= 0 ? 'up' : 'down') : '' }, q ? `${fmtPrice(q.price)} $ · ${q.change >= 0 ? '+' : ''}${fmtNum(q.change, 2)}%` : t('Loading price…'))),
        sw(tok.enabled, (v) => { tok.enabled = v; touch(true); }, t('Show {name}', { name: sym })),
        h('button', { class: 'icon-btn danger', type: 'button', 'aria-label': t('Remove {name}', { name: sym }), onclick: () => { toks.splice(i, 1); touch(true); } }, svgIcon('trash')));
    }), toks.length ? null : h('div', { class: 'empty-state' }, h('b', {}, t('No tokens')), t('Add one with the search above.')));
    sortable(list, { itemSel: '.item', gripSel: '.grip', onMove: (f, t) => { moveItem(toks, f, t); touch(true); } });
  };
  drawList();
  api(`/api/crypto/quotes?pairs=${encodeURIComponent(toks.map((t) => t.pair).join(','))}`).then((q) => { Object.assign(quotes, q); drawList(); }).catch(() => {});
  const add = placeSearch({
    placeholder: t('Add a token: BTC, SOL, LINK…'), min: 1,
    fetcher: (q) => api(`/api/crypto/search?q=${encodeURIComponent(q)}`),
    render: (r) => [h('b', {}, r.symbol), h('span', { class: 'muted' }, `${fmtPrice(r.price)} $`)],
    onPick: (r) => {
      if (toks.length >= 12) return snack(t('12 tokens maximum, the screen memory is limited'), { err: true });
      if (toks.some((t) => t.pair === r.pair)) return snack(t('{symbol} is already in the list', { symbol: r.symbol }));
      toks.push({ pair: r.pair, enabled: true }); state.sel.crypto = r.pair; touch(true);
    },
  });
  const cur = state.sel.crypto && { kind: 'crypto', key: state.sel.crypto, label: state.sel.crypto.split('/')[0] };
  view.append(h('div', { class: 'grid-2' },
    h('div', { class: 'stack' },
      h('section', { class: 'card' }, h('div', { class: 'card-head' }, h('div', {}, h('h2', {}, t('Displayed tokens')), h('p', { class: 'faint' }, t('{n} active of {total}. Drag to reorder.', { n: toks.filter((x) => x.enabled).length, total: toks.length })))), add, h('div', { style: 'height:16px' }), list),
      h('section', { class: 'card' }, h('div', { class: 'card-head' }, h('div', {}, h('h2', {}, t('Display time slot')), h('p', { class: 'faint' }, t('Crypto cards leave the screen outside these hours')))),
        h('div', { class: 'row', style: 'margin-bottom:16px' }, sw(cfg.schedule.crypto.enabled, (v) => { cfg.schedule.crypto.enabled = v; touch(true); }, t('Show crypto cards')), h('span', {}, t('Show crypto cards'))), slotEditor('crypto'))),
    h('section', { class: 'card sticky' }, h('div', { class: 'card-head' }, h('div', {}, h('h2', {}, cur ? cur.label : t('Preview')), h('p', { class: 'faint' }, t('Card as sent')))),
      cur ? bezel(previewUrl(cur, { n: state.nonce }), { alt: t('Preview {name}', { name: cur.label }) }) : h('div', { class: 'empty-state' }, t('Select a token')))));
  return view;
}

/* --- weather */
function pageWeather() {
  const cfg = state.cfg, locs = cfg.weather.locations, W = state.sel.weather;
  if (!W.loc || !locs.find((l) => l.id === W.loc)) W.loc = locs[0]?.id || null;
  const view = h('div', { class: 'enter' });
  const simParams = (extra = {}) => {
    const q = new URLSearchParams({ loc: W.loc || '', ...extra });
    for (const k of ['moment', 'cond', 'season']) if (W[k]) q.set(k, W[k]);
    if (W.temp != null) q.set('temp', W.temp);
    return q;
  };
  let prev;
  const refresh = debounce(() => prev?.setImage(`/api/preview/weather?${simParams({ scene: W.scene || '' })}`), 250);
  const locList = h('div', { class: 'list' }, locs.map((l, i) => h('div', { class: `item${l.enabled ? '' : ' off'}${W.loc === l.id ? ' sel' : ''}`, style: 'flex-wrap:wrap;padding-left:14px' },
    h('span', { class: 'avatar', style: 'background:var(--blue-soft);color:var(--blue);--ring:var(--blue)' }, svgIcon('pin')),
    h('button', { class: 'grow', type: 'button', style: 'background:none;border:0;text-align:left;padding:0;color:inherit', onclick: () => { W.loc = l.id; renderView(); } },
      h('b', {}, l.city), h('small', {}, `${l.lat.toFixed(2)}, ${l.lon.toFixed(2)} · ${l.timezone}`)),
    sw(l.enabled, (v) => { l.enabled = v; touch(true); }, t('Show {name}', { name: l.city })),
    h('button', { class: 'icon-btn danger', type: 'button', 'aria-label': t('Remove {name}', { name: l.city }), disabled: locs.length < 2, onclick: () => { locs.splice(i, 1); touch(true); } }, svgIcon('trash')),
    h('select', { class: 'input', style: 'flex:1 1 100%;min-height:44px', 'aria-label': t('Scene for {name}', { name: l.city }), onchange: (e) => { l.scene = e.target.value; touch(true); } },
      h('option', { value: 'auto', selected: l.scene === 'auto' }, t('Scene of the day (automatic)')), state.meta.scenes.map((s) => h('option', { value: s, selected: l.scene === s }, t('Always: {scene}', { scene: SCENE_LABEL[s] })))))));
  const addLoc = locs.length >= state.meta.max_locations
    ? h('p', { class: 'faint' }, t('{n} places maximum: each place adds a card of about 200 KB on the screen.', { n: state.meta.max_locations }))
    : placeSearch({
      placeholder: t('Add a place: Paris, Lyon…'),
      fetcher: (q) => api(`/api/geocode?q=${encodeURIComponent(q)}`),
      render: (r) => [h('b', {}, r.city), h('span', { class: 'muted' }, [r.region, r.country].filter(Boolean).join(', '))],
      onPick: (r) => { locs.push({ id: r.city.toLowerCase().replace(/[^a-z0-9]/g, '').slice(0, 10) || 'lieu', city: r.city, lat: r.lat, lon: r.lon, timezone: r.timezone, enabled: true, scene: 'auto' }); touch(true); },
    });
  const sceneGrid = h('div', { class: 'scenes' }, state.meta.scenes.map((s) => {
    const on = cfg.weather.scenes_enabled.includes(s);
    const q = new URLSearchParams({ scene: s, fmt: 'png', frame: 6, sample: 'true', bare: 'true', loc: W.loc || '', moment: W.moment || 'APRES-MIDI', cond: W.cond || 'SUN' });
    return h('div', { class: `scene${on ? '' : ' dim'}`, 'aria-pressed': String(W.scene === s) },
      h('button', { type: 'button', style: 'display:block;width:100%;border:0;padding:0;background:none;text-align:left', 'aria-label': t('Preview {name}', { name: SCENE_LABEL[s] }), onclick: () => { W.scene = W.scene === s ? null : s; renderView(); } },
        h('img', { src: `/api/preview/weather?${q}`, alt: '', loading: 'lazy', width: 240, height: 240 }),
        h('span', { class: 'cap' }, SCENE_LABEL[s])),
      h('button', { class: 'tick', type: 'button', role: 'switch', 'aria-checked': String(on), 'aria-label': t('Use {name}', { name: SCENE_LABEL[s] }), title: on ? t('In rotation') : t('Excluded'),
        onclick: () => { const arr = cfg.weather.scenes_enabled; const i = arr.indexOf(s); if (i >= 0) { if (arr.length > 1) arr.splice(i, 1); else return snack(t('Keep at least one scene'), { err: true }); } else arr.push(s); touch(true); } }, svgIcon(on ? 'check' : 'eye', 'ic-s')));
  }));
  const sim = h('section', { class: 'card' },
    h('div', { class: 'card-head' }, h('div', {}, h('h2', {}, t('Simulator')), h('p', { class: 'faint' }, t('See the scene at any hour, in any weather. Nothing is saved.'))),
      h('button', { class: 'btn btn-ghost btn-s', type: 'button', onclick: () => { Object.assign(W, { moment: null, cond: null, season: null, temp: null, scene: null }); renderView(); } }, svgIcon('refresh', 'ic-s'), t('Live'))),
    h('div', { class: 'stack' },
      h('div', { class: 'field' }, h('span', { class: 'label' }, t('Time of day')), chips(MOMENTS, W.moment, (v) => { W.moment = v; renderView(); }, { allowNone: true })),
      h('div', { class: 'field' }, h('span', { class: 'label' }, 'Condition'), chips(CONDS, W.cond, (v) => { W.cond = v; renderView(); }, { allowNone: true })),
      h('div', { class: 'field' }, h('span', { class: 'label' }, t('Season')), chips(SEASONS, W.season, (v) => { W.season = v; renderView(); }, { allowNone: true })),
      range({ label: t('Temperature'), min: -10, max: 40, value: W.temp ?? 21, fmt: (v) => `${v}°`, onInput: (v) => { W.temp = v; refresh(); } })));
  const cur = locs.find((l) => l.id === W.loc);
  view.append(h('div', { class: 'grid-2' },
    h('div', { class: 'stack' },
      h('section', { class: 'card' }, h('div', { class: 'card-head' }, h('div', {}, h('h2', {}, t('Places')), h('p', { class: 'faint' }, t('Each active place becomes a card with its live weather')))), addLoc, h('div', { style: 'height:16px' }), locList),
      sim,
      h('section', { class: 'card' }, h('div', { class: 'card-head' }, h('div', {}, h('h2', {}, t('Display time slot')))),
        h('div', { class: 'row', style: 'margin-bottom:16px' }, sw(cfg.schedule.weather.enabled, (v) => { cfg.schedule.weather.enabled = v; touch(true); }, t('Show weather')), h('span', {}, t('Show weather'))), slotEditor('weather'))),
    h('section', { class: 'card sticky' }, h('div', { class: 'card-head' }, h('div', {}, h('h2', {}, cur ? cur.city : t('Preview')), h('p', { class: 'faint' }, W.scene ? t('Scene: {scene}', { scene: SCENE_LABEL[W.scene] }) : t('Scene of the day')))),
      cur ? (prev = bezel(`/api/preview/weather?${simParams({ scene: W.scene || '', n: state.nonce })}`, { alt: t('Weather preview {name}', { name: cur.city }) })) : h('div', { class: 'empty-state' }, t('Add a place')),
      locs.length > 1 ? h('div', { class: 'preview-actions' }, h('div', { class: 'chips' }, locs.map((l) => h('button', { class: 'chip', type: 'button', 'aria-pressed': String(l.id === W.loc), onclick: () => { W.loc = l.id; renderView(); } }, l.city)))) : null)));
  view.append(h('section', { class: 'card', style: 'margin-top:24px' }, h('div', { class: 'card-head' }, h('div', {}, h('h2', {}, t('Everyday scenes')), h('p', { class: 'faint' }, t('One scene per day among the checked ones, chosen by the weather. Tap a thumbnail to see it in the preview, tick it to include it.')))), sceneGrid));
  return view;
}

/* --- clock */
function pageClock() {
  const cfg = state.cfg, c = cfg.clock;
  const view = h('div', { class: 'enter' });
  let prev;
  const url = () => `/api/preview/clock?${new URLSearchParams({ effect: c.effect, tz: c.timezone, show_weather: c.show_weather, loc: c.location, ns: c.night_start, ne: c.night_end, n: Date.now() })}`;
  const replay = debounce(() => prev?.setImage(url()), 350);
  const hourLabel = (v) => `${String(v).padStart(2, '0')}:00`;
  view.append(h('div', { class: 'grid-2' },
    h('div', { class: 'stack' },
      h('section', { class: 'card' }, h('div', { class: 'card-head' }, h('div', {}, h('h2', {}, t('Display')), h('p', { class: 'faint' }, t('Flip tiles, date and weather like on an HTC Sense')))),
        h('div', { class: 'stack' },
          h('div', { class: 'field' }, h('label', { for: 'tz' }, t('Time zone')),
            h('select', { class: 'input', id: 'tz', onchange: (e) => { c.timezone = e.target.value; touch(); replay(); } }, [...new Set([c.timezone, ...ZONES])].map((z) => h('option', { value: z, selected: z === c.timezone }, z.replace('_', ' '))))),
          h('div', { class: 'row' }, sw(c.show_weather, (v) => { c.show_weather = v; touch(true); }, t('Weather under the clock')), h('div', { class: 'grow' }, h('b', {}, t('Weather under the clock')), h('p', { class: 'faint' }, t('Temperature and animated sky at the bottom of the card')))),
          c.show_weather ? h('div', { class: 'field' }, h('label', { for: 'cl' }, t('Weather place')), h('select', { class: 'input', id: 'cl', onchange: (e) => { c.location = e.target.value; touch(); replay(); } }, cfg.weather.locations.map((l) => h('option', { value: l.id, selected: l.id === c.location }, l.city)))) : null)),
      h('section', { class: 'card' }, h('div', { class: 'card-head' }, h('div', {}, h('h2', {}, t('Entry effect')), h('p', { class: 'faint' }, t('Played once when the card appears, then the time stays still')))),
        chips(state.meta.effects.map((e) => [e, EFFECT_LABEL[e]]), c.effect, (v) => { c.effect = v; touch(true); })),
      h('section', { class: 'card' }, h('div', { class: 'card-head' }, h('div', {}, h('h2', {}, t('Night mode')), h('p', { class: 'faint' }, t('Softer digits during these hours')))),
        h('div', { class: 'stack' },
          range({ label: t('Start'), min: 0, max: 23, value: c.night_start, fmt: hourLabel, onInput: (v) => { c.night_start = v; touch(); replay(); } }),
          range({ label: t('End'), min: 0, max: 23, value: c.night_end, fmt: hourLabel, onInput: (v) => { c.night_end = v; touch(); replay(); } }))),
      h('section', { class: 'card' }, h('div', { class: 'card-head' }, h('div', {}, h('h2', {}, t('Display time slot')))),
        h('div', { class: 'row', style: 'margin-bottom:16px' }, sw(cfg.schedule.clock.enabled, (v) => { cfg.schedule.clock.enabled = v; touch(true); }, t('Show clock')), h('span', {}, t('Show clock'))), slotEditor('clock'))),
    h('section', { class: 'card sticky' }, h('div', { class: 'card-head' }, h('div', {}, h('h2', {}, t('Preview')), h('p', { class: 'faint' }, t('Plays once, like on the screen')))),
      (prev = bezel(url(), { alt: t('Clock preview') })),
      h('div', { class: 'preview-actions' }, h('button', { class: 'btn btn-s', type: 'button', onclick: () => prev.setImage(url()) }, svgIcon('play', 'ic-s'), t('Replay'))))));
  return view;
}

/* --- screen & schedule */
function pageScreen() {
  const cfg = state.cfg, d = cfg.device;
  const view = h('div', { class: 'enter stack' });
  const result = h('div', { class: 'row', style: 'margin-top:14px;flex-wrap:wrap' });
  const ip = h('input', { class: 'input', id: 'ip', value: d.ip, inputmode: 'decimal', autocomplete: 'off', oninput: (e) => { d.ip = e.target.value.trim(); touch(); } });
  const test = async () => {
    result.replaceChildren(h('span', { class: 'pill' }, t('Testing…')));
    try {
      const r = await api('/api/device/test', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ip: d.ip }) });
      result.replaceChildren(r.online ? h('span', { class: 'pill ok' }, svgIcon('wifi', 'ic-s'), t('Screen reachable')) : h('span', { class: 'pill ko' }, svgIcon('alert', 'ic-s'), t('No response at this address')),
        r.online ? h('span', { class: 'pill' }, t('{n} MB free', { n: fmtMo(r.free) })) : null);
    } catch (e) { result.replaceChildren(h('span', { class: 'pill ko' }, e.message)); }
  };
  view.append(
    h('section', { class: 'card' }, h('div', { class: 'card-head' }, h('div', {}, h('h2', {}, t('Language')), h('p', { class: 'faint' }, t('Language of this interface and of the texts shown on the screen')))),
      chips([['en', 'English'], ['fr', 'Français']], cfg.language, async (v) => { cfg.language = v; await save(); location.reload(); })),
    h('section', { class: 'card' }, h('div', { class: 'card-head' }, h('div', {}, h('h2', {}, t('Connection')), h('p', { class: 'faint' }, t('Address of the screen on your network. If it changes, rerun the search: python scripts/find_device.py')))),
      h('div', { class: 'row', style: 'align-items:flex-end;flex-wrap:wrap' }, h('div', { class: 'field grow', style: 'max-width:320px' }, h('label', { for: 'ip' }, t('IP address')), ip), h('button', { class: 'btn', type: 'button', onclick: test }, svgIcon('wifi'), t('Test connection'))), result),
    h('section', { class: 'card' }, h('div', { class: 'card-head' }, h('div', {}, h('h2', {}, t('Pace')), h('p', { class: 'faint' }, t('How often prices and weather are refreshed. The clock updates every minute.')))),
      chips([[3, '3 min'], [5, '5 min'], [9, '9 min'], [15, '15 min'], [30, '30 min'], [60, '1 h']], d.refresh_minutes, (v) => { d.refresh_minutes = v; touch(true); }),
      h('p', { class: 'faint', style: 'margin-top:12px' }, t('The Windows task runs every 9 minutes: a slower pace is honored, a faster one is capped at 9 minutes.'))),
    h('section', { class: 'card' }, h('div', { class: 'card-head' }, h('div', {}, h('h2', {}, t('Cards and time slots')), h('p', { class: 'faint' }, t('Each card can have several time ranges')))), timeline(),
      h('div', { class: 'stack', style: 'margin-top:28px' }, state.cfg.schedule.order.map((k) => h('div', { class: 'item', style: 'align-items:flex-start;padding:18px;flex-direction:column' },
        h('div', { class: 'row', style: 'width:100%' }, h('span', { class: 'avatar', style: `background:${KIND[k].color}22;color:${KIND[k].color};--ring:${KIND[k].color}` }, svgIcon(KIND[k].icon)), h('div', { class: 'grow' }, h('b', {}, KIND[k].label), h('small', {}, KIND[k].sub)),
          sw(cfg.schedule[k].enabled, (v) => { cfg.schedule[k].enabled = v; touch(true); }, t('Show {name}', { name: KIND[k].label }))),
        h('div', { style: 'padding-left:62px;width:100%' }, slotEditor(k)))))),
    memoryCard());
  return view;
}

/* ----------------------------------------------------------------- routing */

function renderView() {
  const page = PAGES[state.route] || PAGES.overview;
  $('#page-title').textContent = page.title;
  $('#page-eyebrow').textContent = page.eyebrow;
  document.title = `${page.title} · GeekMagic`;
  document.querySelectorAll('.rail-btn').forEach((a) => { const on = a.dataset.route === state.route; a.classList.toggle('on', on); on ? a.setAttribute('aria-current', 'page') : a.removeAttribute('aria-current'); });
  const fn = { overview: pageOverview, crypto: pageCrypto, weather: pageWeather, clock: pageClock, screen: pageScreen }[state.route] || pageOverview;
  $('#view').replaceChildren(fn());
}
function renderChrome() {
  const dev = state.status?.device;
  const dot = $('#rail-dot');
  dot.className = `dot ${dev ? (dev.online ? 'ok' : 'ko') : ''}`;
  $('#rail-status').title = dev ? (dev.online ? t('Screen online ({ip})', { ip: dev.ip }) : t('Screen unreachable ({ip})', { ip: dev.ip })) : t('Unknown state');
}
function touch(structural = false) {
  syncDirtyBar();
  if (structural) { renderSide(); renderView(); } else renderSideSoft();
}
const renderSideSoft = debounce(renderSide, 400);

async function refreshStatus() {
  try {
    state.status = await api('/api/status');
    renderChrome();
    if (state.route === 'overview' || state.route === 'screen') { const y = scrollY; renderView(); scrollTo(0, y); }
    renderSide();
  } catch { /* server unavailable: retry later */ }
}
function route() {
  state.route = (location.hash.replace(/^#\/?/, '') || 'overview').split('?')[0];
  if (!PAGES[state.route]) state.route = 'overview';
  renderView();
  scrollTo(0, 0);
  $('#main').focus({ preventScroll: true });
}

async function boot() {
  try {
    [state.cfg, state.meta] = await Promise.all([api('/api/config'), api('/api/meta')]);
  } catch (e) {
    $('#view').replaceChildren(h('div', { class: 'card empty-state' }, h('b', {}, t('Server unreachable')), e.message));
    return;
  }
  state.saved = JSON.stringify(state.cfg);
  $('#send-btn').addEventListener('click', () => sendNow());
  addEventListener('hashchange', route);
  window.addEventListener('beforeunload', (e) => { if (dirty()) { e.preventDefault(); } });
  route(); renderSide();
  refreshStatus();
  setInterval(refreshStatus, 20000);
}
boot();
