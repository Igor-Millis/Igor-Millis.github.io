/* EduData page: pipeline tabs and the query replay console. */
(() => {
  "use strict";
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  /* ---------- pipeline tabs ---------- */
  const pipe = document.querySelector("[data-pipe]");
  if (pipe) {
    const tabs = Array.from(pipe.querySelectorAll('[role="tab"]'));
    const panels = Array.from(document.querySelectorAll("[data-pipe-panels] [role=tabpanel]"));
    const select = (i, focus) => {
      tabs.forEach((t, j) => { t.setAttribute("aria-selected", j === i ? "true" : "false"); t.tabIndex = j === i ? 0 : -1; });
      panels.forEach((p, j) => (p.hidden = j !== i));
      if (focus) tabs[i].focus();
    };
    tabs.forEach((t, i) => {
      t.addEventListener("click", () => select(i));
      t.addEventListener("keydown", (e) => {
        if (e.key === "ArrowRight") select((i + 1) % tabs.length, true);
        if (e.key === "ArrowLeft") select((i - 1 + tabs.length) % tabs.length, true);
      });
    });
    select(0);
  }

  /* ---------- query replay ---------- */
  const box = document.querySelector("[data-replay]");
  if (!box) return;
  const data = JSON.parse(box.querySelector('script[type="application/json"]').textContent);
  const btns = Array.from(box.querySelectorAll(".replay-q button"));
  const steps = Array.from(box.querySelectorAll(".step"));
  const verdict = box.querySelector("[data-verdict]");
  let timers = [];

  const pretty = (obj) =>
    JSON.stringify(obj, null, 2).replace(/\[\s+([^\[\]{}]*?)\s+\]/g, (_, inner) => "[" + inner.replace(/\s*\n\s*/g, " ") + "]");
  const hlJSON = (obj) =>
    esc(pretty(obj))
      .replace(/(&quot;[^&]*?&quot;)(\s*:)/g, '<span class="k">$1</span>$2')
      .replace(/:\s(&quot;.*?&quot;)/g, ': <span class="s">$1</span>')
      .replace(/\b(true|false|null)\b/g, '<span class="kw">$1</span>');
  const KW = /\b(SELECT|FROM|WHERE|AND|OR|IN|AS|GROUP BY ALL|ORDER BY ALL|sum|bool_or|string_agg|min|list_contains|DISTINCT)\b/g;
  const hlSQL = (sql) => esc(sql).replace(KW, '<span class="kw">$1</span>').replace(/\?/g, '<span class="k">?</span>');

  function show(i) {
    const it = data.items[i];
    timers.forEach(clearTimeout); timers = [];
    btns.forEach((b, j) => b.setAttribute("aria-pressed", j === i ? "true" : "false"));
    steps.forEach((s) => s.classList.remove("on"));
    verdict.classList.remove("warn");
    steps[0].innerHTML = hlJSON(it.contract);
    if (it.ok) {
      steps[1].innerHTML = hlSQL(it.sql) + "\n\n<span class=\"k\">params</span> = " + esc(it.params);
      steps[2].innerHTML = '<span class="s">✓ validated</span>\n<span class="s">✓ read_only</span>\n<span class="s">✓ ' + esc(it.mart) + "</span>";
      verdict.innerHTML = data.ok.replace("{mart}", esc(it.mart)) + (it.ranking ? " " + data.rank : "");
    } else {
      steps[1].innerHTML = '<span class="kw">— not executed —</span>';
      steps[2].innerHTML = '<span class="kw">pede_esclarecimento: true</span>';
      verdict.textContent = data.why[it.why];
      verdict.classList.add("warn");
    }
    steps.forEach((s, j) => {
      if (reduce) s.classList.add("on");
      else timers.push(setTimeout(() => s.classList.add("on"), 120 + j * 260));
    });
  }
  btns.forEach((b, i) => b.addEventListener("click", () => show(i)));
  show(0);
})();
