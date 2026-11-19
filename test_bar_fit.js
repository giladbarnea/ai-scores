// Run in the generated page: agent-browser --session ai-scores-test eval --stdin < test_bar_fit.js
(async () => {
  const assert = (condition, message) => { if (!condition) throw new Error(message); };
  const settle = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(resolve))));
  const visible = node => node.getClientRects().length && getComputedStyle(node).display !== "none";
  assert(getComputedStyle(document.documentElement).colorScheme === "dark"
    && getComputedStyle(document.body).backgroundColor === "rgb(13, 13, 13)",
    "The page must stay dark regardless of the device appearance setting");
  const panel = document.querySelector('.panel[data-chart="vals-index"]');
  const plot = () => panel.querySelector(":scope > .plot");
  const bars = () => [...plot().querySelectorAll(".bar")].filter(visible);
  const centers = () => bars().map(bar => { const box = bar.getBoundingClientRect(); return box.y + box.height / 2; }).sort((a, b) => a - b);
  const setModels = selected => document.querySelectorAll('input[id^="show-"]').forEach(input => {
    if (input.checked !== selected.includes(input.value)) input.click();
  });
  document.querySelector('label[for="x-effort"]').click();
  document.querySelector("#models-all").click();
  document.querySelector("#levels-all").click();
  await settle();
  const fullHeight = panel.getBoundingClientRect().height;
  const fullBarHeight = bars()[0].getBoundingClientRect().height;
  const fullCenters = centers();
  const rowSpacing = fullCenters[1] - fullCenters[0];
  setModels(["gemini-4-neon", "gpt-6-2-sol", "gemini-4-carbon"]);
  await settle();
  const selected = centers();
  assert(bars().length === 3, `The three selected models must have three Vals bars, got ${bars().length}`);
  assert(panel.getBoundingClientRect().height < fullHeight * 0.65,
    `The three-bar card must shrink instead of keeping hidden rows: full ${fullHeight}, filtered ${panel.getBoundingClientRect().height}`);
  assert(selected.slice(1).every((center, index) => Math.abs(center - selected[index] - rowSpacing) < 0.5),
    `Visible bars must close their hidden-row gaps, got centers ${selected.join(", ")}`);
  assert(Math.abs(bars()[0].getBoundingClientRect().height - fullBarHeight) < 0.5,
    "Compacting rows must not stretch or squash the bars");
  const lowestBar = Math.max(...bars().map(bar => bar.getBoundingClientRect().bottom));
  const axisNumbers = [...plot().querySelectorAll(".bar-axis text")].filter(visible);
  assert(axisNumbers.every(label => label.getBoundingClientRect().top > lowestBar
    && label.getBoundingClientRect().bottom < panel.getBoundingClientRect().bottom),
    "Compacting bars must keep the score-axis labels below the bars and inside the card");
  document.querySelector("#models-all").click();
  document.querySelector("#levels-none").click();
  document.querySelector('label[for="level-high"]').click();
  await settle();
  assert(bars().length === 2 && panel.getBoundingClientRect().height < fullHeight * 0.6,
    "The thinking-level filter must compact the two high-effort bars too");
  document.querySelector('label[for="x-cost"]').click();
  await settle();
  assert(plot().querySelectorAll(".marker").length > 0 && !plot().querySelector(".bar"),
    "Switching to Cost must retain the scatter plot, not reuse compacted bar geometry");
  document.querySelector('label[for="x-effort"]').click();
  document.querySelector("#levels-all").click();
  await settle();
  assert(bars().length === 10 && Math.abs(panel.getBoundingClientRect().height - fullHeight) < 0.5,
    "All models and levels must restore the exact full card height");
  for (const card of document.querySelectorAll(".panel:not([hidden])")) {
    const bounds = card.getBoundingClientRect();
    const names = card.querySelectorAll(":scope > .plot:not([data-metric]) .name text");
    const outside = [...names].filter(visible).filter(name => {
      const box = name.getBoundingClientRect();
      return box.left < bounds.left + 4 || box.right > bounds.right - 4;
    });
    assert(!outside.length, `Bar model labels must stay inside ${card.querySelector("h3").textContent}: ${outside.map(node => node.textContent).join(", ")}`);
  }
  assert(!document.querySelector(".missing"), "Sparse cards must not list models without scores");
  return "Bar fit checks passed: model and level compaction, fixed bar size, Cost switch, exact reset and contained model labels";
})();
