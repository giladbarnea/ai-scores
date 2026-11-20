// Run in the generated page: agent-browser --session ai-scores-test eval --stdin < test_chart_fit.js
(async () => {
  const assert = (condition, message) => { if (!condition) throw new Error(message); };
  const settle = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(resolve))));
  const plot = name => document.querySelector(`.panel > .plot[data-metric="${name}"]`);
  const click = id => document.querySelector(`label[for="${id}"]`).click();
  const setModels = names => document.querySelectorAll('input[id^="show-"]').forEach(input => {
    if (input.checked !== names.includes(input.value)) click(input.id);
  });
  const scoreTicks = chart => [...chart.querySelectorAll('svg.chart text')]
    .filter(node => node.getBoundingClientRect().width && /^−?\d+(\.\d+)?$/.test(node.textContent)
      && Number(node.getAttribute("x")) < chart.querySelector("clipPath rect").x.baseVal.value)
    .map(node => Number(node.textContent.replace("−", "-"))).sort((first, second) => first - second);
  const range = chart => {
    const ticks = scoreTicks(chart);
    return `${ticks[0]} to ${ticks.at(-1)}`;
  };
  const boxCenter = node => {
    const box = node.getBoundingClientRect();
    return { x: (box.left + box.right) / 2, y: (box.top + box.bottom) / 2 };
  };
  const solLow = chart => chart.querySelector('.marker.m-gpt-6-2-sol[data-level="low"] use');
  const dragAroundSolLow = chart => {
    const { x, y } = boxCenter(solLow(chart));
    for (const [type, offset] of [["pointerdown", -6], ["pointermove", 6], ["pointerup", 6]]) {
      chart.dispatchEvent(new PointerEvent(type, {
        clientX: x + offset, clientY: y + offset, bubbles: true, pointerType: "mouse", isPrimary: true, button: 0,
      }));
    }
    const zoom = document.querySelector("#zoom");
    assert(zoom.open && zoom.querySelectorAll("circle").length === 1 && zoom.querySelector(".zoom-range").textContent.includes("34.5"),
      "A tight drag around the moved Sol low point must open that 34.5 score, not a point from the old scale");
    zoom.querySelector("button").click();
  };
  const models = ["gpt-6-2-astra", "gpt-6-2-sol", "opus-5-5"];
  document.querySelector("#models-all").click();
  document.querySelector("#levels-all").click();
  click("x-effort");
  await settle();
  const hle = plot("hle-diamond");
  const crit = plot("critpt-v2");
  assert(range(hle) === "10 to 90" && range(crit) === "20 to 80", "The unfiltered score axes must fit the published scores");
  setModels(models);
  await settle();
  assert(range(hle) === "30 to 80" && range(crit) === "30 to 80",
    `The three-model view must fit both charts to 30–80. HLE: ${range(hle)}. CritPt: ${range(crit)}`);
  const lowRing = hle.querySelector('.column[data-level="low"] .ring.m-gpt-6-2-sol');
  assert(Math.abs(boxCenter(lowRing).y - boxCenter(solLow(hle)).y) < 0.5,
    "The thinking-level hover ring must move with its point");
  dragAroundSolLow(hle);
  click("show-fable-5-2");
  await settle();
  assert(range(hle) === "30 to 90", `Fable's 80.2 must expand HLE to 90, got ${range(hle)}`);
  click("show-fable-5-2");
  await settle();
  assert(range(hle) === "30 to 80", `Taking Fable out must shrink HLE again, got ${range(hle)}`);
  click("x-cost");
  await settle();
  const cost = plot("hle-diamond");
  assert(range(cost) === "30 to 80", `Cost must also fit only the visible scores, got ${range(cost)}`);
  const costTarget = cost.querySelector('.cost-point.m-gpt-6-2-sol[data-level="low"]');
  assert(Math.abs(boxCenter(costTarget).y - boxCenter(solLow(cost)).y) < 0.5,
    "The Cost hover target must move with its point");
  dragAroundSolLow(cost);
  document.querySelector("#levels-none").click();
  click("level-high");
  await settle();
  assert(range(cost) === "50 to 70", `High-only HLE must tighten again in Cost, got ${range(cost)}`);
  click("x-effort");
  await settle();
  assert(range(hle) === "50 to 70", `High-only HLE must use the same score range in Thinking level, got ${range(hle)}`);
  document.querySelector("#levels-all").click();
  document.querySelector("#models-all").click();
  await settle();
  assert(range(hle) === "10 to 90" && range(crit) === "20 to 80", "Clearing the filters must restore the original score axes");
  return "Chart fit checks passed: shrink, expand, reset, both views, hover alignment and tight drag-to-zoom";
})();
