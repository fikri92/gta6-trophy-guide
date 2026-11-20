/* Leonida Legend — GTA VI trophy companion.
   Plain ES module, no dependencies, no network: reads data/trophies.json from the same folder,
   keeps the earned set in localStorage, and renders everything with DOM calls. */

const STORAGE_KEY = 'leonida-legend:gta6-trophies:v1';
const DATA_URL = 'data/trophies.json';
const GRADES = ['platinum', 'gold', 'silver', 'bronze'];
const GRADE_RANK = { platinum: 0, gold: 1, silver: 2, bronze: 3 };
const KINDS = ['story', 'missable', 'collectibles', 'activities', 'online'];

const els = {
  earnedCount: document.getElementById('earned-count'),
  totalCount: document.getElementById('total-count'),
  pct: document.getElementById('pct'),
  bar: document.getElementById('bar'),
  barFill: document.getElementById('bar-fill'),
  missableLeft: document.getElementById('missable-left'),
  platinumNote: document.getElementById('platinum-note'),
  search: document.getElementById('search'),
  sort: document.getElementById('sort'),
  gradePills: document.getElementById('grade-pills'),
  kindPills: document.getElementById('kind-pills'),
  spoiler: document.getElementById('spoiler'),
  spoilerState: document.getElementById('spoiler-state'),
  stats: document.getElementById('stats'),
  list: document.getElementById('list'),
  empty: document.getElementById('empty'),
  emptyCopy: document.getElementById('empty-copy'),
  clearFilters: document.getElementById('clear-filters'),
  resultCount: document.getElementById('result-count'),
  resultMeta: document.getElementById('result-meta'),
  viewTitle: document.getElementById('view-title'),
  viewSub: document.getElementById('view-sub'),
  roadmap: document.getElementById('roadmap'),
  missableList: document.getElementById('missable-list'),
  exportBtn: document.getElementById('export'),
  importBtn: document.getElementById('import'),
  importFile: document.getElementById('import-file'),
  resetBtn: document.getElementById('reset'),
  resetDialog: document.getElementById('reset-dialog'),
  toast: document.getElementById('toast'),
  footMeta: document.getElementById('foot-meta'),
  panelChecklist: document.getElementById('panel-checklist'),
  panelRoadmap: document.getElementById('panel-roadmap'),
  panelMissable: document.getElementById('panel-missable'),
  tabs: [...document.querySelectorAll('.tab')],
};

const state = {
  doc: null,
  trophies: [],
  byId: new Map(),
  earned: new Set(),
  view: 'checklist',
  grade: 'all',
  kind: 'all',
  query: '',
  sort: 'stage',
  spoiler: true,
};

/* ------------------------------------------------------------------ storage */

function loadEarned() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return new Set();
    const parsed = JSON.parse(raw);
    const ids = Array.isArray(parsed) ? parsed : Array.isArray(parsed?.earned) ? parsed.earned : [];
    return new Set(ids.filter((id) => Number.isInteger(id)));
  } catch {
    return new Set();
  }
}

function saveEarned() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ version: 1, earned: [...state.earned].sort((a, b) => a - b) }));
  } catch {
    toast('Could not save to this browser’s storage');
  }
}

/* ------------------------------------------------------------------ helpers */

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = text;
  return node;
}

const ICON_TEMPLATE = document.getElementById('icon-template');

function icon(name, size = 16, className = 'icon') {
  const svg = ICON_TEMPLATE.content.firstElementChild.cloneNode(true);
  svg.setAttribute('class', className);
  svg.setAttribute('width', String(size));
  svg.setAttribute('height', String(size));
  svg.querySelector('use').setAttribute('href', `#${name}`);
  return svg;
}

let toastTimer = 0;
function toast(message) {
  els.toast.textContent = message;
  els.toast.classList.add('is-visible');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => els.toast.classList.remove('is-visible'), 2400);
}

const isEarned = (t) => state.earned.has(t.id);
const isRevealed = (t) => !state.spoiler || !t.hidden || isEarned(t);

function matches(t) {
  if (state.grade !== 'all' && t.grade !== state.grade) return false;
  if (state.kind === 'missable' && !t.missable) return false;
  if (state.kind !== 'all' && state.kind !== 'missable' && t.kind !== state.kind) return false;
  if (state.query) {
    const q = state.query;
    const hay = `${t.name} ${t.description} ${t.guide} ${t.grade} ${t.kind}`.toLowerCase();
    if (!hay.includes(q)) return false;
  }
  return true;
}

