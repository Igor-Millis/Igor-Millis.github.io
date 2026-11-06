/* Bankroll simulator: 200 bettors placing 1-unit bets at odds 2/(1+m) on a 50/50 event. */
(() => {
  "use strict";
  const fig = document.querySelector("[data-bets]");
  if (!fig) return;
  const { lang } = JSON.parse(fig.dataset.bets);
  const svg = fig.querySelector("[data-svg]");
  const mIn = fig.querySelector("[data-m]"), nIn = fig.querySelector("[data-n]");
  const mOut = fig.querySelector("[data-mo]"), nOut = fig.querySelector("[data-no]");
  const outs = fig.querySelectorAll("[data-o]");
  const NS = "http://www.w3.org/2000/svg";
  const W = 640, H = 300, L = 52, R = 14, T = 12, B = 30, PEOPLE = 200, SHOW = 40, P = 0.5;
  let seed = 7;

  const loc = (x, d) => { const s = x.toFixed(d); return lang === "pt" ? s.replace(".", ",") : s; };
  const intl = (x) => Math.round(x).toLocaleString(lang === "pt" ? "pt-BR" : "en-US");
  const nFrom = (v) => Math.round(Math.pow(10, 1 + (3 * v) / 100)); // 10 .. 10,000
  function mulberry32(a) {
    return () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }
  const el = (name, attrs) => { const e = document.createElementNS(NS, name); for (const k in attrs) e.setAttribute(k, attrs[k]); return e; };

  function run() {
    const m = +mIn.value / 100, n = nFrom(+nIn.value), odds = 2 / (1 + m);
    const mu = P * odds - 1, sd = odds * Math.sqrt(P * (1 - P));
    mOut.textContent = loc(m * 100, 1) + "%";
    nOut.textContent = intl(n);
    const rnd = mulberry32(seed);
    const step = Math.max(1, Math.floor(n / 160));
    const finals = new Float64Array(PEOPLE), paths = [];
    for (let i = 0; i < PEOPLE; i++) {
      let s = 0; const path = i < SHOW ? [[0, 0]] : null;
      for (let k = 1; k <= n; k++) {
        s += rnd() < P ? odds - 1 : -1;
        if (path && (k % step === 0 || k === n)) path.push([k, s]);
      }
      finals[i] = s; if (path) paths.push(path);
    }
    // scale
    const band = 2.2 * sd * Math.sqrt(n);
    let lo = Math.min(mu * n - band, ...finals), hi = Math.max(band * 0.6, ...finals, 1);
    lo = Math.min(lo, -1); const X = (k) => L + (k / n) * (W - L - R), Y = (v) => T + ((hi - v) / (hi - lo)) * (H - T - B);
    svg.textContent = "";
    // grid
    const raw = (hi - lo) / 5, mag = Math.pow(10, Math.floor(Math.log10(raw)));
    const stepY = [1, 2, 5, 10].map((s) => s * mag).find((s) => s >= raw);
    for (let v = Math.ceil(lo / stepY) * stepY; v <= hi; v += stepY) {
      svg.append(el("line", { class: "gl", x1: L, x2: W - R, y1: Y(v), y2: Y(v) }));
      const t = el("text", { x: L - 8, y: Y(v) + 4, "text-anchor": "end" }); t.textContent = intl(v); svg.append(t);
    }
    svg.append(el("line", { class: "ax", x1: L, x2: W - R, y1: Y(0), y2: Y(0) }));
    [0, 0.5, 1].forEach((f) => { const t = el("text", { x: X(f * n), y: H - 10, "text-anchor": f === 0 ? "start" : f === 1 ? "end" : "middle" }); t.textContent = intl(f * n); svg.append(t); });
    // band nμ ± 2σ√n
    const pts = [], low = [];
    for (let j = 0; j <= 60; j++) { const k = (j / 60) * n; pts.push(`${X(k)},${Y(mu * k + 2 * sd * Math.sqrt(k))}`); low.push(`${X(k)},${Y(mu * k - 2 * sd * Math.sqrt(k))}`); }
    svg.append(el("polygon", { points: pts.concat(low.reverse()).join(" "), fill: "var(--accent)", opacity: ".10" }));
    for (const p of paths) svg.append(el("polyline", { points: p.map(([k, s]) => `${X(k)},${Y(s)}`).join(" "), fill: "none", stroke: "var(--text-3)", "stroke-width": 1, opacity: ".5" }));
    svg.append(el("line", { x1: X(0), y1: Y(0), x2: X(n), y2: Y(mu * n), stroke: "var(--accent)", "stroke-width": 1.75 }));
    // readouts
    let ahead = 0, sum = 0, mn = Infinity, mx = -Infinity;
    for (const f of finals) { if (f > 0) ahead++; sum += f; mn = Math.min(mn, f); mx = Math.max(mx, f); }
    outs[0].textContent = loc((100 * ahead) / PEOPLE, 0) + "%";
    outs[1].textContent = intl(sum / PEOPLE) + " u";
    outs[2].textContent = intl(mu * n) + " u";
    outs[3].textContent = `${intl(mn)} / ${intl(mx)}`;
  }
  mIn.addEventListener("input", run);
  nIn.addEventListener("input", run);
  fig.querySelector("[data-rerun]").addEventListener("click", () => { seed = (seed * 48271) % 2147483647; run(); });
  run();
})();
