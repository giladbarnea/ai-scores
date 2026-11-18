// Run in the generated page: agent-browser --session ai-scores-test eval --stdin < test_filters.js
(() => {
  const assert = (condition, message) => { if (!condition) throw new Error(message); };
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
  const plot = document.querySelector('.plot[data-metric="aa-intelligence-index"]');
  const markers = [...plot.querySelectorAll(".marker")].filter(visible);
  assert(markers.length === 9, `High-only must show nine AA Index points, got ${markers.length}`);
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
  assert(bars("GPQA Diamond (OpenAI)").length === 3, "Not stated must independently show the three unknown-effort results");
  document.querySelector('label[for="level-not-stated"]').click();

  document.querySelector('label[for="x-cost"]').click();
  const costPlot = document.querySelector('.plot[data-metric="aa-intelligence-index"]');
  const costMarkers = [...costPlot.querySelectorAll(".marker")].filter(visible);
  const faded = costMarkers.filter(node => Number(getComputedStyle(node).opacity) < .5);
  assert(costMarkers.length === 9 && faded.length === 6,
    `High-only cost view must show nine points, six dominated, got ${costMarkers.length} / ${faded.length}`);
  const frontier = costPlot.querySelector(".filtered-frontier").getAttribute("points").trim().split(/\s+/);
  assert(frontier.length === 3, `Only Sol 6.2, Astra 6.2 and Fable high belong on this frontier, got ${frontier.length} points`);
  const position = slug => {
    const marker = costPlot.querySelector(`.marker.m-${slug}[data-level="high"] use`);
    return `${Number(marker.getAttribute("x"))},${Number(marker.getAttribute("y"))}`;
  };
  assert(JSON.stringify(frontier) === JSON.stringify(["gpt-6-2-sol", "gpt-6-2-astra", "fable-5-2"].map(position)),
    "The cost frontier must join the three independently checked high-effort deals");
  document.querySelector('label[for="show-gpt-6-2-sol"]').click();
  const remaining = [...costPlot.querySelectorAll(".marker")].filter(visible);
  assert(remaining.length === 8 && remaining.filter(node => Number(getComputedStyle(node).opacity) < .5).length === 4,
    "Hiding Sol 6.2 must restore Hydrogen high to the frontier and leave four dominated points");
  const hydrogen = costPlot.querySelector('.marker.m-gemini-4-hydrogen[data-level="high"]');
  assert(Number(getComputedStyle(hydrogen).opacity) === 1, "A hidden model must not still dominate Hydrogen high");
  document.querySelector('label[for="show-gpt-6-2-sol"]').click();
  const bounds = costPlot.getBoundingClientRect();
  const clipped = [...costPlot.querySelectorAll(".filtered-labels text")].filter(visible)
    .filter(node => node.getBoundingClientRect().left < bounds.left || node.getBoundingClientRect().right > bounds.right);
  assert(!clipped.length, `Filtered cost labels escape the chart: ${clipped.map(node => node.textContent).join(", ")}`);

  document.querySelector('label[for="x-effort"]').click();
  document.querySelector("#levels-none").click();
  assert([...document.querySelectorAll(".panel > .plot")].every(node => node.classList.contains("empty")),
    "With no levels selected, every chart must explain its empty selection");
  document.querySelector('label[for="level-max"]').click();
  const maxPlot = document.querySelector('.plot[data-metric="aa-intelligence-index"]');
  assert([...maxPlot.querySelectorAll(".marker")].filter(visible).length === 7,
    "Max-only must not invent max scores for the Gemini models");
  const sparse = document.querySelector('.plot[data-metric="deepswe-v1-1"]');
  assert([...sparse.querySelectorAll(".marker")].filter(visible).length === 3,
    "Max-only must keep Sonnet's single DeepSWE point and the two GPT max points");

  document.querySelector("#levels-none").click();
  document.querySelector('label[for="level-high"]').click();
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
  assert(zoom.open && zoom.querySelectorAll("circle").length === 9, "Dragging over the chart must zoom only the nine selected high points");
  assert(zoom.querySelector(".zoom-range").textContent.startsWith("high to high"), "Zoom must not restore deselected thinking levels");
  zoom.querySelector("button").click();
  assert(!zoom.open, "The zoom must still close normally");
  document.querySelector("#levels-all").click();
  const reset = document.querySelector('.plot[data-metric="aa-intelligence-index"]');
  assert([...reset.querySelectorAll(".marker")].filter(visible).length === 42, "All must restore every published AA Index point");
  return "Thinking-level filter checks passed: effort, cost frontier, model combinations, sparse/unknown results, empty state, reset and zoom";
})();
