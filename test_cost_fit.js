// Run in the generated page: agent-browser --session ai-scores-test eval --stdin < test_cost_fit.js
(async () => {
  if (document.readyState !== "complete") await new Promise(resolve => window.addEventListener("load", resolve, { once: true }));
  const assert = (condition, message) => { if (!condition) throw new Error(message); };
  const settle = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(resolve))));
  const click = id => document.querySelector(`label[for="${id}"]`).click();
  const setModels = names => document.querySelectorAll('input[id^="show-"]').forEach(input => {
    if (input.checked !== names.includes(input.value)) click(input.id);
  });
  const plot = name => document.querySelector(`.panel > .plot[data-metric="${name}"]`);
  const center = node => {
    const bounds = node.getBoundingClientRect();
    return { x: (bounds.left + bounds.right) / 2, y: (bounds.top + bounds.bottom) / 2 };
  };
  document.getElementById("models-all").click();
  document.getElementById("levels-all").click();
  click("x-cost");
  await settle();
  const arc = plot("arc-agi-2");
  const fullScoreTicks = [...plot("vals-index").querySelectorAll(".score-axis text")].map(node => Number(node.textContent));
  assert(Math.min(...fullScoreTicks) <= 63.94 && Math.max(...fullScoreTicks) >= 71.31
    && Math.max(...fullScoreTicks) - Math.min(...fullScoreTicks) <= 20,
    `The default Vals Cost scatter must fit its 63.94–71.31 scores, not retain the bar's 0–100 range: ${fullScoreTicks}`);
  const originalLimits = arc.dataset.xLimits;
  const originalPoint = center(arc.querySelector('.marker.m-opus-5-5[data-level="max"] use'));
  setModels(["opus-5-5", "sonnet-5-5"]);
  await settle();
  const [low, high] = arc.dataset.xLimits.split(",").map(Number);
  assert(low === 0.1 && high === 3,
    `Filtered ARC must end at $3, the first tick after its $1.85 point, not retain the full-data limits: ${low}–${high}`);
  for (const name of ["vals-index", "vals-finance-index-v1"]) {
    const chart = plot(name);
    const [bottom, top] = chart.dataset.yLimits.split(",").map(Number);
    assert(top - bottom <= 2,
      `${name}'s two scores less than one point apart must not keep a ten-point score range, got ${bottom}–${top}`);
  }
  const ratings = [...plot("gdpval-aa").querySelectorAll(".filtered-labels text")];
  assert(ratings[0].textContent.startsWith("1866") && ratings[1].textContent.startsWith("1838")
    && Number(ratings[0].getAttribute("y")) < Number(ratings[1].getAttribute("y")),
    "GDPval's higher 1866 Opus label must stay above Sonnet's 1838 label after the Cost-axis refit");
  const marker = arc.querySelector('.marker.m-opus-5-5[data-level="max"] use');
  const target = arc.querySelector('.cost-point.m-opus-5-5[data-level="max"]');
  assert(Math.hypot(center(marker).x - center(target).x, center(marker).y - center(target).y) < 0.5,
    "Both coordinates of the hover target must track its marker after Cost-axis fitting");
  const point = center(marker);
  for (const [type, offset] of [["pointerdown", -6], ["pointermove", 6], ["pointerup", 6]]) {
    arc.dispatchEvent(new PointerEvent(type, { clientX: point.x + offset, clientY: point.y + offset,
      bubbles: true, pointerType: "mouse", isPrimary: true, button: 0 }));
  }
  const zoom = document.getElementById("zoom");
  assert(zoom.open && zoom.querySelectorAll("circle").length === 1
    && zoom.querySelector(".zoom-range").textContent.includes("91.7"),
    "A tight drag around the moved Opus max must open only its 91.7 point, using the fitted log-cost limits");
  zoom.querySelector("button").click();
  document.getElementById("models-all").click();
  await settle();
  assert(arc.dataset.xLimits === originalLimits, "All models must restore the exact original Cost limits");
  const restored = center(marker);
  assert(Math.hypot(restored.x - originalPoint.x, restored.y - originalPoint.y) < 0.5,
    "All models must restore the marker's exact original position");
  const assertCostLabels = selection => {
    const issues = [];
    for (const chart of document.querySelectorAll('.panel:not([hidden]) > .plot[data-mode="cost"]')) {
      const card = chart.closest(".panel").getBoundingClientRect();
      const fitted = chart.querySelector(".filtered-labels");
      const groups = fitted ? [...fitted.children].filter(node => node.tagName === "text").map(node => [node])
        : [...document.querySelectorAll('input[id^="show-"]:checked')].map(input =>
          [...chart.querySelectorAll(`.end.m-${input.value} text`)]);
      const labels = groups.map(nodes => nodes.map(node => node.getBoundingClientRect()).filter(box => box.width))
        .filter(boxes => boxes.length);
      if (labels.flat().some(label => label.left < card.left - 0.5 || label.right > card.right + 0.5
        || label.top < card.top - 0.5 || label.bottom > card.bottom + 0.5)) issues.push(`${chart.dataset.metric}: clipped label`);
      if (labels.some((first, index) => labels.slice(index + 1).some(second => first.some(from => second.some(to =>
        Math.min(from.right, to.right) - Math.max(from.left, to.left) > 0.5
        && Math.min(from.bottom, to.bottom) - Math.max(from.top, to.top) > 0.5))))) issues.push(`${chart.dataset.metric}: overlapping labels`);
    }
    assert(!issues.length, `${selection}: Cost labels must stay inside cards and clear of one another: ${issues.join(", ")}`);
  };
  assertCostLabels("All models");
  for (const names of [["opus-5-5"], ["opus-5-5", "sonnet-5-5"], ["opus-5-5", "gpt-6-2-sol"]]) {
    setModels(names);
    await settle();
    assertCostLabels(names.join(", "));
  }
  document.getElementById("models-all").click();
  document.getElementById("levels-none").click();
  click("level-high");
  await settle();
  assertCostLabels("All models, high only");
  document.getElementById("levels-all").click();
  await settle();
  assertCostLabels("All restored");
  return "Cost fit checks passed: sparse score padding, log-cost bounds, aligned hover targets, tight zoom, exact reset and unclipped labels across selections";
})();
