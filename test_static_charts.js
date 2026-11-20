// Run with page scripting disabled; agent-browser eval itself remains available through CDP.
(() => {
  if (document.body.classList.contains("zoomable")) return "Static checks require page scripting disabled";
  const assert = (condition, message) => { if (!condition) throw new Error(message); };
  for (const mode of ["effort", "cost"]) {
    document.querySelector(`label[for="x-${mode}"]`).click();
    const plots = [...document.querySelectorAll(".panel .plot")].filter(plot => plot.getBoundingClientRect().width);
    assert(plots.length > 80, `Without JavaScript, ${mode} must still render the benchmark collection, got ${plots.length}`);
    const outside = [];
    for (const plot of plots) {
      const card = plot.closest(".panel").getBoundingClientRect();
      const svg = plot.querySelector("svg.chart");
      const scale = svg.getBoundingClientRect().width / svg.viewBox.baseVal.width;
      for (const label of svg.querySelectorAll("text")) {
        const box = label.getBoundingClientRect();
        if (!box.width) continue;
        if (box.left < card.left - 0.5 || box.right > card.right + 0.5 || box.top < card.top - 0.5 || box.bottom > card.bottom + 0.5) {
          outside.push(`${plot.closest(".panel").querySelector("h3").textContent}: ${label.textContent}`);
        }
        const size = parseFloat(getComputedStyle(label).fontSize) * scale;
        assert(size >= 8.5 && (innerWidth >= 700 || Math.abs(size - 9) <= 0.5),
          `Without JavaScript, ${label.textContent} must retain 9px phone text, got ${size.toFixed(1)}px`);
      }
    }
    assert(!outside.length, `Without JavaScript, ${mode} labels must stay inside cards: ${outside.slice(0, 10).join(", ")}`);
    const vals = plots.find(plot => plot.dataset.metric === "vals-index-vals-reasoning-study");
    const ticks = [...vals.querySelectorAll(".score-axis text")].map(label => Number(label.textContent));
    assert(Math.max(...ticks) - Math.min(...ticks) <= 25, `Static ${mode} must fit the Vals score range, got ${ticks}`);
  }
  document.querySelector('label[for="x-effort"]').click();
  for (const input of document.querySelectorAll('input[id^="show-"]')) input.checked = input.value === "opus-5-5";
  const starts = [...document.querySelectorAll('.panel[data-chart="aa-intelligence-index"] .start text')]
    .filter(label => label.getBoundingClientRect().width && label.textContent === "34.8");
  assert(starts.length === 1, "The no-JavaScript model filter must retain the remaining shared start score");
  for (const input of document.querySelectorAll('input[id^="show-"]')) input.checked = true;
  return "No-JavaScript charts render both views with contained, readable labels and fitted default axes";
})();