function sortedTrophies(list) {
  const out = [...list];
  if (state.sort === 'name') {
    out.sort((a, b) => a.name.localeCompare(b.name, 'en'));
  } else if (state.sort === 'grade') {
    out.sort((a, b) => GRADE_RANK[a.grade] - GRADE_RANK[b.grade] || a.stage - b.stage || a.id - b.id);
  } else {
    out.sort((a, b) => a.stage - b.stage || GRADE_RANK[a.grade] - GRADE_RANK[b.grade] || a.id - b.id);
  }
  return out;
}

function flag(text, variant, iconName) {
  const node = el('span', `flag flag-${variant}`);
  if (iconName) node.append(icon(iconName, 11));
  node.append(document.createTextNode(text));
  return node;
}

/* ------------------------------------------------------------------ header */

function renderHeader() {
  const total = state.trophies.length;
  const earned = state.trophies.filter(isEarned).length;
  const pct = total ? Math.round((earned / total) * 100) : 0;
  const missableLeft = state.trophies.filter((t) => t.missable && !isEarned(t)).length;
  const platinum = state.trophies.find((t) => t.grade === 'platinum');

  els.earnedCount.textContent = String(earned);
  els.totalCount.textContent = String(total);
  els.pct.textContent = `${pct}%`;
  els.barFill.style.width = `${pct}%`;
  els.bar.setAttribute('aria-valuenow', String(earned));
  els.bar.setAttribute('aria-valuemax', String(total));
  els.bar.setAttribute('aria-valuetext', `${earned} of ${total} trophies earned, ${pct} percent`);

  els.missableLeft.textContent = `${missableLeft} missable still unearned`;
  els.missableLeft.classList.toggle('hot', missableLeft > 0 && missableLeft < state.trophies.filter((t) => t.missable).length);

  const platinumDone = platinum ? isEarned(platinum) : false;
  els.platinumNote.textContent = platinumDone ? 'Platinum earned' : `Platinum ${earned === total - 1 ? 'one away' : 'locked'}`;

  document.title = `${earned}/${total} · Leonida Legend — GTA VI trophy guide`;
}

function renderStats() {
  const frag = document.createDocumentFragment();
  for (const grade of GRADES) {
    const all = state.trophies.filter((t) => t.grade === grade);
    const got = all.filter(isEarned).length;
    const cell = el('div', 'gcell');
    cell.dataset.grade = grade;
    cell.setAttribute('role', 'group');
    cell.setAttribute('aria-label', `${grade}: ${got} of ${all.length} earned`);

    const top = el('div', 'gcell-top');
    top.append(el('span', 'gcell-dot'));
    top.append(el('span', 'gcell-name', grade === 'platinum' ? 'Plat' : grade));
    top.append(el('span', 'gcell-val', `${got}/${all.length}`));
    cell.append(top);

    const bar = el('div', 'gcell-bar');
    const fill = el('span');
    fill.style.width = `${all.length ? (got / all.length) * 100 : 0}%`;
    bar.append(fill);
    cell.append(bar);
    frag.append(cell);
  }
  els.stats.replaceChildren(frag);
}

function renderCounts() {
  const countFor = (kind) =>
    kind === 'all' ? state.trophies.length : kind === 'missable' ? state.trophies.filter((t) => t.missable).length : state.trophies.filter((t) => t.kind === kind).length;

  for (const pill of els.gradePills.querySelectorAll('.pill')) {
    const n = pill.querySelector('.pill-n');
    const grade = pill.dataset.grade;
    n.textContent = String(grade === 'all' ? state.trophies.length : state.trophies.filter((t) => t.grade === grade).length);
  }
  for (const pill of els.kindPills.querySelectorAll('.pill')) {
    pill.querySelector('.pill-n').textContent = String(countFor(pill.dataset.kind));
  }
  for (const tab of els.tabs) {
    const key = tab.dataset.view;
    const n = tab.querySelector('.tab-n');
    n.textContent = String(
      key === 'checklist' ? state.trophies.length : key === 'roadmap' ? state.doc.roadmap.length : state.trophies.filter((t) => t.missable).length,
    );
  }
}

