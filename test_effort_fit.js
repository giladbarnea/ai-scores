// Run in the generated page with agent-browser eval --stdin.
(async () => {
  const assert = (condition, message) => { if (!condition) throw new Error(message); };
  const settle = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(resolve))));
  const click = id => document.querySelector(`label[for="${id}"]`).click();
  document.querySelector("#models-all").click();
  document.querySelector("#levels-none").click();
  click("level-max");
  click("x-effort");
  await settle();
  const plot = document.querySelector('.panel > .plot[data-metric="aa-intelligence-index"]');
  const [low, high] = plot.dataset.xLimits.split(",").map(Number);
  assert(low > 3 && high < 5, `Max-only must use one column, not retain low–xhigh: ${low}–${high}`);
  const ticks = [...plot.querySelectorAll(".effort-axis text, .fitted-effort-axis text")]
    .filter(node => node.getBoundingClientRect().width).map(node => node.textContent);
  assert(ticks.join(",") === "max", `Max-only must label only max, got ${ticks}`);
  const marker = plot.querySelector('.marker.m-opus-5-5[data-level="max"] use');
  const column = plot.querySelector('.column[data-level="max"]');
  const center = node => { const box = node.getBoundingClientRect(); return {x: box.left + box.width / 2, y: box.top + box.height / 2}; };
  assert(Math.abs(center(column).x - center(marker).x) < 0.5, "Effort hover column must track the fitted point");
  const point = center(marker);
  for (const [type, offset] of [["pointerdown", -6], ["pointermove", 6], ["pointerup", 6]]) {
    plot.dispatchEvent(new PointerEvent(type, {clientX: point.x + offset, clientY: point.y + offset,
      bubbles: true, pointerType: "mouse", isPrimary: true, button: 0}));
  }
  const zoom = document.querySelector("#zoom");
  assert(zoom.open && zoom.querySelector(".zoom-range").textContent.startsWith("max to max"),
    "Zoom must resolve the moved max column to max, not a former lower-effort coordinate");
  zoom.querySelector("button").click();
  document.querySelector("#levels-all").click();
  await settle();
  assert(plot.dataset.xLimits === "-0.85,4.9", "All levels must restore the full effort scale exactly");
  return "Effort x fit passed: one visible column, ticks, hover, zoom and exact reset";
})();
