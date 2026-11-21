// Run in the generated page with agent-browser eval --stdin.
(async () => {
  const failures = [];
  const assert = (condition, message) => { if (!condition) failures.push(message); };
  const settle = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(resolve))));
  const zoom = document.getElementById("zoom");
  const drag = (plot, start, end) => {
    for (const [type, coordinates] of [["pointerdown", start], ["pointermove", end], ["pointerup", end]]) {
      plot.dispatchEvent(new PointerEvent(type, { ...coordinates, bubbles: true, pointerType: "mouse", isPrimary: true, button: 0 }));
    }
    if (!zoom.open) throw new Error("A tested selection containing points must open the zoom");
  };
  const shape = () => {
    const bounds = zoom.querySelector("clipPath rect");
    return { width: Number(bounds.getAttribute("width")), height: Number(bounds.getAttribute("height")) };
  };
  const checkLabels = mode => {
    const chart = zoom.querySelector(".zoom-chart").getBoundingClientRect();
    const labels = [...zoom.querySelectorAll(".filtered-labels text")].map(label => label.getBoundingClientRect());
    assert(labels.every(box => box.left >= chart.left - 0.5 && box.right <= chart.right + 0.5
      && box.top >= chart.top - 0.5 && box.bottom <= chart.bottom + 0.5), `${mode}: skinny selection labels must stay inside the chart`);
    assert(!labels.some((first, index) => labels.slice(index + 1).some(second =>
      Math.min(first.right, second.right) - Math.max(first.left, second.left) > 0.5
      && Math.min(first.bottom, second.bottom) - Math.max(first.top, second.top) > 0.5)), `${mode}: skinny selection labels must not overlap`);
    const ticks = [...zoom.querySelectorAll("text")].filter(label => Number(label.getAttribute("x")) < Number(zoom.querySelector("clipPath rect").getAttribute("x")))
      .map(label => label.getBoundingClientRect()).sort((first, second) => first.top - second.top);
    assert(ticks.every((tick, index) => !index || tick.top >= ticks[index - 1].bottom - 0.5), `${mode}: skinny selection score ticks must not overlap`);
  };
  document.querySelector("#models-all").click();
  document.querySelector("#levels-all").click();
  for (const mode of ["cost", "effort"]) {
    document.querySelector(`label[for="x-${mode}"]`).click();
    await settle();
    const plot = document.querySelector('.panel[data-chart="hle-diamond"] > .plot');
    const box = plot.getBoundingClientRect();
    const [left, top, width, height] = plot.dataset.axes.split(",").map(Number);
    const axes = { x: box.left + box.width * left / 100, y: box.top + box.height * top / 100,
      width: box.width * width / 100, height: box.height * height / 100 };
    const sourceRatio = axes.width / axes.height;
    drag(plot, { clientX: box.left + 2, clientY: box.top + 2 }, { clientX: box.right - 2, clientY: box.bottom - 2 });
    const whole = shape();
    assert(whole.width >= axes.width - 0.5 && whole.height >= axes.height - 0.5,
      `${mode}: whole-chart zoom must not shrink its ${axes.width.toFixed(1)}×${axes.height.toFixed(1)}px source to ${whole.width.toFixed(1)}×${whole.height.toFixed(1)}px`);
    const levels = [...zoom.querySelectorAll("text")].filter(label => /^(low|medium|high|xhigh|max)$/.test(label.textContent));
    const ticks = levels.map(label => label.getBoundingClientRect());
    assert(!ticks.some((first, index) => ticks.slice(index + 1).some(second =>
      Math.min(first.right, second.right) - Math.max(first.left, second.left) > 0.5
      && Math.min(first.bottom, second.bottom) - Math.max(first.top, second.top) > 0.5)), "Thinking-level phone ticks must stay separated like the page's staggered ticks");
    const circle = zoom.querySelector('circle[data-model="sonnet-5-5"][data-level="medium"]');
    for (const type of ["pointerdown", "pointerup"]) circle.dispatchEvent(new PointerEvent(type, {
      bubbles: true, pointerType: "touch", clientX: circle.getBoundingClientRect().x, clientY: circle.getBoundingClientRect().y,
    }));
    const tip = zoom.querySelector('.cost-point.m-sonnet-5-5[data-level="medium"] .tip');
    const details = mode === "cost" ? ["23.8", "medium", "$0.0327"] : ["23.8", "medium"];
    assert(tip && tip.getBoundingClientRect().width && details.every(value => tip.textContent.includes(value)),
      `${mode}: tapping intermediate Sonnet medium must visibly show ${details.join(" / ")}`);
    zoom.querySelector("button").click();
    const middleScore = axes.y + axes.height * (90 - 51) / 80;
    drag(plot, { clientX: axes.x, clientY: middleScore - 5 }, { clientX: axes.x + axes.width, clientY: middleScore + 5 });
    const flat = shape();
    assert(Math.abs(flat.width / flat.height / (2 * sourceRatio) - 1) < 0.01,
      `${mode}: a flat selection must clamp to twice the source ratio, got ${flat.width / flat.height}`);
    checkLabels(`${mode} flat`);
    zoom.querySelector("button").click();
    const marker = plot.querySelector(mode === "cost" ? '.marker.m-opus-5-5[data-level="low"] use' : '.marker.m-opus-5-5[data-level="high"] use').getBoundingClientRect();
    const center = (marker.left + marker.right) / 2;
    drag(plot, { clientX: center - 5, clientY: axes.y }, { clientX: center + 5, clientY: axes.y + axes.height });
    const tall = shape();
    assert(Math.abs(tall.width / tall.height / (sourceRatio / 2) - 1) < 0.01,
      `${mode}: a tall selection must clamp to half the source ratio, got ${tall.width / tall.height}`);
    checkLabels(`${mode} tall`);
    zoom.querySelector("button").click();
  }
  if (failures.length) throw new Error(failures.join("\n"));
  return "Zoom enlarges whole charts, staggers phone ticks, bounds skinny selection ratios and retains touch point details";
})();
