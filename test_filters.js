// Run in the generated page: agent-browser --session ai-scores-test eval --stdin < test_filters.js
(async () => {
  if (document.readyState !== "complete") await new Promise(resolve => window.addEventListener("load", resolve, { once: true }));
  const assert = (condition, message) => { if (!condition) throw new Error(message); };
  const settle = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(resolve))));
  const visible = node => {
    for (let parent = node; parent; parent = parent.parentElement) {
      if (getComputedStyle(parent).display === "none") return false;
    }
    return true;
  };
  assert(document.querySelectorAll('input[name="thinking-level"]').length === 6,
    "The page must offer low, medium, high, xhigh, max and Not stated filters");
  document.querySelectorAll('input[id^="show-"]').forEach(input => { if (!input.checked) input.click(); });
  document.querySelector('label[for="x-effort"]').click();
  document.querySelector("#levels-none").click();
  document.querySelector('label[for="level-high"]').click();
  await settle();
  const plot = document.querySelector('.plot[data-metric="aa-intelligence-index"]');
  const markers = [...plot.querySelectorAll(".marker")].filter(visible);
  assert(markers.length === 10, `High-only must show ten AA Index points, got ${markers.length}`);
  assert(markers.some(marker => marker.classList.contains("m-gemini-4-neon")), "Neon's real high point must be filterable");
  assert(markers.every(marker => marker.dataset.level === "high"), "A deselected level still has a visible point");
  const label = plot.querySelector(".filtered-labels .end.m-gpt-6-2-astra text");
  assert(label?.textContent === "60.1", `Astra's high score must replace its max label, got ${label?.textContent}`);
  const plotBounds = plot.getBoundingClientRect();
  const overflowing = [...plot.querySelectorAll(".filtered-labels text")].filter(visible)
    .filter(node => node.getBoundingClientRect().right > plotBounds.right);
  assert(!overflowing.length, `Filtered model names escape the effort chart: ${overflowing.map(node => node.textContent).join(", ")}`);
  const series = plot.querySelector(".series.m-gpt-6-2-astra path").getAttribute("d");
  assert(!series.includes("L"), "A high-only series must not still draw through hidden low/max points");
  const panel = name => [...document.querySelectorAll(".panel")].find(node => node.querySelector("h3").textContent === name);
  const bars = name => [...panel(name).querySelectorAll(".plot .bar")].filter(visible);
  assert(bars("Vals Index").length === 2, "High-only must keep only Fable and Carbon's high-effort Vals bars");
  assert(bars("GPQA Diamond (OpenAI)").length === 0, "Unknown effort must not masquerade as high");
  document.querySelector('label[for="level-not-stated"]').click();
  await settle();
  assert(bars("GPQA Diamond (OpenAI)").length === 3, "Not stated must independently show the three unknown-effort results");
  document.querySelector('label[for="level-not-stated"]').click();

  document.querySelector('label[for="x-cost"]').click();
  await settle();
  const costPlot = document.querySelector('.plot[data-metric="aa-intelligence-index"]');
  const costMarkers = [...costPlot.querySelectorAll(".marker")].filter(visible);
  const links = () => [...costPlot.querySelectorAll(".dominance-link")];
  assert(costMarkers.length === 10 && links().length === 7,
    `High-only cost view must show ten points and one link for each of seven beaten points, got ${costMarkers.length} / ${links().length}`);
  const unbeaten = new Set(["gpt-6-2-sol", "gpt-6-2-astra", "fable-5-2"]);
  assert(new Set(links().map(link => link.dataset.loserModel)).size === 7 && links().every(link =>
    unbeaten.has(link.dataset.winnerModel) && !unbeaten.has(link.dataset.loserModel)
    && link.dataset.winnerLevel === "high" && link.dataset.loserLevel === "high"),
    "Only Sol 6.2, Astra 6.2 and Fable high are unbeaten. Each arrow must end at one of them");
  document.querySelector('label[for="show-gpt-6-2-sol"]').click();
  await settle();
  const remaining = [...costPlot.querySelectorAll(".marker")].filter(visible);
  assert(remaining.length === 9 && links().length === 5,
    "Hiding Sol 6.2 must leave only five beaten points");
  assert(links().every(link => link.dataset.winnerModel !== "gpt-6-2-sol" && link.dataset.loserModel !== "gemini-4-hydrogen"),
    "A hidden model must not beat Hydrogen high");
  document.querySelector('label[for="show-gpt-6-2-sol"]').click();
  await settle();
  const bounds = costPlot.getBoundingClientRect();
  const clipped = [...costPlot.querySelectorAll(".filtered-labels text")].filter(visible)
    .filter(node => node.getBoundingClientRect().left < bounds.left || node.getBoundingClientRect().right > bounds.right);
  assert(!clipped.length, `Filtered cost labels escape the chart: ${clipped.map(node => node.textContent).join(", ")}`);

  document.querySelector('label[for="x-effort"]').click();
  document.querySelector("#levels-none").click();
  await settle();
  assert([...document.querySelectorAll(".panel > .plot")].every(node => node.classList.contains("empty")),
    "With no levels selected, every chart must explain its empty selection");
  document.querySelector('label[for="level-max"]').click();
  await settle();
  const maxPlot = document.querySelector('.plot[data-metric="aa-intelligence-index"]');
  assert([...maxPlot.querySelectorAll(".marker")].filter(visible).length === 7,
    "Max-only must not invent max scores for the Gemini models");
  const sparse = document.querySelector('.plot[data-metric="deepswe-v1-1"]');
  assert([...sparse.querySelectorAll(".marker")].filter(visible).length === 4,
    "Max-only must keep Sonnet and MAI's single DeepSWE points and the two GPT max points");

  document.querySelector("#levels-none").click();
  document.querySelector('label[for="level-high"]').click();
  await settle();
  const zoomSource = document.querySelector('.plot[data-metric="aa-intelligence-index"]');
  const sourceBox = zoomSource.getBoundingClientRect();
  const [left, top, width, height] = zoomSource.dataset.axes.split(",").map(Number);
  const start = { clientX: sourceBox.left + sourceBox.width * left / 100 + 1,
    clientY: sourceBox.top + sourceBox.height * top / 100 + 1 };
  const end = { clientX: start.clientX + sourceBox.width * width / 100 - 2,
    clientY: start.clientY + sourceBox.height * height / 100 - 2 };
  for (const [type, coordinates] of [["pointerdown", start], ["pointermove", end], ["pointerup", end]]) {
    zoomSource.dispatchEvent(new PointerEvent(type, { ...coordinates, bubbles: true, pointerType: "mouse", isPrimary: true, button: 0 }));
  }
  const zoom = document.querySelector("#zoom");
  assert(zoom.open && zoom.querySelectorAll("circle").length === 10, "Dragging over the chart must zoom only the ten selected high points");
  assert(zoom.querySelector(".zoom-range").textContent.startsWith("high to high"), "Zoom must not restore deselected thinking levels");
  zoom.querySelector("button").click();
  assert(!zoom.open, "The zoom must still close normally");
  document.querySelector("#levels-all").click();
  await settle();
  const reset = document.querySelector('.plot[data-metric="aa-intelligence-index"]');
  assert([...reset.querySelectorAll(".marker")].filter(visible).length === 46, "All must restore every published AA Index point");
  const defaults = new URL(location.href).searchParams;
  assert(!defaults.has("models") && !defaults.has("levels") && !defaults.has("axis"), "The all-model, all-level effort view must keep a clean URL");
  return "Thinking-level filter checks passed: effort, Cost dominance, model combinations, sparse/unknown results, empty state, reset and zoom";
})();