/* ------------------------------------------------------------------ checklist card */

function buildCard(t) {
  const earned = isEarned(t);
  const revealed = isRevealed(t);
  const card = el('article', 'card');
  card.dataset.id = String(t.id);
  card.dataset.grade = t.grade;
  card.classList.toggle('is-earned', earned);
  card.classList.toggle('is-locked', !revealed);
  card.setAttribute('aria-labelledby', `trophy-name-${t.id}`);

  const badge = el('div', 'badge');
  badge.dataset.grade = t.grade;
  badge.append(icon('i-trophy', 19));
  badge.append(el('span', 'badge-label', t.grade === 'platinum' ? 'Plat' : t.grade));
  badge.setAttribute('role', 'img');
  badge.setAttribute('aria-label', `${t.grade} trophy`);
  card.append(badge);

  const body = el('div', 'card-body');

  if (revealed) {
    const head = el('div', 'card-head');
    const name = el('h3', 'card-name', t.name);
    name.id = `trophy-name-${t.id}`;
    head.append(name);
    head.append(el('span', 'card-stage', `Stage ${t.stage}`));
    if (earned) head.append(flag('Earned', 'earned', 'i-check'));
    body.append(head);
    body.append(el('p', 'card-desc', t.description));
    body.append(el('p', 'card-guide', t.guide));
  } else {
    const locked = el('div', 'card-head');
    const line = el('h3', 'locked-line');
    line.id = `trophy-name-${t.id}`;
    line.append(icon('i-lock', 15));
    line.append(el('span', 'locked-strong', 'Hidden trophy'));
    line.append(document.createTextNode(' — tick to reveal'));
    locked.append(line);
    body.append(locked);
    body.append(el('p', 'locked-hint', `Stage ${t.stage} · ${t.grade} · guide and sources appear when you tick it`));
  }

  const foot = el('div', 'card-foot');
  if (t.missable) foot.append(flag('Missable', 'missable', 'i-alert'));
  if (!revealed) foot.append(flag('Story spoiler', 'hidden', 'i-lock'));
  if (t.kind === 'online') foot.append(flag('Online', 'kind'));
  if (t.kind === 'platinum') foot.append(flag('Platinum', 'kind', 'i-spark'));

  if (revealed && Array.isArray(t.sources) && t.sources.length) {
    const sources = el('div', 'sources');
    sources.append(el('span', 'sources-label', 'Sources'));
    for (const src of t.sources) {
      const a = el('a', 'src');
      a.href = src.url;
      a.target = '_blank';
      a.rel = 'noopener noreferrer nofollow';
      a.append(icon('i-link', 10));
      a.append(document.createTextNode(src.name));
      a.setAttribute('aria-label', `${src.name} (opens in a new tab, not loaded by this app)`);
      sources.append(a);
    }
    foot.append(sources);
  }
  body.append(foot);
  card.append(body);

  const check = el('button', 'check');
  check.type = 'button';
  check.setAttribute('role', 'checkbox');
  check.setAttribute('aria-checked', String(earned));
  check.setAttribute('aria-label', earned ? `Mark ${revealed ? t.name : 'hidden trophy'} as not earned` : `Mark ${revealed ? t.name : 'hidden trophy'} as earned`);
  check.append(icon('i-check', 16));
  check.addEventListener('click', () => toggle(t.id));
  card.append(check);

  return card;
}

function toggle(id) {
  const t = state.byId.get(id);
  if (!t) return;
  const wasEarned = state.earned.has(id);
  if (wasEarned) state.earned.delete(id);
  else state.earned.add(id);
  saveEarned();

  const reveal = !wasEarned && t.hidden && state.spoiler;
  render();
  if (reveal) toast(`Revealed: ${t.name}`);
  else if (!wasEarned) toast(`Earned: ${t.name}`);
  else toast(`Unmarked: ${t.name}`);
}

/* ------------------------------------------------------------------ checklist view */

