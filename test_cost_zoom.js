// Run in the generated page: agent-browser --session ai-scores-test eval --stdin < test_cost_zoom.js
(async () => {
  if (document.readyState !== "complete") await new Promise(resolve => window.addEventListener("load", resolve, { once: true }));
  const assert = (condition, message) => { if (!condition) throw new Error(message); };
  const settle = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(resolve))));
  document.querySelectorAll('input[id^="show-"]').forEach(input => {
    const wanted = ["gpt-6-2-sol", "gpt-6-2-astra"].includes(input.value);
    if (input.checked !== wanted) input.click();
  });
  document.getElementById("levels-none").click();
  document.querySelector('label[for="level-high"]').click();
  document.querySelector('label[for="level-max"]').click();
  document.querySelector('label[for="x-cost"]').click();
  await settle();
  const plot = document.querySelector('.plot[data-metric="aa-intelligence-index"]');
  const box = plot.getBoundingClientRect();
  const drag = (start, end) => {
    for (const [type, coordinates] of [["pointerdown", start], ["pointermove", end], ["pointerup", end]]) {
      plot.dispatchEvent(new PointerEvent(type, { ...coordinates, bubbles: true, pointerType: "mouse", isPrimary: true, button: 0 }));
    }
  };
  drag({ clientX: box.left + 3, clientY: box.top + 3 }, { clientX: box.right - 3, clientY: box.bottom - 3 });
  const zoom = document.getElementById("zoom");
  assert(zoom.open, "Dragging in Cost mode must open the zoom, just as effort mode does");
  const closeArea = zoom.querySelector("button").getBoundingClientRect();
  assert(closeArea.width >= 44 && closeArea.height >= 44,
    `The zoom Close button needs a 44×44 touch area, got ${closeArea.width}×${closeArea.height}`);
  assert(zoom.querySelectorAll("circle").length === 4, "Cost zoom must keep only the two selected models at high and max");
  const circle = (model, level) => [...zoom.querySelectorAll("circle")].find(node => node.querySelector("title")?.textContent.startsWith(`${model} ${level}:`));
  const solHigh = circle("GPT-6.2 Sol", "high");
  const solMax = circle("GPT-6.2 Sol", "max");
  const astraHigh = circle("GPT-6.2 Astra", "high");
  assert(solHigh && solMax && astraHigh, "Cost zoom must identify each model and thinking level");
  const firstGap = Number(solMax.getAttribute("cx")) - Number(solHigh.getAttribute("cx"));
  const secondGap = Number(astraHigh.getAttribute("cx")) - Number(solMax.getAttribute("cx"));
  const expectedRatio = Math.log(1110 / 553) / Math.log(2010 / 1110);
  assert(firstGap > 0 && secondGap > 0 && Math.abs(firstGap / secondGap - expectedRatio) < 0.00001,
    "Cost zoom must use actual logarithmic prices, not effort positions or a linear cost scale");
  assert(zoom.querySelector(".zoom-range").textContent.includes("US$ to run the whole index"), "Cost zoom must state the cost denominator");
  zoom.querySelector("button").click();

  const viewWidth = plot.querySelector("svg").viewBox.baseVal.width;
  const pointX = level => Number(plot.querySelector(`.marker.m-gpt-6-2-sol[data-level="${level}"] use`).getAttribute("x"));
  const cutoff = box.left + (pointX("high") + pointX("max")) / 2 / viewWidth * box.width;
  drag({ clientX: box.left + 3, clientY: box.top + 3 }, { clientX: cutoff, clientY: box.bottom - 3 });
  assert(zoom.open && zoom.querySelectorAll("circle").length === 1 && circle("GPT-6.2 Sol", "high"),
    "A narrow log-cost selection must keep only Sol high at $553 and support a single-price zoom");
  zoom.querySelector("button").click();
  const start = { clientX: box.left + 3, clientY: box.top + 3 };
  const end = { clientX: box.right - 3, clientY: box.bottom - 3 };
  plot.dispatchEvent(new PointerEvent("pointerdown", { ...start, bubbles: true, pointerType: "touch", isPrimary: true }));
  await new Promise(resolve => setTimeout(resolve, 1100));
  for (const type of ["pointermove", "pointerup"]) {
    plot.dispatchEvent(new PointerEvent(type, { ...end, bubbles: true, pointerType: "touch", isPrimary: true }));
  }
  assert(zoom.open && zoom.querySelectorAll("circle").length === 4, "Press-and-hold touch zoom must work in Cost mode too");
  zoom.querySelector("button").click();
  return "Cost zoom checks passed: mouse/touch, filtered models/levels, logarithmic prices, cost units and single-point selection";
})();
