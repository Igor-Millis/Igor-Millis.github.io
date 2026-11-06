/* Threshold explorer: precision / recall / F1 / implied cost ratio along a real curve. */
(() => {
  "use strict";
  document.querySelectorAll("[data-th]").forEach((fig) => {
    const { curve, lang } = JSON.parse(fig.dataset.th);
    const svg = fig.querySelector("svg");
    const g = JSON.parse(svg.dataset.geom);
    const range = fig.querySelector('input[type="range"]');
    const out = fig.querySelector("output");
    const reads = fig.querySelectorAll("[data-out]");
    const cursor = svg.querySelector("[data-cursor]");
    const line = cursor.querySelector("line");
    const pts = cursor.querySelectorAll("[data-p]");
    const fmt = (v, d) => {
      const s = v.toFixed(d);
      return lang === "pt" ? s.replace(".", ",") : s;
    };
    const X = (v) => g.l + ((v - g.x0) / (g.x1 - g.x0)) * (g.w - g.l - g.r);
    const Y = (v) => g.t + (1 - v) * (g.h - g.t - g.b);

    function update() {
      const r = curve[+range.value];
      const [tau, prec, rec, f1] = r;
      out.textContent = fmt(tau, 2);
      reads[0].textContent = fmt(prec, 3);
      reads[1].textContent = fmt(rec, 3);
      reads[2].textContent = fmt(f1, 3);
      reads[3].textContent = fmt((1 - tau) / tau, 2) + "×";
      const x = X(tau);
      line.setAttribute("x1", x); line.setAttribute("x2", x);
      pts.forEach((p) => {
        p.setAttribute("cx", x);
        p.setAttribute("cy", Y(r[+p.dataset.p]));
      });
    }
    range.addEventListener("input", update);
    update();
  });
})();