function renderList() {
  const all = state.trophies;
  const filtered = sortedTrophies(all.filter(matches));
  const frag = document.createDocumentFragment();
  for (const t of filtered) frag.append(buildCard(t));
  els.list.replaceChildren(frag);

  const total = all.length;
  els.resultCount.textContent = `Showing ${filtered.length} of ${total} trophies`;
  const earnedShown = filtered.filter(isEarned).length;
  const bits = [];
  if (state.query) bits.push(`matching “${state.query}”`);
  if (state.grade !== 'all') bits.push(state.grade);
  if (state.kind !== 'all') bits.push(state.kind);
  els.resultMeta.textContent = `${earnedShown} earned in this view${bits.length ? ` · ${bits.join(' · ')}` : ''}`;

  const none = filtered.length === 0;
  els.empty.hidden = !none;
  els.list.hidden = none;
  if (none) {
    els.emptyCopy.textContent = state.query
      ? `Nothing matches “${state.query}”. Try a shorter word, or clear the grade and type filters.`
      : 'No trophy matches these filters. Clear them to see the full list again.';
  }
}

/* ------------------------------------------------------------------ roadmap view */

function renderRoadmap() {
  const frag = document.createDocumentFragment();
  for (const stage of state.doc.roadmap) {
    const inStage = state.trophies.filter((t) => t.stage === stage.stage);
    const got = inStage.filter(isEarned).length;

    const section = el('section', 'stage');
    section.setAttribute('aria-label', `Stage ${stage.stage}: ${stage.title}`);

    const top = el('div', 'stage-top');
    top.append(el('div', 'stage-num', String(stage.stage)));
    const text = el('div');
    text.append(el('h3', 'stage-title', stage.title));
    text.append(el('p', 'stage-detail', stage.detail));
    top.append(text);
    const progress = el('div', 'stage-progress');
    progress.append(el('b', null, `${got}/${inStage.length}`));
    progress.append(el('span', null, 'earned'));
    top.append(progress);
    section.append(top);

    const chips = el('div', 'stage-trophies');
    for (const t of inStage.sort((a, b) => GRADE_RANK[a.grade] - GRADE_RANK[b.grade] || a.id - b.id)) {
      const revealed = isRevealed(t);
      const chip = el('button', 'tchip');
      chip.type = 'button';
      chip.dataset.grade = t.grade;
      chip.dataset.id = String(t.id);
      chip.classList.toggle('is-earned', isEarned(t));
      chip.classList.toggle('is-locked', !revealed);
      chip.append(el('span', 'dot'));
      chip.append(document.createTextNode(revealed ? t.name : 'Hidden trophy'));
      if (t.missable) chip.append(el('span', 'mini-flag', 'missable'));
      chip.setAttribute(
        'aria-label',
        `${revealed ? t.name : 'Hidden trophy'}${t.missable ? ', missable' : ''} — ${isEarned(t) ? 'earned' : 'not earned'}; open in checklist`,
      );
      chip.addEventListener('click', () => openTrophy(t.id));
      chips.append(chip);
    }
    if (!inStage.length) chips.append(el('p', 'stage-detail', 'No trophies in this stage.'));
    section.append(chips);
    frag.append(section);
  }
  els.roadmap.replaceChildren(frag);
}

/* ------------------------------------------------------------------ missable view */

function renderMissable() {
  const list = state.trophies.filter((t) => t.missable).sort((a, b) => a.stage - b.stage || a.id - b.id);
  const frag = document.createDocumentFragment();
  for (const t of list) {
    const earned = isEarned(t);
    const revealed = isRevealed(t);
    const card = el('article', 'missable-card');
    card.classList.toggle('is-earned', earned);

    const ic = el('div', 'missable-icon');
    ic.append(icon(earned ? 'i-check' : 'i-alert', 18));
    card.append(ic);

    const body = el('div');
    const head = el('div', 'missable-head');
    head.append(el('h3', 'missable-name', revealed ? t.name : 'Hidden trophy'));
    head.append(el('span', 'missable-stage', `Stage ${t.stage} · ${t.grade}`));
    if (earned) head.append(flag('Earned', 'earned', 'i-check'));
    body.append(head);
    body.append(el('p', 'missable-why', t.missable_note || 'This trophy can be lost by advancing the story.'));
    card.append(body);

    const act = el('div', 'missable-act');
    const jump = el('button', 'btn btn-quiet');
    jump.type = 'button';
    jump.append(icon('i-list', 15));
    jump.append(document.createTextNode('Open'));
    jump.setAttribute('aria-label', `Open ${revealed ? t.name : 'hidden trophy'} in the checklist`);
    jump.addEventListener('click', () => openTrophy(t.id));
    act.append(jump);
    card.append(act);

    frag.append(card);
  }
  els.missableList.replaceChildren(frag);
}

