// Small hand-written SVG/HTML charts. Every label goes in through textContent.
(function () {
  const SVG = 'http://www.w3.org/2000/svg';

  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function svg(tag, attrs) {
    const e = document.createElementNS(SVG, tag);
    for (const k in attrs || {}) e.setAttribute(k, attrs[k]);
    return e;
  }

  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  // ---- tooltip -------------------------------------------------------------
  const tip = () => document.getElementById('tip');

  function showTip(e, lines) {
    const t = tip();
    t.replaceChildren();
    lines.forEach((line, i) => t.append(el('div', i === 0 ? 'tip-h' : null, line)));
    t.style.opacity = 1;
    const pad = 14, w = t.offsetWidth, h = t.offsetHeight;
    let x = e.clientX + pad, y = e.clientY + pad;
    if (x + w > innerWidth - 8) x = e.clientX - w - pad;
    if (y + h > innerHeight - 8) y = e.clientY - h - pad;
    t.style.left = x + 'px';
    t.style.top = y + 'px';
  }

  function hideTip() { tip().style.opacity = 0; }

  function hover(node, linesFn) {
    node.addEventListener('mousemove', e => showTip(e, linesFn()));
    node.addEventListener('mouseleave', hideTip);
  }

  // ---- colour ramp ---------------------------------------------------------
  function hexToRgb(h) {
    h = h.replace('#', '');
    return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16));
  }

  function ramp(t) {
    // t in [0,1] -> colour between --heat-1 and --heat-4 (heat-0 is reserved for "nothing")
    const stops = [1, 2, 3, 4].map(i => hexToRgb(cssVar('--heat-' + i)));
    const x = Math.max(0, Math.min(1, t)) * (stops.length - 1);
    const i = Math.min(stops.length - 2, Math.floor(x)), f = x - i;
    const c = stops[i].map((v, k) => Math.round(v + (stops[i + 1][k] - v) * f));
    return { bg: `rgb(${c.join(',')})`, light: (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) > 150 };
  }

  // ---- sparkline -----------------------------------------------------------
  function sparkline(host, values, color) {
    host.replaceChildren();
    if (values.length < 2) return;
    const w = 220, h = 36, lo = Math.min(...values), hi = Math.max(...values);
    const s = svg('svg', { viewBox: `0 0 ${w} ${h}`, preserveAspectRatio: 'none', class: 'spark' });
    const pts = values.map((v, i) => [2 + i / (values.length - 1) * (w - 4), h - 3 - (v - lo) / (hi - lo || 1) * (h - 6)]);
    s.append(svg('polyline', { points: pts.map(p => p.join(',')).join(' '), fill: 'none', stroke: color, 'stroke-width': 2, 'stroke-linejoin': 'round', 'stroke-linecap': 'round', 'vector-effect': 'non-scaling-stroke' }));
    host.append(s);
  }

  // ---- rating line chart with rank bands -----------------------------------
  const RANK_COLORS = {
    'newbie': '#8c8c8c', 'pupil': '#3fae49', 'specialist': '#03a89e', 'expert': '#3b6cf6',
    'candidate master': '#b14fc5', 'master': '#ff9a1f', 'international master': '#ff9a1f',
    'grandmaster': '#e5484d', 'international grandmaster': '#e5484d', 'legendary grandmaster': '#e5484d',
  };

  function rankColor(rating, bands) {
    const b = bands.find(b => rating >= b.min && (b.max == null || rating <= b.max));
    return b ? RANK_COLORS[b.name] : cssVar('--ink-2');
  }

  function ratingChart(host, history, bands) {
    host.replaceChildren();
    if (!history.length) { host.append(el('div', 'empty', 'No rated contests yet.')); return; }
    const W = Math.max(320, host.clientWidth), H = 280, m = { l: 44, r: 16, t: 12, b: 26 };
    const rs = history.map(x => x.newRating);
    const lo = Math.max(0, Math.floor((Math.min(...rs) - 100) / 100) * 100), hi = Math.ceil((Math.max(...rs) + 100) / 100) * 100;
    const t0 = history[0].time, t1 = history[history.length - 1].time;
    const X = t => m.l + (t1 === t0 ? 0.5 : (t - t0) / (t1 - t0)) * (W - m.l - m.r);
    const Y = r => m.t + (1 - (r - lo) / (hi - lo)) * (H - m.t - m.b);
    const s = svg('svg', { viewBox: `0 0 ${W} ${H}`, width: W, height: H, class: 'chart' });

    // rank bands
    bands.forEach(b => {
      const top = Math.min(hi, b.max == null ? hi : b.max + 1), bot = Math.max(lo, b.min);
      if (top <= bot) return;
      s.append(svg('rect', { x: m.l, y: Y(top), width: W - m.l - m.r, height: Y(bot) - Y(top), fill: RANK_COLORS[b.name], opacity: 0.16 }));
    });
    // grid + y labels
    const step = (hi - lo) > 800 ? 200 : 100;
    for (let r = lo; r <= hi; r += step) {
      s.append(svg('line', { x1: m.l, x2: W - m.r, y1: Y(r), y2: Y(r), class: 'grid' }));
      const t = svg('text', { x: m.l - 8, y: Y(r) + 4, 'text-anchor': 'end' }); t.textContent = r; s.append(t);
    }
    // x labels: years / months
    const fmt = new Intl.DateTimeFormat(undefined, { month: 'short', year: '2-digit' });
    const ticks = Math.min(6, history.length);
    for (let i = 0; i < ticks; i++) {
      const tt = t0 + (t1 - t0) * (ticks === 1 ? 0.5 : i / (ticks - 1));
      const t = svg('text', { x: X(tt), y: H - 6, 'text-anchor': i === 0 ? 'start' : i === ticks - 1 ? 'end' : 'middle' });
      t.textContent = fmt.format(new Date(tt * 1000)); s.append(t);
    }
    // line + dots
    const pts = history.map(x => [X(x.time), Y(x.newRating)]);
    s.append(svg('polyline', { points: pts.map(p => p.join(',')).join(' '), fill: 'none', stroke: cssVar('--ink-2'), 'stroke-width': 2, 'stroke-linejoin': 'round' }));
    const dots = history.map((x, i) => {
      const d = svg('circle', { cx: pts[i][0], cy: pts[i][1], r: 4, fill: rankColor(x.newRating, bands), stroke: cssVar('--surface'), 'stroke-width': 2 });
      s.append(d); return d;
    });
    // crosshair + nearest-point hover
    const cross = svg('line', { y1: m.t, y2: H - m.b, class: 'cross', opacity: 0 });
    s.append(cross);
    const hit = svg('rect', { x: m.l, y: 0, width: W - m.l - m.r, height: H, fill: 'transparent' });
    s.append(hit);
    let last = -1;
    hit.addEventListener('mousemove', e => {
      const box = s.getBoundingClientRect(), px = (e.clientX - box.left) * (W / box.width);
      let best = 0;
      pts.forEach((p, i) => { if (Math.abs(p[0] - px) < Math.abs(pts[best][0] - px)) best = i; });
      if (last >= 0) dots[last].setAttribute('r', 4);
      dots[best].setAttribute('r', 6); last = best;
      cross.setAttribute('x1', pts[best][0]); cross.setAttribute('x2', pts[best][0]); cross.setAttribute('opacity', 1);
      const x = history[best];
      showTip(e, [x.contestName, `${x.newRating}  (${x.delta >= 0 ? '+' : ''}${x.delta})`, `rank ${x.rank} · ${new Date(x.time * 1000).toLocaleDateString()}`]);
    });
    hit.addEventListener('mouseleave', () => { hideTip(); cross.setAttribute('opacity', 0); if (last >= 0) dots[last].setAttribute('r', 4); last = -1; });
    host.append(s);
  }

  // ---- activity calendar -----------------------------------------------------
  function calendar(host, days) {
    host.replaceChildren();
    const wrap = el('div', 'cal-wrap');
    const months = el('div', 'cal-months');
    const grid = el('div', 'cal');
    const first = new Date(days[0].date + 'T00:00:00');
    const pad = first.getDay();
    for (let i = 0; i < pad; i++) { const c = el('span', 'cal-pad'); grid.append(c); }
    const max = Math.max(1, ...days.map(d => d.submissions));
    let lastMonth = -1;
    const mfmt = new Intl.DateTimeFormat(undefined, { month: 'short' });
    days.forEach((d, i) => {
      const c = el('span');
      if (d.submissions) {
        const lv = Math.min(4, Math.ceil(d.submissions / max * 4));
        c.style.background = `var(--heat-${lv})`;
      }
      hover(c, () => [new Date(d.date + 'T00:00:00').toDateString(), `${d.submissions} submission${d.submissions === 1 ? '' : 's'}`, `${d.solved} new problem${d.solved === 1 ? '' : 's'} solved`]);
      grid.append(c);
      const dt = new Date(d.date + 'T00:00:00');
      if (dt.getDate() <= 7 && dt.getDay() === 0 && dt.getMonth() !== lastMonth) {
        const col = Math.floor((i + pad) / 7);
        const lab = el('span', null, mfmt.format(dt));
        lab.style.gridColumn = String(col + 1);
        months.append(lab);
        lastMonth = dt.getMonth();
      }
    });
    wrap.append(months, grid);
    host.append(wrap);
    // Size the squares so a year fills the card (between 10px and 16px).
    const cols = Math.ceil((days.length + pad) / 7);
    const fit = () => {
      const w = host.clientWidth;
      if (!w) return;
      const size = Math.max(10, Math.min(16, Math.floor((w - (cols - 1) * 3) / cols)));
      wrap.style.setProperty('--cell', size + 'px');
      wrap.scrollLeft = wrap.scrollWidth;
    };
    requestAnimationFrame(fit);
    if (window.ResizeObserver) new ResizeObserver(fit).observe(host);
  }

  // ---- heatmap grid (HTML) -------------------------------------------------
  // value(cell) -> number; max for colour scaling; label(cell) -> text in the cell
  function heatmap(host, data, opts) {
    host.replaceChildren();
    if (!data.rows.length) { host.append(el('div', 'empty', 'No problems match these filters.')); return; }
    const vals = data.cells.flat().map(opts.value).filter(v => v != null);
    const max = opts.max != null ? opts.max : Math.max(1, ...vals);
    const table = el('div', 'hm');
    table.style.gridTemplateColumns = `minmax(64px, max-content) repeat(${data.cols.length}, minmax(30px, 1fr))`;
    table.append(el('div', 'hm-corner', opts.corner || ''));
    data.cols.forEach(c => table.append(el('div', 'hm-col', String(c))));
    data.rows.forEach((r, i) => {
      table.append(el('div', 'hm-row', r));
      data.cols.forEach((c, j) => {
        const cell = data.cells[i][j];
        const v = opts.value(cell);
        const d = el('div', 'hm-cell');
        if (!cell.total) d.classList.add('none');
        else if (v != null && v > 0) {
          const col = ramp(opts.sqrt ? Math.sqrt(v / max) : v / max);
          d.style.background = col.bg;
          d.style.color = col.light ? '#0d1117' : '#fff';
        }
        d.textContent = cell.total ? opts.label(cell) : '';
        hover(d, () => [`${r} · ${c}`, `${cell.total} problems`, `${cell.solved} solved · ${cell.attempted} attempted · ${cell.unseen} unseen`]);
        table.append(d);
      });
    });
    host.append(table);
  }

  // ---- horizontal bars (HTML) ------------------------------------------------
  function bars(host, items, opts) {
    host.replaceChildren();
    const list = el('div', 'bars');
    items.forEach(it => {
      const row = el('div', 'bar-row');
      row.append(el('div', 'bar-label', opts.label(it)));
      const track = el('div', 'bar-track');
      const fill = el('div', 'bar-fill');
      fill.style.width = (Math.max(0, Math.min(1, opts.value(it))) * 100).toFixed(1) + '%';
      track.append(fill);
      row.append(track);
      row.append(el('div', 'bar-val', opts.text(it)));
      hover(row, () => opts.tip(it));
      list.append(row);
    });
    host.append(list);
  }

  window.Charts = { el, sparkline, ratingChart, rankColor, RANK_COLORS, calendar, heatmap, bars, hover, hideTip };
})();
