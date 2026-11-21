// Run in the generated page with agent-browser eval --stdin.
(async () => {
  const assert = (condition, message) => { if (!condition) throw new Error(message); };
  const settle = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(resolve))));
  const zoom = document.getElementById("zoom");
  const setModels = names => document.querySelectorAll('input[id^="show-"]').forEach(input => {
    if (input.checked !== names.includes(input.value)) input.click();
  });
  const drag = (plot, start, end) => {
    for (const [type, coordinates] of [["pointerdown", start], ["pointermove", end], ["pointerup", end]]) {
      plot.dispatchEvent(new PointerEvent(type, { ...coordinates, bubbles: true, pointerType: "mouse", isPrimary: true, button: 0 }));
    }
    assert(zoom.open, "Dragging over visible points must open the zoom");
  };
  const wideDrag = plot => {
    const box = plot.getBoundingClientRect();
    drag(plot, { clientX: box.left + 2, clientY: box.top + 2 }, { clientX: box.right - 2, clientY: box.bottom - 2 });
    const [, , width, height] = plot.dataset.axes.split(",").map(Number);
    return box.width * width / (box.height * height);
  };
  const checkRatio = expected => {
    const bounds = zoom.querySelector("clipPath rect");
    assert(bounds, "Zoom must expose its plotting bounds");
    const actual = Number(bounds.getAttribute("width")) / Number(bounds.getAttribute("height"));
    assert(Math.abs(actual / expected - 1) < 0.01,
      `Zoom must preserve the selection aspect ratio ${expected.toFixed(3)}, got ${actual.toFixed(3)}`);
    const chart = zoom.querySelector(".zoom-chart").getBoundingClientRect();
    assert(chart.left >= 0 && chart.right <= innerWidth + 0.5 && chart.top >= 0 && chart.bottom <= innerHeight + 0.5,
      `Proportioned zoom must fit the viewport: ${JSON.stringify(chart)}`);
  };
  const checkLabels = (mode, expected) => {
    assert(!zoom.querySelector(".zoom-legend"), "Zoom must identify models beside their points, not reserve space for a legend");
    const group = zoom.querySelector(".filtered-labels");
    const labels = [...group.querySelectorAll(mode === "cost" ? ":scope > text" : ".end text")];
    assert(labels.length === expected.length, `${mode} zoom needs ${expected.length} score labels, got ${labels.length}`);
    const names = [...group.querySelectorAll(".name text")];
    for (const [score, name] of expected) {
      const model = names.find(label => label.textContent === name);
      const label = labels.find(label => label.textContent === (mode === "cost" ? `${score}${name}` : score)
        && (mode === "cost" || label.getAttribute("y") === model?.getAttribute("y")));
      assert(label, `${mode} zoom must label ${score} ${name} without effort`);
      if (mode === "cost") continue;
      assert(model && model.getAttribute("y") === label.getAttribute("y"), `${name}'s score and name must share one line`);
    }
    assert(mode === "cost" || new Set(names.map(label => label.getAttribute("x"))).size === 1,
      "Thinking-level zoom must align model names in one end-label column");
    const chart = zoom.querySelector(".zoom-chart").getBoundingClientRect();
    const boxes = [...labels, ...names].map(label => label.getBoundingClientRect());
    assert(boxes.every(box => box.left >= chart.left - 0.5 && box.right <= chart.right + 0.5
      && box.top >= chart.top - 0.5 && box.bottom <= chart.bottom + 0.5), `${mode} zoom labels must stay inside the chart`);
    assert(!boxes.some((first, index) => boxes.slice(index + 1).some(second =>
      Math.min(first.right, second.right) - Math.max(first.left, second.left) > 0.5
      && Math.min(first.bottom, second.bottom) - Math.max(first.top, second.top) > 0.5)), `${mode} zoom labels must not overlap`);
  };
  const ends = [["71.3", "Gemini 4 Neon"], ["63.8", "GPT-6 Astra"], ["72.2", "GPT-6.2 Astra"],
    ["58.8", "GPT-6.1 Sol"], ["64.0", "GPT-6.2 Sol"], ["80.2", "Fable 5.2"], ["67.9", "Opus 5.5"],
    ["53.3", "Sonnet 5.5"], ["69.1", "Gemini 4 Carbon"], ["58.8", "Gemini 4 Hydrogen"]];
  for (const mode of ["cost", "effort"]) {
    document.querySelector("#models-all").click();
    document.querySelector("#levels-all").click();
    document.querySelector(`label[for="x-${mode}"]`).click();
    await settle();
    const plot = document.querySelector('.panel[data-chart="hle-diamond"] > .plot');
    const ratio = wideDrag(plot);
    checkRatio(ratio);
    checkLabels(mode, ends);
    const bounds = zoom.querySelector("clipPath rect");
    const ticks = [...zoom.querySelectorAll("text")].filter(label => Number(label.getAttribute("x")) < Number(bounds.getAttribute("x"))
      && /^\d+(\.\d+)?$/.test(label.textContent)).map(label => Number(label.textContent));
    assert(Math.min(...ticks) === 10 && Math.max(...ticks) === 90, `${mode} HLE zoom must fit scores to 10–90, got ${ticks}`);
    zoom.querySelector("button").click();
    setModels(["gpt-6-2-sol"]);
    await settle();
    const marker = plot.querySelector('.marker.m-gpt-6-2-sol[data-level="low"] use').getBoundingClientRect();
    const center = { x: (marker.left + marker.right) / 2, y: (marker.top + marker.bottom) / 2 };
    drag(plot, { clientX: center.x - 6, clientY: center.y - 6 }, { clientX: center.x + 6, clientY: center.y + 6 });
    assert(zoom.querySelectorAll("circle").length === 1, `${mode} narrow selection must keep only Sol low`);
    checkRatio(1);
    checkLabels(mode, [["34.5", "GPT-6.2 Sol"]]);
    const narrowBounds = zoom.querySelector("clipPath rect");
    const scoreTicks = [...zoom.querySelectorAll("text")].filter(label => Number(label.getAttribute("x")) < Number(narrowBounds.getAttribute("x"))
      && /^\d+(\.\d+)?$/.test(label.textContent)).map(label => Number(label.textContent));
    assert(Math.max(...scoreTicks) - Math.min(...scoreTicks) <= 2, `${mode} single-point zoom must tighten its score axis, got ${scoreTicks}`);
    zoom.querySelector("button").click();
  }
  document.querySelector("#models-all").click();
  await settle();
  return "Zoom shares page labels and fitted axes in both views, keeps wide/narrow selection proportions, and contains non-overlapping labels";
})();
