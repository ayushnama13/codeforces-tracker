// CF Tracker frontend. Plain JS, no build step. All API strings go in via textContent.
(function () {
  const { el, sparkline, ratingChart, calendar, heatmap, bars, hover, RANK_COLORS } = Charts;
  const DEFAULT_HANDLE = 'ayushanma';
  const HANDLE_RE = /^[A-Za-z0-9_.-]{3,24}$/;
  const view = document.getElementById('view');

  // ---- small utilities -------------------------------------------------------
  const ls = {
    get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : v; } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* private mode */ } },
  };
  let handle = ls.get('handle', DEFAULT_HANDLE);
  if (!HANDLE_RE.test(handle)) handle = DEFAULT_HANDLE;

  async function api(path, opts = {}) {
    const init = { method: opts.method || 'GET', headers: {} };
    if (opts.body) { init.headers['Content-Type'] = 'application/json'; init.body = JSON.stringify(opts.body); }
    const r = await fetch(`/api/${encodeURIComponent(handle)}${path}`, init);
    let data = null;
    try { data = await r.json(); } catch (e) { /* non-JSON error page */ }
    if (!r.ok) throw new Error((data && typeof data.detail === 'string' && data.detail) || `${r.status} ${r.statusText}`);
    return data;
  }

  function h(tag, cls, ...kids) {
    const e = el(tag, cls);
    kids.flat().forEach(k => { if (k == null || k === false) return; e.append(k instanceof Node ? k : document.createTextNode(String(k))); });
    return e;
  }
  const cfUrl = (cid, idx) => `https://codeforces.com/contest/${cid}/problem/${idx}`;
  function ext(text, href, cls) { const a = el('a', cls || 'link', text); a.href = href; a.target = '_blank'; a.rel = 'noopener'; return a; }
  function pid(id, linkToDetail) {
    if (!linkToDetail) return el('span', 'pid', id);
    const a = el('a', 'pid', id); a.href = `#/problem/${id}`; a.title = 'Your submissions on this problem'; return a;
  }
  const ratingPill = r => el('span', 'pill', r == null ? '–' : String(r));
  const tagList = (tags, max) => h('div', null, (tags || []).slice(0, max || 99).map(t => el('span', 'tag', t)));
  function btn(text, cls, onClick, title) { const b = el('button', 'btn ' + (cls || ''), text); if (title) b.title = title; b.onclick = onClick; return b; }
  function card(title, small, ...kids) {
    const head = h('h2', null, title, small instanceof Node ? small : small ? el('small', null, small) : null);
    return h('section', 'card', head, ...kids);
  }
  const fmtDate = ts => new Date(ts * 1000).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
  const fmtDateTime = ts => new Date(ts * 1000).toLocaleString(undefined, { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  function ago(ts) {
    const s = Date.now() / 1000 - ts;
    if (s < 90) return 'just now';
    if (s < 3600) return `${Math.round(s / 60)} min ago`;
    if (s < 86400) return `${Math.round(s / 3600)} h ago`;
    return `${Math.round(s / 86400)} days ago`;
  }
  const VERDICT = { OK: ['AC', 'v-ok'], WRONG_ANSWER: ['WA', 'v-wa'], TIME_LIMIT_EXCEEDED: ['TLE', 'v-tle'], MEMORY_LIMIT_EXCEEDED: ['MLE', 'v-tle'], RUNTIME_ERROR: ['RE', 'v-wa'], COMPILATION_ERROR: ['CE', 'v-other'], IDLENESS_LIMIT_EXCEEDED: ['ILE', 'v-tle'], CHALLENGED: ['HACKED', 'v-wa'], SKIPPED: ['SKIP', 'v-other'], TESTING: ['…', 'v-other'] };
  function verdict(v) { const [t, c] = VERDICT[v] || [v || '–', 'v-other']; const s = el('span', 'verdict ' + c, t); if (v) s.title = v; return s; }
  const PTYPE = { CONTESTANT: 'contest', OUT_OF_COMPETITION: 'unofficial', VIRTUAL: 'virtual', PRACTICE: 'practice', MANAGER: 'manager' };
  const plural = (n, w) => `${n} ${w}${n === 1 ? '' : 's'}`;

  let toastTimer;
  function toast(msg) {
    const t = document.getElementById('toast');
    t.textContent = msg; t.classList.add('show');
    clearTimeout(toastTimer); toastTimer = setTimeout(() => t.classList.remove('show'), 2200);
  }

  function statusChip(meta) {
    const c = h('div', 'status', el('span', 'dot' + (meta.stale ? ' stale' : '')),
      meta.stale ? `Offline: showing cached data from ${ago(meta.loaded_at)}` : `Loaded ${ago(meta.loaded_at)}`);
    c.title = `${meta.problems_rows} problems in the local list, updated ${fmtDateTime(meta.problems_updated)}`;
    return c;
  }
  function pageHead(title, sub, meta) {
    return h('div', 'head', h('div', null, el('h1', null, title), sub ? el('div', 'sub', sub) : null), meta ? statusChip(meta) : null);
  }
  function table(headers, rows) {
    const thead = h('thead', null, h('tr', null, headers.map(x => typeof x === 'string' ? el('th', null, x) : el('th', x.num ? 'num' : null, x.label))));
    return h('div', 'tbl', h('table', null, thead, h('tbody', null, rows)));
  }
  function td(content, cls) { const c = el('td', cls); if (content instanceof Node) c.append(content); else if (content != null) c.textContent = String(content); return c; }

  // Run an action, then re-render the current page with fresh data.
  async function act(fn, msg) {
    try { await fn(); if (msg) toast(msg); await render(false); }
    catch (e) { toast('Failed: ' + e.message); }
  }

  // ---- pages ---------------------------------------------------------------
  const pages = {};

  pages.today = {
    load: () => api('/today'),
    draw(d) {
      const s = d.summary, hist = d.rating_history || [];
      const last = hist[hist.length - 1];
      const rankC = RANK_COLORS[s.rank] || 'var(--ink-2)';
      const today = new Date().toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

      const ratingTile = h('div', 'card stat',
        el('div', 'l', 'Rating'),
        h('div', null, el('span', 'v', s.rating == null ? 'unrated' : String(s.rating)),
          last ? el('span', 'd ' + (last.delta >= 0 ? 'up' : 'down'), (last.delta >= 0 ? '+' : '') + last.delta) : null),
        h('div', 'l', (() => { const r = el('span', null, s.rank || 'unrated'); r.style.color = rankC; r.style.fontWeight = 600; r.style.textTransform = 'capitalize'; return r; })(),
          s.maxRating != null ? ` · max ${s.maxRating}` : ''),
        el('div'));
      sparkline(ratingTile.lastChild, hist.map(x => x.newRating), rankC);
      if (hist.length) hover(ratingTile.lastChild, () => [`Last ${plural(hist.length, 'rated contest')}`, `${hist[0].newRating} → ${last.newRating}`]);

      const stats = h('section', 'grid g4 mb', ratingTile,
        h('div', 'card stat', el('div', 'l', 'Solved'), el('div', 'v', String(s.solved)), el('div', 'l', `${s.submissions} submissions`)),
        h('div', 'card stat', el('div', 'l', 'Current streak'), el('div', 'v', plural(s.current_streak, 'day')), el('div', 'l', `longest ${plural(s.longest_streak, 'day')}`)),
        h('div', 'card stat', el('div', 'l', 'Attempted, not solved'), el('div', 'v', String(s.attempted_unsolved)), el('div', 'l', 'in the upsolve queue')));

      return [pageHead('Today', today, d.meta), stats,
        h('section', 'grid g-main mb', dailyCard(d.daily), reviewsCard(d.reviews, 'Due for review')),
        activityCard(d.calendar, 'mb'),
        upsolveCard(d.upsolve, d.upsolve_total)];
    },
  };

  function dailyCard(daily) {
    const p = daily && daily.problem;
    if (!p) return card('Problem of the day', null, el('div', 'empty', 'No unsolved problem found near your rating.'));
    const status = daily.done ? h('span', 'pill good', '✓ Solved') : el('small', null, 'stretch pick for ' + daily.date);
    return h('section', 'card pick',
      h('h2', null, 'Problem of the day', status),
      h('div', 'row', pid(p.id), ratingPill(p.rating), p.solvedCount ? el('span', 'muted small', `${p.solvedCount.toLocaleString()} solvers`) : null),
      el('div', 'name', p.name),
      tagList(p.tags),
      p.reason ? el('div', 'why', p.reason) : null,
      h('div', 'row wrap', ext('Open on Codeforces ↗', p.url, 'btn primary'),
        el('span', 'muted small right', daily.done ? 'Nice. A new pick comes tomorrow.' : 'Marked solved automatically once you get AC.')));
  }

  const SOURCE = { hard: 'took many tries', backlog: 'from backlog', revise: 'marked for revision' };
  function reviewsCard(r, title) {
    const list = el('ul', 'list');
    r.due.forEach(x => {
      const when = x.reviews_done === 0 ? 'first review' : x.overdue_days > 0 ? `overdue ${x.overdue_days}d` : 'due today';
      const name = ext(x.name || x.id, x.url, 't');
      name.title = `${SOURCE[x.source] || x.source} · review ${x.reviews_done + 1} of 3 · ${when}`;
      list.append(h('li', null, pid(x.id, x.source !== 'backlog'), name,
        el('span', 'muted small', `${x.reviews_done}/3`), ratingPill(x.rating),
        h('span', 'acts',
          btn('Done', 'sm', () => act(() => api(`/review/${x.id}`, { method: 'POST' }), `${x.id} reviewed`), 'I re-solved it; schedule the next review'),
          btn('Hide', 'sm ghost', () => act(() => api(`/hide/${x.id}`, { method: 'POST' }), `${x.id} hidden`), 'Never show this problem again'))));
    });
    const small = `${r.due.length} due · ${r.upcoming} upcoming · ${r.mastered} mastered`;
    return card(title, small, r.due.length ? list : el('div', 'empty', 'Nothing due right now.'));
  }

  function activityCard(days, cls) {
    const host = el('div');
    const total = days.reduce((a, d) => a + d.submissions, 0), active = days.filter(d => d.submissions).length;
    const c = card('Activity', `${total} submissions on ${plural(active, 'day')} in the last ${Math.round(days.length / 7)} weeks`, host,
      h('div', 'row', el('span', 'muted small', 'Each square is a day; brighter means more submissions.'),
        h('div', 'legend right', 'Less', [0, 1, 2, 3, 4].map(i => { const s = el('span'); s.style.background = `var(--heat-${i})`; return s; }), 'More')));
    if (cls) c.classList.add(cls);
    calendar(host, days);
    return c;
  }

  function upsolveCard(items, total) {
    const rows = items.map(u => h('tr', null,
      td(pid(u.id, u.source === 'attempted')),
      td(ext(u.name, u.url)),
      td(ratingPill(u.rating)),
      td(tagList(u.tags, 3)),
      td(u.source === 'attempted' ? String(u.tries) : '–', 'num'),
      td(u.source === 'attempted' ? verdict(u.last_verdict) : el('span', 'muted small', 'not tried'))));
    return card('Upsolve queue', `${items.length} of ${total} · attempted-but-unsolved first, then unsolved problems from your contests`,
      items.length ? table(['Problem', 'Name', 'Rating', 'Tags', { label: 'Tries', num: true }, 'Last verdict'], rows) : el('div', 'empty', 'Nothing to upsolve.'));
  }

  // ---- practice ----
  let practiceBand = null;
  pages.practice = {
    load: () => api('/practice' + (practiceBand ? `?band=${practiceBand}` : '')),
    draw(d) {
      const TIERS = [['comfortable', 'Comfortable', 'At or a little below your rating'], ['stretch', 'Stretch', 'Up to +200 over your rating'], ['hard', 'Hard', '+200 to +400 over your rating']];
      const tiers = h('section', 'grid g3 mb', TIERS.map(([k, name, range]) => {
        const items = d.recommend[k] || [];
        return h('div', 'card tier', el('h3', null, name), el('div', 'range', range),
          items.length ? items.map(p => h('div', 'prob',
            h('div', 'row', pid(p.id), ratingPill(p.rating), el('span', 'muted small right', p.solvedCount ? `${p.solvedCount.toLocaleString()} solvers` : '')),
            ext(p.name, p.url, 'nm link'),
            p.reason ? el('div', 'rs', p.reason) : null,
            tagList(p.tags, 4))) : el('div', 'empty', 'No problems in this range.'));
      }));

      const lad = d.ladder;
      practiceBand = lad.band;
      const bands = h('div', 'bands', d.ladders.map(b => {
        const pct = b.total ? Math.round(b.solved / b.total * 100) : 0;
        const x = h('button', 'band' + (b.band === lad.band ? ' on' : ''), el('b', null, String(b.band)), el('small', null, `${b.solved}/${b.total}`),
          h('div', 'progress', (() => { const f = el('div'); f.style.width = pct + '%'; return f; })()));
        x.title = `${b.solved} of ${b.total} problems rated ${b.band} solved`;
        x.onclick = () => { practiceBand = b.band; render(false); };
        return x;
      }));
      const solvedTop = lad.problems.filter(p => p.solved).length;
      const prog = h('div', 'progress', (() => { const f = el('div'); f.style.width = (lad.problems.length ? solvedTop / lad.problems.length * 100 : 0) + '%'; return f; })());
      const rows = lad.problems.map((p, i) => h('tr', null,
        td(String(i + 1), 'num muted'), td(pid(p.id, p.solved)), td(ext(p.name, p.url)), td(tagList(p.tags, 3)),
        td(p.solvedCount.toLocaleString(), 'num'), td(p.solved ? el('span', 'check', '✓') : '', 'num')));
      const ladder = card(`Ladder · ${lad.band}`, `${solvedTop} of ${lad.problems.length} done · most-solved problems at this rating`,
        prog, el('div', 'mb'), bands, el('div', 'mb'),
        lad.problems.length ? table([{ label: '#', num: true }, 'Problem', 'Name', 'Tags', { label: 'Solvers', num: true }, { label: '', num: true }], rows) : el('div', 'empty', 'No problems at this rating.'));
      return [pageHead('Practice', 'Unsolved problems picked around your rating, leaning on your weakest tags. Picks are stable for the day.', d.meta), tiers, ladder];
    },
  };

  // ---- progress ----
  pages.progress = {
    load: () => api('/progress'),
    draw(d) {
      const s = d.summary, hist = d.rating_history, contests = d.contests;
      const best = contests.length ? Math.min(...contests.map(c => c.rank)) : null;
      const bestDelta = contests.length ? Math.max(...contests.map(c => c.delta)) : null;
      const stats = h('section', 'grid g4 mb',
        h('div', 'card stat', el('div', 'l', 'Rating'), el('div', 'v', s.rating == null ? '–' : String(s.rating)), el('div', 'l', s.maxRating != null ? `max ${s.maxRating} (${s.maxRank})` : 'unrated')),
        h('div', 'card stat', el('div', 'l', 'Rated contests'), el('div', 'v', String(hist.length)), el('div', 'l', hist.length ? `since ${fmtDate(hist[0].time)}` : '')),
        h('div', 'card stat', el('div', 'l', 'Best rank'), el('div', 'v', best == null ? '–' : String(best)), el('div', 'l', bestDelta != null ? `best gain ${bestDelta >= 0 ? '+' : ''}${bestDelta}` : '')),
        h('div', 'card stat', el('div', 'l', 'Longest streak'), el('div', 'v', plural(s.longest_streak, 'day')), el('div', 'l', `current ${plural(s.current_streak, 'day')}`)));

      const chartHost = el('div');
      const chart = card('Rating', 'hover a point for the contest', chartHost);
      chart.classList.add('mb');
      requestAnimationFrame(() => ratingChart(chartHost, hist, d.rank_bands));

      const weakHost = el('div');
      const weak = d.weak_tags.slice(0, 12);
      const weakCard = card('Weakest tags', 'share of tried problems you solved (3+ tried)', weakHost);
      if (weak.length) bars(weakHost, weak, {
        label: t => t.tag, value: t => t.solve_rate, text: t => `${Math.round(t.solve_rate * 100)}%`,
        tip: t => [t.tag, `${t.solved} of ${t.attempted} tried problems solved`, t.avg_rating_solved ? `avg solved rating ${t.avg_rating_solved}, max ${t.max_rating_solved}` : 'no rated solves'],
      }); else weakHost.append(el('div', 'empty', 'Not enough data yet.'));

      const dl = d.daily_history.slice(0, 14);
      const dailyCard = card('Problem of the day log', dl.length ? `${dl.filter(x => x.done).length} of ${dl.length} solved` : null,
        dl.length ? h('ul', 'list', dl.map(x => h('li', null, el('span', 'muted small', x.date), pid(x.id), el('span', 't'),
          x.done ? el('span', 'pill good', 'solved') : el('span', 'pill', 'missed')))) : el('div', 'empty', 'Picks show up here from today on.'));

      const rows = contests.map(c => h('tr', null,
        td(fmtDate(c.time), 'muted nowrap'),
        td(ext(c.contestName, `https://codeforces.com/contest/${c.contestId}`)),
        td(c.division ? el('span', 'pill', c.division) : ''),
        td(String(c.rank), 'num'),
        td((() => { const x = el('span', c.delta >= 0 ? 'up' : 'down', (c.delta >= 0 ? '+' : '') + c.delta); x.style.fontWeight = 600; return x; })(), 'num'),
        td(String(c.newRating), 'num'),
        td(`${c.solved_in_contest}/${c.total_problems}`, 'num'),
        td(c.upsolved_later ? `+${c.upsolved_later}` : '–', 'num')));
      const contestCard = card('Contest history', 'solved = during the contest; upsolved = solved later',
        contests.length ? table(['Date', 'Contest', 'Div', { label: 'Rank', num: true }, { label: 'Δ', num: true }, { label: 'Rating', num: true }, { label: 'Solved', num: true }, { label: 'Upsolved', num: true }], rows) : el('div', 'empty', 'No rated contests.'));

      return [pageHead('Progress', null, d.meta), stats, chart, activityCard(d.calendar, 'mb'),
        h('section', 'grid g-main mb', weakCard, dailyCard), contestCard];
    },
    redrawOnResize: true,
  };

  // ---- coverage ----
  const cov = { axis: ls.get('cov.axis', 'letter'), lastN: ls.get('cov.lastN', '100'), divs: JSON.parse(ls.get('cov.divs', '[]') || '[]'), mode: ls.get('cov.mode', 'pct') };
  function saveCov() { ls.set('cov.axis', cov.axis); ls.set('cov.lastN', cov.lastN); ls.set('cov.divs', JSON.stringify(cov.divs)); ls.set('cov.mode', cov.mode); }
  pages.coverage = {
    load() {
      const q = new URLSearchParams({ axis: cov.axis });
      if (/^\d+$/.test(cov.lastN) && +cov.lastN > 0) q.set('last_n', cov.lastN);
      cov.divs.forEach(x => q.append('div', x));
      return api('/coverage?' + q);
    },
    draw(d) {
      const seg = (opts, cur, set) => h('div', 'seg', opts.map(([v, label]) => { const b = el('button', v === cur ? 'on' : null, label); b.onclick = () => { set(v); saveCov(); render(false); }; return b; }));
      const lastN = el('input', 'field'); lastN.type = 'number'; lastN.min = 1; lastN.placeholder = 'all'; lastN.value = cov.lastN; lastN.style.width = '84px';
      let t; lastN.oninput = () => { clearTimeout(t); t = setTimeout(() => { cov.lastN = lastN.value.trim(); saveCov(); render(false); }, 500); };
      const divs = h('div', 'chips', d.divisions.map(x => {
        const b = el('button', 'chip' + (cov.divs.includes(x) ? ' on' : ''), x);
        b.onclick = () => { cov.divs = cov.divs.includes(x) ? cov.divs.filter(y => y !== x) : cov.divs.concat(x); saveCov(); render(false); };
        return b;
      }));
      const controls = h('section', 'card mb', h('div', 'controls',
        h('label', null, 'Rows', seg([['letter', 'Problem letter'], ['tag', 'Tag']], cov.axis, v => cov.axis = v)),
        h('label', null, 'Cells show', seg([['total', 'Problems'], ['pct', '% solved'], ['unsolved', 'Not solved']], cov.mode, v => cov.mode = v)),
        h('label', null, 'Last', lastN, 'contests')),
        h('div', 'row wrap', el('span', 'muted small', 'Divisions (none selected = all):'), divs));
      divs.parentNode.style.marginTop = '12px';

      const hm = d.heatmap, all = hm.cells.flat();
      const totals = hm.rows.length ? { total: 0, solved: 0, attempted: 0 } : null;
      if (cov.axis === 'letter' && totals) all.forEach(c => { totals.total += c.total; totals.solved += c.solved; totals.attempted += c.attempted; });
      const MODES = {
        total: { value: c => c.total, label: c => String(c.total), sqrt: true },
        pct: { value: c => c.total ? c.solved / c.total : null, label: c => c.solved ? `${Math.round(c.solved / c.total * 100)}%` : '', max: 1 },
        unsolved: { value: c => c.total - c.solved, label: c => String(c.total - c.solved), sqrt: true },
      };
      const host = el('div', 'hm-wrap');
      heatmap(host, hm, Object.assign({ corner: cov.axis === 'letter' ? 'letter \\ rating' : 'tag \\ rating' }, MODES[cov.mode]));
      const sub = totals && cov.axis === 'letter' ? `${totals.total.toLocaleString()} rated problems · ${totals.solved} solved · ${totals.attempted} attempted` : 'a problem with several tags counts once per tag';
      return [pageHead('Coverage', 'Which kinds of problems you have and have not touched. Hover a cell for the split.', d.meta),
        controls, card(cov.axis === 'letter' ? 'Problem letter × rating' : 'Tag × rating band', sub, host,
          el('div', 'muted small', cov.mode === 'pct'
            ? 'Brighter = larger share solved. Grey = none solved yet. Dashed = no problems in that cell.'
            : 'Brighter = more problems. Dashed = no problems in that cell.'))];
    },
  };

  // ---- revision ----
  pages.revision = {
    load: () => api('/revision'),
    draw(d) {
      const input = el('input', 'field'); input.placeholder = 'Problem id, e.g. 1784D2'; input.style.flex = '1'; input.spellcheck = false;
      const form = h('form', 'row', input, el('button', 'btn primary', 'Add'));
      form.onsubmit = e => {
        e.preventDefault();
        const id = input.value.trim().toUpperCase().replace(/\s+/g, '');
        if (!/^\d+[A-Z]\d?$/.test(id)) { toast('Use a problem id like 1784D2'); return; }
        act(() => api('/backlog', { method: 'POST', body: { id } }), `${id} added to backlog`);
      };
      const backlog = el('ul', 'list');
      d.backlog.forEach(p => backlog.append(h('li', null, pid(p.id), ext(p.name || p.id, p.url || cfUrl(p.contestId, p.index), 't'), ratingPill(p.rating),
        h('span', 'acts', btn('Remove', 'sm ghost', () => act(() => api(`/backlog/${p.id}`, { method: 'DELETE' }), `${p.id} removed`))))));
      const backlogCard = card('Backlog', `${d.backlog.length} problems you added by hand`, form, el('div', 'mb'),
        d.backlog.length ? backlog : el('div', 'empty', 'Empty. Add problems you want to come back to.'));

      const revise = el('ul', 'list');
      d.revise.forEach(id => revise.append(h('li', null, pid(id, true), el('span', 't'),
        h('span', 'acts', btn('Unmark', 'sm ghost', () => act(() => api(`/revise/${id}`, { method: 'DELETE' }), `${id} unmarked`))))));
      const reviseCard = card('Marked for revision', `${d.revise.length}`, d.revise.length ? revise : el('div', 'empty', 'Mark problems from their detail page.'));

      return [pageHead('Revision', 'Spaced repetition at 7, 30 and 90 days for backlog problems, problems you marked, and problems that took 4+ tries.', d.meta),
        h('section', 'grid g-main mb', reviewsCard(d.reviews, 'Due'), h('div', 'grid', backlogCard, reviseCard)),
        el('div', 'muted small', `${plural(d.hidden.length, 'problem')} hidden from reviews and picks.`)];
    },
  };

  // ---- problem detail ----
  pages.problem = {
    load: arg => api(`/problem/${encodeURIComponent(arg)}`),
    draw(d) {
      const mins = d.minutes_to_ac;
      const fmtMins = m => m == null ? '–' : m < 60 ? `${m} min` : m < 1440 ? `${(m / 60).toFixed(1)} h` : `${Math.round(m / 1440)} days`;
      const statusPill = d.status === 'solved' ? el('span', 'pill good', 'solved') : el('span', 'pill bad', 'not solved');
      const head = h('div', 'head', h('div', null,
        h('div', 'row', pid(d.id), ratingPill(d.rating), statusPill),
        el('h1', null, d.name)),
        h('div', 'row', ext('Open on Codeforces ↗', d.url, 'btn primary'),
          btn('Mark for revision', '', () => act(() => api(`/revise/${d.id}`, { method: 'POST' }), `${d.id} marked for revision`)),
          btn('Add to backlog', '', () => act(() => api('/backlog', { method: 'POST', body: { id: d.id } }), `${d.id} added to backlog`))));
      const stats = h('section', 'grid g4 mb',
        h('div', 'card stat', el('div', 'l', d.status === 'solved' ? 'Tries to AC' : 'Tries so far'), el('div', 'v', String(d.tries))),
        h('div', 'card stat', el('div', 'l', 'Time to AC'), el('div', 'v', fmtMins(mins)), el('div', 'l', 'from first submission')),
        h('div', 'card stat', el('div', 'l', 'Solved in contest'), el('div', 'v', d.solved_in_contest ? 'Yes' : 'No')),
        h('div', 'card stat', el('div', 'l', 'First tried'), el('div', 'v', d.first_ts ? fmtDate(d.first_ts) : '–'), el('div', 'l', d.first_ok_ts ? `AC on ${fmtDate(d.first_ok_ts)}` : '')));
      const rows = d.submissions.map(s => h('tr', null, td(fmtDateTime(s.time), 'muted nowrap'), td(verdict(s.verdict)),
        td(PTYPE[s.participantType] || s.participantType || '–'), td(String(s.passedTestCount), 'num'), td(s.language || '–', 'muted')));
      const back = btn('← Back', 'sm ghost', () => history.length > 1 ? history.back() : (location.hash = '#/today'));
      back.style.marginBottom = '10px';
      return [back, head, tagList(d.tags), el('div', 'mb'), stats,
        card('Submissions', plural(d.submissions.length, 'submission'), table(['Time', 'Verdict', 'Type', { label: 'Tests passed', num: true }, 'Language'], rows))];
    },
  };

  // ---- router ----------------------------------------------------------------
  let current = { name: null, arg: null, data: null }, token = 0;

  function parseHash() {
    const m = location.hash.replace(/^#\/?/, '').split('/');
    const name = pages[m[0]] ? m[0] : 'today';
    return { name, arg: m[1] ? decodeURIComponent(m[1]) : null };
  }

  function skeleton() {
    return [h('div', 'head', h('div', null, el('div', 'skel', null))), h('section', 'grid g4 mb', [0, 1, 2, 3].map(() => el('div', 'skel'))), el('div', 'skel mb'), el('div', 'skel')]
      .map((n, i) => { if (i === 0) n.firstChild.firstChild.style.cssText = 'height:28px;width:180px'; return n; });
  }

  function errorView(e) {
    const retry = btn('Try again', 'primary', () => render(true));
    return [card('Could not load data', null, el('p', null, e.message), h('div', 'row', retry))].map(c => { c.classList.add('error'); return c; });
  }

  function paint(nodes) {
    Charts.hideTip();
    view.replaceChildren(...nodes);
    document.body.dataset.ready = '1';
  }

  async function render(showSkeleton = true) {
    const { name, arg } = parseHash();
    const my = ++token;
    document.querySelectorAll('#nav a, #mnav a').forEach(a => a.classList.toggle('on', a.getAttribute('href') === '#/' + name));
    document.title = `${name[0].toUpperCase() + name.slice(1)} · CF Tracker`;
    document.body.dataset.ready = '';
    if (showSkeleton || current.name !== name) view.replaceChildren(...skeleton());
    try {
      const data = await pages[name].load(arg);
      if (my !== token) return;
      current = { name, arg, data };
      paint(pages[name].draw(data));
    } catch (e) {
      if (my !== token) return;
      paint(errorView(e));
    }
  }


  // ---- header wiring ---------------------------------------------------------
  const hIn = document.getElementById('handle');
  hIn.value = handle;
  document.getElementById('handle-form').onsubmit = e => {
    e.preventDefault();
    const v = hIn.value.trim();
    if (!HANDLE_RE.test(v)) { toast('Handles are 3–24 letters, digits, _ . -'); return; }
    handle = v; ls.set('handle', v); practiceBand = null; hIn.blur(); render(true);
  };
  document.getElementById('theme').onclick = () => {
    const r = document.documentElement;
    r.dataset.theme = r.dataset.theme === 'dark' ? 'light' : 'dark';
    ls.set('theme', r.dataset.theme);
    if (current.data) paint(pages[current.name].draw(current.data));
  };
  document.getElementById('refresh').onclick = async () => {
    const b = document.getElementById('refresh'), ic = document.getElementById('refresh-ic');
    b.disabled = true; ic.className = 'spin';
    try { await api('/refresh', { method: 'POST' }); toast('Fetched the latest data from Codeforces'); await render(false); }
    catch (e) { toast('Refresh failed: ' + e.message); }
    finally { b.disabled = false; ic.className = ''; }
  };
  document.getElementById('mnav').replaceChildren(...[...document.querySelectorAll('#nav a')].map(a => a.cloneNode(true)));

  let lastW = innerWidth, rt;
  addEventListener('resize', () => {
    clearTimeout(rt);
    rt = setTimeout(() => {
      if (Math.abs(innerWidth - lastW) < 40 || !current.data || !pages[current.name].redrawOnResize) return;
      lastW = innerWidth; paint(pages[current.name].draw(current.data));
    }, 200);
  });
  addEventListener('hashchange', () => render(true));
  render(true);
})();
