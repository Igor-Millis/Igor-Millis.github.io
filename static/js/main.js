/* Global behaviour: theme, command palette, copy, reveal-on-scroll, hero field. */
(() => {
  "use strict";
  const root = document.documentElement;
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));

  /* ---------- toast ---------- */
  const toast = $(".toast");
  let toastTimer;
  function say(msg) {
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add("on");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("on"), 1800);
  }

  /* ---------- theme ---------- */
  function toggleTheme() {
    const next = root.dataset.theme === "light" ? "dark" : "light";
    root.dataset.theme = next;
    try { localStorage.setItem("theme", next); } catch (e) { /* storage unavailable */ }
    document.dispatchEvent(new CustomEvent("themechange"));
  }
  $$("[data-theme-toggle]").forEach((b) => b.addEventListener("click", toggleTheme));


  /* ---------- command palette ---------- */
  const data = JSON.parse(($("#cmdk-data") || {}).textContent || '{"items":[]}');
  const dlg = $(".cmdk");
  const input = dlg && $("input", dlg);
  const list = dlg && $("ul", dlg);
  let shown = [], sel = 0, lastFocus = null;

  function copy(text) {
    const done = () => say(data.copied || "Copied");
    if (navigator.clipboard) navigator.clipboard.writeText(text).then(done, () => {});
    else done();
  }
  function run(item) {
    close();
    if (item.action === "theme") toggleTheme();
    else if (item.action === "copy") copy(item.value);
    else if (item.href) item.ext ? window.open(item.href, "_blank", "noopener") : (location.href = item.href);
  }
  function render() {
    const q = input.value.trim().toLowerCase();
    shown = data.items.filter((i) => !q || (i.label + " " + (i.hint || "")).toLowerCase().includes(q));
    sel = Math.min(sel, Math.max(0, shown.length - 1));
    list.innerHTML = "";
    shown.forEach((it, i) => {
      const li = document.createElement("li");
      li.setAttribute("role", "option");
      li.setAttribute("aria-selected", i === sel ? "true" : "false");
      const a = document.createElement("span"); a.textContent = it.label;
      const b = document.createElement("small"); b.textContent = (it.hint || "") + (it.ext ? " ↗" : "");
      li.append(a, b);
      li.addEventListener("click", () => run(it));
      li.addEventListener("mousemove", () => { if (sel !== i) { sel = i; mark(); } });
      list.appendChild(li);
    });
  }
  function mark() {
    $$("li", list).forEach((li, i) => li.setAttribute("aria-selected", i === sel ? "true" : "false"));
    const cur = list.children[sel];
    if (cur) cur.scrollIntoView({ block: "nearest" });
  }
  function open() {
    if (!dlg) return;
    lastFocus = document.activeElement;
    dlg.hidden = false; dlg.classList.add("open");
    input.value = ""; sel = 0; render(); input.focus();
  }
  function close() {
    if (!dlg || dlg.hidden) return;
    dlg.classList.remove("open"); dlg.hidden = true;
    if (lastFocus) lastFocus.focus();
  }
  if (dlg) {
    $$("[data-cmdk]").forEach((b) => b.addEventListener("click", open));
    dlg.addEventListener("click", (e) => { if (e.target === dlg) close(); });
    input.addEventListener("input", () => { sel = 0; render(); });
    input.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown") { sel = (sel + 1) % Math.max(1, shown.length); mark(); e.preventDefault(); }
      else if (e.key === "ArrowUp") { sel = (sel - 1 + shown.length) % Math.max(1, shown.length); mark(); e.preventDefault(); }
      else if (e.key === "Enter" && shown[sel]) { run(shown[sel]); e.preventDefault(); }
      else if (e.key === "Escape") close();
      else if (e.key === "Tab") e.preventDefault();
    });
    document.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); dlg.hidden ? open() : close(); return; }
      const typing = /input|textarea|select/i.test((e.target.tagName || "")) || e.target.isContentEditable;
      if (typing || e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === "/") { e.preventDefault(); open(); }
      else if (e.key === "t") toggleTheme();
    });
  }

  /* ---------- copy email links (desktop: copy + still allow mailto on second click) ---------- */
  $$("[data-copy]").forEach((a) => a.addEventListener("click", (e) => {
    if (a.dataset.copied) return;
    if (window.matchMedia("(hover: hover)").matches) {
      e.preventDefault(); a.dataset.copied = "1"; copy(a.dataset.copy);
    }
  }));

  /* ---------- reveal on scroll ---------- */
  const rv = $$(".rv");
  const revealAll = () => rv.forEach((el) => el.classList.add("in"));
  if (!reduce && "IntersectionObserver" in window) {
    let fired = false;
    const io = new IntersectionObserver((es) => {
      fired = true;
      es.forEach((en) => { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0 });
    rv.forEach((el) => io.observe(el));
    // Safety net: never leave content invisible if the observer does not run (e.g. throttled tabs).
    setTimeout(() => { if (!fired) revealAll(); }, 1500);
  } else revealAll();

  /* ---------- hero: particles descending a loss surface ---------- */
  const cv = $("#field");
  if (cv) field(cv);

  function field(canvas) {
    const ctx = canvas.getContext("2d");
    const stepEl = $("#step"), lossEl = $("#loss");
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    let W = 0, H = 0, P = [], t = 0, running = false, visible = true, raf = 0;
    let bg = "#0b0e11", rgb = "108,196,201";
    const mouse = { x: -9, y: -9, on: false };

    // Loss: sum of Gaussian wells drifting slowly + weak quadratic bowl. Coordinates in [-1,1]^2.
    const wells = [
      { x: 0.42, y: -0.18, a: 1.0, s: 0.22, ph: 0.0 },
      { x: -0.35, y: 0.32, a: 0.8, s: 0.26, ph: 2.1 },
      { x: 0.05, y: 0.45, a: 0.55, s: 0.18, ph: 4.2 },
      { x: 0.78, y: 0.4, a: 0.6, s: 0.2, ph: 1.3 },
    ];
    function grad(x, y) {
      let gx = 0.3 * x, gy = 0.3 * y, L = 0.15 * (x * x + y * y);
      for (const w of wells) {
        const cx = w.x + 0.08 * Math.sin(t * 0.0021 + w.ph), cy = w.y + 0.08 * Math.cos(t * 0.0017 + w.ph);
        const dx = x - cx, dy = y - cy, s2 = w.s * w.s, e = w.a * Math.exp(-(dx * dx + dy * dy) / (2 * s2));
        L -= e; gx += (e * dx) / s2; gy += (e * dy) / s2;
      }
      if (mouse.on) { // cursor = a hill: particles flow away from it
        const dx = x - mouse.x, dy = y - mouse.y, s2 = 0.012, e = 0.9 * Math.exp(-(dx * dx + dy * dy) / (2 * s2));
        L += e; gx -= (e * dx) / s2; gy -= (e * dy) / s2;
      }
      return [gx, gy, L];
    }
    const toPx = (v, n) => ((v + 1) / 2) * n;
    const toU = (p, n) => (p / n) * 2 - 1;
    function spawn(p) { p.x = Math.random() * 2 - 1; p.y = Math.random() * 2 - 1; p.age = 0; p.life = 220 + Math.random() * 380; return p; }

    function colors() {
      const cs = getComputedStyle(root);
      bg = cs.getPropertyValue("--bg").trim() || bg;
      rgb = cs.getPropertyValue("--particle").trim() || rgb;
      ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
    }
    function resize() {
      const r = canvas.getBoundingClientRect();
      W = canvas.width = Math.round(r.width * dpr);
      H = canvas.height = Math.round(r.height * dpr);
      const n = Math.min(420, Math.round((r.width * r.height) / 3200));
      P = Array.from({ length: n }, () => spawn({}));
      colors();
    }
    function frame() {
      t++;
      const aspect = W / H;
      ctx.globalAlpha = 1;
      ctx.fillStyle = bg; ctx.globalAlpha = 0.09; ctx.fillRect(0, 0, W, H);
      ctx.globalAlpha = 1;
      let sumL = 0;
      for (const p of P) {
        const [gx, gy, L] = grad(p.x * aspect * 0.6, p.y);
        sumL += L;
        const ox = toPx(p.x, W), oy = toPx(p.y, H);
        const lr = 0.0045;
        p.x -= lr * gx + (Math.random() - 0.5) * 0.0012; // SGD: gradient step + small noise
        p.y -= lr * gy + (Math.random() - 0.5) * 0.0012;
        p.age++;
        const nx = toPx(p.x, W), ny = toPx(p.y, H);
        const speed = Math.min(1, Math.hypot(gx, gy) * 0.6);
        ctx.strokeStyle = `rgba(${rgb},${0.18 + 0.55 * speed})`;
        ctx.lineWidth = dpr;
        ctx.beginPath(); ctx.moveTo(ox, oy); ctx.lineTo(nx, ny); ctx.stroke();
        if (p.age > p.life || Math.abs(p.x) > 1.05 || Math.abs(p.y) > 1.05) spawn(p);
      }
      if (t % 12 === 0) {
        if (stepEl) stepEl.textContent = t;
        if (lossEl) lossEl.textContent = (sumL / P.length).toFixed(3);
      }
    }
    function loop() { if (!running) return; frame(); raf = requestAnimationFrame(loop); }
    function start() { if (running || reduce || !visible || document.hidden) return; running = true; raf = requestAnimationFrame(loop); }
    function stop() { running = false; cancelAnimationFrame(raf); }

    resize();
    if (reduce) { for (let i = 0; i < 260; i++) frame(); return; }
    window.addEventListener("resize", () => { stop(); resize(); start(); });
    document.addEventListener("themechange", colors);
    document.addEventListener("visibilitychange", () => (document.hidden ? stop() : start()));
    new IntersectionObserver(([e]) => { visible = e.isIntersecting; visible ? start() : stop(); }).observe(canvas);
    const hero = canvas.parentElement;
    hero.addEventListener("pointermove", (e) => {
      const r = canvas.getBoundingClientRect();
      mouse.x = toU(e.clientX - r.left, r.width) * (W / H) * 0.6;
      mouse.y = toU(e.clientY - r.top, r.height);
      mouse.on = true;
    });
    hero.addEventListener("pointerleave", () => (mouse.on = false));
    start();
  }
})();