function openTrophy(id) {
  setView('checklist');
  state.query = '';
  state.grade = 'all';
  state.kind = 'all';
  els.search.value = '';
  syncPills();
  render();
  const card = els.list.querySelector(`.card[data-id="${id}"]`);
  if (card) {
    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
    card.classList.add('is-flash');
    setTimeout(() => card.classList.remove('is-flash'), 1200);
    const check = card.querySelector('.check');
    if (check) check.focus({ preventScroll: true });
  }
}

/* ------------------------------------------------------------------ views & controls */

const VIEW_COPY = {
  checklist: {
    title: 'Trophy checklist',
    sub: 'All 55 trophies in roadmap order. Tick a card to bank it — progress saves in this browser.',
  },
  roadmap: {
    title: 'Roadmap to the platinum',
    sub: 'Eight stages, in the order that keeps every missable in reach. Tap a trophy to jump to its guide.',
  },
  missable: {
    title: 'Missable trophies',
    sub: 'Twelve trophies can be lost for good. Each card names the moment it disappears.',
  },
};

function setView(view, focusPanel = false) {
  state.view = view;
  for (const tab of els.tabs) {
    const selected = tab.dataset.view === view;
    tab.setAttribute('aria-selected', String(selected));
    tab.tabIndex = selected ? 0 : -1;
  }
  els.panelChecklist.hidden = view !== 'checklist';
  els.panelRoadmap.hidden = view !== 'roadmap';
  els.panelMissable.hidden = view !== 'missable';
  els.viewTitle.textContent = VIEW_COPY[view].title;
  els.viewSub.textContent = VIEW_COPY[view].sub;
  document.querySelector('.view-tools').style.visibility = view === 'checklist' ? 'visible' : 'hidden';
  render();
  if (focusPanel) {
    const panel = view === 'checklist' ? els.panelChecklist : view === 'roadmap' ? els.panelRoadmap : els.panelMissable;
    panel.focus({ preventScroll: true });
  }
}

function syncPills() {
  for (const pill of els.gradePills.querySelectorAll('.pill')) {
    pill.setAttribute('aria-pressed', String(pill.dataset.grade === state.grade));
  }
  for (const pill of els.kindPills.querySelectorAll('.pill')) {
    pill.setAttribute('aria-pressed', String(pill.dataset.kind === state.kind));
  }
  els.spoiler.setAttribute('aria-checked', String(state.spoiler));
  els.spoilerState.textContent = state.spoiler ? 'On — story names hidden' : 'Off — everything visible';
}

function render() {
  renderHeader();
  renderStats();
  renderCounts();
  if (state.view === 'checklist') renderList();
  if (state.view === 'roadmap') renderRoadmap();
  if (state.view === 'missable') renderMissable();
}

/* ------------------------------------------------------------------ export / import / reset */

