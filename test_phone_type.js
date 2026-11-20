// Run in the generated page with agent-browser eval --stdin.
(async () => {
  if (innerWidth >= 700) return "Phone typography applies below 700px";
  const assert = (condition, message) => { if (!condition) throw new Error(message); };
  const settle = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(resolve))));
  document.querySelector("#models-all").click();
  document.querySelector("#levels-all").click();
  for (const mode of ["effort", "cost"]) {
    document.querySelector(`label[for="x-${mode}"]`).click();
    await settle();
    const tiny = [];
    for (const plot of document.querySelectorAll(".panel:not([hidden]) > .plot")) {
      const svg = plot.querySelector("svg.chart");
      const scale = svg.getBoundingClientRect().width / svg.viewBox.baseVal.width;
      const ticks = [...svg.querySelectorAll(".effort-axis text, .fitted-effort-axis text, .cost-axis text, .fitted-cost-axis text")].filter(label => ["low", "medium", "high", "xhigh", "max"].includes(label.textContent) || label.textContent.startsWith("$"))
        .filter(label => label.getBoundingClientRect().width).map(label => label.getBoundingClientRect());
      assert(!ticks.some((first, index) => ticks.slice(index + 1).some(second =>
        Math.min(first.right, second.right) > Math.max(first.left, second.left)
        && Math.min(first.bottom, second.bottom) > Math.max(first.top, second.top))),
        `${plot.closest(".panel").querySelector("h3").textContent}: axis ticks must not overlap`);
      for (const label of svg.querySelectorAll("text, tspan")) {
        if (!label.getBoundingClientRect().width || !label.textContent.trim()) continue;
        const size = parseFloat(getComputedStyle(label).fontSize) * scale;
        if (size < 11) tiny.push(`${plot.closest(".panel").querySelector("h3").textContent}: ${label.textContent} ${size.toFixed(1)}px`);
      }
    }
    assert(!tiny.length, `${mode}: chart text must render at least 11px: ${tiny.slice(0, 8).join(", ")}`);
  }
  document.querySelector('label[for="x-effort"]').click();
  await settle();
  return "Phone chart text is at least 11 CSS pixels in both views";
})();
