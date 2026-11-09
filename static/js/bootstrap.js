/* Resampling by hand: one NP resample (with replacement) and one P resample (from Exp(xbar)) per draw. */
(() => {
  "use strict";
  const fig = document.querySelector("[data-boot]");
  if (!fig) return;
  const { lang, x } = JSON.parse(fig.dataset.boot);
  const svg = fig.querySelector("[data-svg]");
  const outs = fig.querySelectorAll("[data-o]");
  const NS = "http://www.w3.org/2000/svg";
  const W = 640, n = x.length, XMAX = 12, BINS = 48, HI = 10;
  const xbar = x.reduce((a, b) => a + b, 0) / n;
  let stat = "mean", np = [], p = [], last = null;

  const loc = (v, d) => { const s = v.toFixed(d); return lang === "pt" ? s.replace(".", ",") : s; };
  const intl = (v) => Math.round(v).toLocaleString(lang === "pt" ? "pt-BR" : "en-US");
  function mulberry32(a) {
    return () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }
  let rnd = mulberry32(2026);
  const el = (name, attrs, text) => {
    const e = document.createElementNS(NS, name);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (text !== undefined) e.textContent = text;
    return e;
  };
  const median = (a) => { const s = [...a].sort((u, v) => u - v), m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };
  const mean = (a) => a.reduce((u, v) => u + v, 0) / a.length;
  const f = (a) => (stat === "mean" ? mean(a) : median(a));
  const sd = (a) => { const m = mean(a); return Math.sqrt(a.reduce((u, v) => u + (v - m) ** 2, 0) / (a.length - 1)); };
  const quant = (a, q) => { const s = [...a].sort((u, v) => u - v), h = (s.length - 1) * q, lo = Math.floor(h);
    return s[lo] + (h - lo) * ((s[Math.min(lo + 1, s.length - 1)]) - s[lo]); };

  function draw(k) {
    for (let r = 0; r < k; r++) {
      const idx = Array.from({ length: n }, () => Math.floor(rnd() * n));
      const xs = idx.map((i) => x[i]);
      const ps = Array.from({ length: n }, () => -xbar * Math.log(1 - rnd()));
      np.push(xs); p.push(ps);
      last = { idx, ps };
    }
    render();
  }

  function hist(vals, x0, y0, w, h, color, title, obs) {
    const g = el("g");
    const counts = new Array(BINS).fill(0);
    for (const v of vals) { const b = Math.floor((v / HI) * BINS); if (b >= 0 && b < BINS) counts[b]++; }
    const cmax = Math.max(1, ...counts), bw = w / BINS;
    g.append(el("text", { x: x0, y: y0 - 8, class: "t-strong" }, title));
    g.append(el("line", { class: "ax", x1: x0, x2: x0 + w, y1: y0 + h, y2: y0 + h }));
    counts.forEach((c, i) => {
      if (!c) return;
      const bh = (c / cmax) * (h - 4);
      g.append(el("rect", { x: x0 + i * bw + 0.5, y: y0 + h - bh, width: bw - 1, height: bh, fill: color, opacity: 0.6 }));
    });
    const X = (v) => x0 + (v / HI) * w;
    g.append(el("line", { x1: X(obs), x2: X(obs), y1: y0, y2: y0 + h, stroke: "var(--text)", "stroke-width": 1.25 }));
    for (let v = 0; v <= HI; v += 2) g.append(el("text", { x: X(v), y: y0 + h + 16, "text-anchor": "middle" }, String(v)));
    return g;
  }

  function render() {
    svg.textContent = "";
    const L = 20, R = 14, X = (v) => L + (v / XMAX) * (W - L - R);
    // row 1: the data, with counts of the last NP resample
    const y1 = 60, y2 = 108;
    svg.append(el("text", { x: L, y: 14, class: "t-strong" }, lang === "pt" ? "dados (x) e a última reamostra NP" : "data (x) and the last NP resample"));
    svg.append(el("line", { class: "ax", x1: L, x2: W - R, y1, y2: y1 }));
    // counts per distinct value (5.1 appears twice in the data), labels staggered on three levels
    const counts = new Map();
    x.forEach((v) => counts.set(v, 0));
    if (last) last.idx.forEach((i) => counts.set(x[i], counts.get(x[i]) + 1));
    [...counts.keys()].sort((a, b) => a - b).forEach((v, rank) => {
      const c = counts.get(v), on = c > 0;
      svg.append(el("circle", { cx: X(v), cy: y1, r: 4.5, fill: on ? "var(--accent)" : "var(--bg)", stroke: on ? "var(--accent)" : "var(--text-3)", "stroke-width": 1.25, opacity: on ? 1 : 0.7 }));
      if (on) svg.append(el("text", { x: X(v), y: y1 - 10 - (rank % 3) * 10, "text-anchor": "middle", class: "t-accent" }, "×" + c));
    });
    svg.append(el("text", { x: L, y: y2 - 18, class: "t-strong" }, (lang === "pt" ? "última reamostra P: Exp(média " : "last P resample: Exp(mean ") + loc(xbar, 1) + ")"));
    svg.append(el("line", { class: "ax", x1: L, x2: W - R, y1: y2, y2 }));
    if (last) last.ps.forEach((v) => { if (v <= XMAX) svg.append(el("circle", { cx: X(v), cy: y2, r: 4, fill: "var(--signal)", opacity: 0.8 })); });
    for (let v = 0; v <= XMAX; v += 2) svg.append(el("text", { x: X(v), y: y2 + 16, "text-anchor": "middle" }, String(v)));
    // row 2: histograms of the statistic
    const tn = np.map(f), tp = p.map(f), obs = f(x);
    const name = stat === "mean" ? (lang === "pt" ? "média" : "mean") : (lang === "pt" ? "mediana" : "median");
    svg.append(hist(tn, 40, 170, 260, 170, "var(--accent)", "NP · " + name + (lang === "pt" ? " de cada reamostra" : " of each resample"), obs));
    svg.append(hist(tp, 360, 170, 260, 170, "var(--signal)", "P · " + name + (lang === "pt" ? " de cada reamostra" : " of each resample"), obs));
    // readouts
    const B = np.length;
    outs[0].textContent = intl(B);
    outs[1].textContent = B > 1 ? loc(sd(tn), 3) : "—";
    outs[2].textContent = B > 1 ? loc(sd(tp), 3) : "—";
    outs[3].textContent = B >= 40 ? `[${loc(quant(tn, 0.025), 2)}${lang === "pt" ? ";" : ","} ${loc(quant(tn, 0.975), 2)}]` : "—";
  }

  fig.querySelectorAll("[data-add]").forEach((b) => b.addEventListener("click", () => draw(+b.dataset.add)));
  fig.querySelector("[data-reset]").addEventListener("click", () => { np = []; p = []; last = null; rnd = mulberry32(2026); render(); });
  fig.querySelectorAll("[data-stat]").forEach((r) => r.addEventListener("change", () => { stat = r.value; render(); }));
  render();
})();