function exportProgress() {
  const payload = {
    app: 'leonida-legend',
    game: state.doc.game,
    platform: state.doc.platform,
    exported_at: new Date().toISOString(),
    total: state.trophies.length,
    earned_count: state.earned.size,
    earned: [...state.earned].sort((a, b) => a - b),
    earned_names: state.trophies.filter(isEarned).map((t) => t.name),
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `gta6-trophy-progress-${new Date().toISOString().slice(0, 10)}.json`;
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
  toast(`Exported ${payload.earned_count} of ${payload.total} trophies`);
}

async function importProgress(file) {
  let parsed;
  try {
    parsed = JSON.parse(await file.text());
  } catch {
    toast('That file is not valid JSON');
    return;
  }
  const raw = Array.isArray(parsed) ? parsed : Array.isArray(parsed?.earned) ? parsed.earned : null;
  if (!raw) {
    toast('No “earned” list found in that file');
    return;
  }
  const valid = new Set();
  let skipped = 0;
  for (const item of raw) {
    if (Number.isInteger(item) && state.byId.has(item)) valid.add(item);
    else if (typeof item === 'string') {
      const hit = state.trophies.find((t) => t.name === item);
      if (hit) valid.add(hit.id);
      else skipped += 1;
    } else skipped += 1;
  }
  if (!valid.size && raw.length) {
    toast('No trophy in that file matched this list');
    return;
  }
  state.earned = valid;
  saveEarned();
  render();
  toast(`Imported ${valid.size} earned${skipped ? ` · ${skipped} skipped` : ''}`);
}

/* ------------------------------------------------------------------ boot */

async function boot() {
  state.earned = loadEarned();
  try {
    const res = await fetch(DATA_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    state.doc = await res.json();
  } catch (error) {
    els.list.replaceChildren();
    els.empty.hidden = false;
    els.emptyCopy.textContent = `Could not read ${DATA_URL} (${error.message}). Serve the app folder over HTTP rather than opening the file directly.`;
    return;
  }

  state.trophies = state.doc.trophies;
  state.byId = new Map(state.trophies.map((t) => [t.id, t]));

  const storedSpoiler = localStorage.getItem(`${STORAGE_KEY}:spoiler`);
  state.spoiler = storedSpoiler === null ? true : storedSpoiler === '1';

  els.tabs.forEach((tab) => {
    tab.addEventListener('click', () => setView(tab.dataset.view, true));
    tab.addEventListener('keydown', (event) => {
      if (!['ArrowDown', 'ArrowUp', 'ArrowRight', 'ArrowLeft', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      const index = els.tabs.indexOf(tab);
      const last = els.tabs.length - 1;
      let next = index;
      if (event.key === 'ArrowDown' || event.key === 'ArrowRight') next = index === last ? 0 : index + 1;
      if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') next = index === 0 ? last : index - 1;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = last;
      els.tabs[next].focus();
      setView(els.tabs[next].dataset.view, true);
    });
  });

  els.gradePills.addEventListener('click', (event) => {
    const pill = event.target.closest('.pill');
    if (!pill) return;
    state.grade = pill.dataset.grade;
    syncPills();
    render();
  });

  els.kindPills.addEventListener('click', (event) => {
    const pill = event.target.closest('.pill');
    if (!pill) return;
    state.kind = pill.dataset.kind;
    syncPills();
    render();
  });

  let searchTimer = 0;
  els.search.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      state.query = els.search.value.trim().toLowerCase();
      render();
    }, 90);
  });

  els.sort.addEventListener('change', () => {
    state.sort = els.sort.value;
    render();
  });

  els.spoiler.addEventListener('click', () => {
    state.spoiler = !state.spoiler;
    localStorage.setItem(`${STORAGE_KEY}:spoiler`, state.spoiler ? '1' : '0');
    syncPills();
    render();
    toast(state.spoiler ? 'Spoiler shield on' : 'Spoiler shield off');
  });

  els.exportBtn.addEventListener('click', exportProgress);
  els.importBtn.addEventListener('click', () => els.importFile.click());
  els.importFile.addEventListener('change', () => {
    const file = els.importFile.files?.[0];
    if (file) importProgress(file);
    els.importFile.value = '';
  });

  els.resetBtn.addEventListener('click', () => {
    if (typeof els.resetDialog.showModal === 'function') els.resetDialog.showModal();
    else if (window.confirm('Reset all trophy progress in this browser?')) doReset();
  });
  els.resetDialog.addEventListener('close', () => {
    if (els.resetDialog.returnValue === 'confirm') doReset();
    els.resetDialog.returnValue = '';
  });

  els.clearFilters.addEventListener('click', () => {
    state.query = '';
    state.grade = 'all';
    state.kind = 'all';
    els.search.value = '';
    syncPills();
    render();
    els.search.focus();
  });

  document.addEventListener('keydown', (event) => {
    const tag = document.activeElement?.tagName;
    const typing = tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT';
    if (event.key === '/' && !typing) {
      event.preventDefault();
      els.search.focus();
      els.search.select();
    }
    if (event.key === 'Escape' && document.activeElement === els.search && els.search.value) {
      els.search.value = '';
      state.query = '';
      render();
    }
  });

  const missableTotal = state.trophies.filter((t) => t.missable).length;
  els.footMeta.textContent = `${state.trophies.length} trophies · ${missableTotal} missable · ${state.doc.roadmap.length} roadmap stages · ${state.doc.meta?.source_note ? 'Sources cited on every card' : ''}`;

  syncPills();
  setView('checklist');
  render();
}

function doReset() {
  state.earned = new Set();
  saveEarned();
  render();
  toast('Progress reset');
}

boot();
