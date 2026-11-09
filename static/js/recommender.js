/* Adaptive Recommender page: independent tab groups (steps, methods). Without JS every panel stays visible. */
(() => {
  "use strict";
  document.querySelectorAll("[data-pipe]").forEach((pipe) => {
    const id = pipe.getAttribute("data-pipe");
    const tabs = Array.from(pipe.querySelectorAll('[role="tab"]'));
    const box = document.querySelector(`[data-pipe-panels="${id}"]`);
    if (!box) return;
    const panels = Array.from(box.querySelectorAll("[role=tabpanel]"));
    const select = (i, focus) => {
      tabs.forEach((t, j) => { t.setAttribute("aria-selected", j === i ? "true" : "false"); t.tabIndex = j === i ? 0 : -1; });
      panels.forEach((p, j) => (p.hidden = j !== i));
      if (focus) tabs[i].focus();
    };
    tabs.forEach((t, i) => {
      t.addEventListener("click", () => select(i));
      t.addEventListener("keydown", (e) => {
        if (e.key === "ArrowRight") { e.preventDefault(); select((i + 1) % tabs.length, true); }
        if (e.key === "ArrowLeft") { e.preventDefault(); select((i - 1 + tabs.length) % tabs.length, true); }
      });
    });
    select(0);
  });
})();
