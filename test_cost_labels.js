// Run in the generated page with agent-browser eval --stdin.
(async () => {
  const assert = (condition, message) => { if (!condition) throw new Error(message); };
  const settle = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(resolve))));
  document.querySelector("#models-all").click();
  document.querySelector("#levels-all").click();
  document.querySelector('label[for="x-cost"]').click();
  await settle();
  const check = () => {
    const issues = [];
    for (const plot of document.querySelectorAll('.panel:not([hidden]) > .plot[data-mode="cost"]')) {
      const labels = [...plot.querySelectorAll(".end text, .filtered-labels > text")].filter(label => label.getBoundingClientRect().width);
      const markers = [...plot.querySelectorAll(".marker use")].filter(marker => marker.getBoundingClientRect().width);
      const series = [...plot.querySelectorAll(".series path")].filter(path => path.getBoundingClientRect().width);
      for (const label of labels) {
        const box = label.getBoundingClientRect();
        const inside = point => point.x > box.left - 2 && point.x < box.right + 2 && point.y > box.top - 2 && point.y < box.bottom + 2;
        if (markers.some(marker => { const markerBox = marker.getBoundingClientRect();
          return inside({x: markerBox.left + markerBox.width / 2, y: markerBox.top + markerBox.height / 2}); })) {
          issues.push(`${plot.dataset.metric}: ${label.textContent} covers a point`);
        }
        if (series.some(path => {
          const matrix = path.getScreenCTM();
          for (let distance = 0; distance <= path.getTotalLength(); distance += 1) {
            if (inside(path.getPointAtLength(distance).matrixTransform(matrix))) return true;
          }
          return false;
        })) issues.push(`${plot.dataset.metric}: ${label.textContent} covers a series`);
      }
      const models = new Set(markers.map(marker => [...marker.closest(".marker").classList].find(name => name.startsWith("m-"))));
      for (const model of models) {
        const leader = [...plot.querySelectorAll(`.leader.${model} path, path.leader.${model}`)].find(path => path.getBoundingClientRect().width);
        if (!leader) issues.push(`${plot.dataset.metric}: ${model} needs a visible leader`);
      }
    }
    assert(!issues.length, `Cost labels must clear the data and connect to their points: ${issues.slice(0, 12).join(", ")}`);
  };
  check();
  for (const input of document.querySelectorAll('input[id^="show-"]')) {
    if (input.checked !== ["opus-5-5", "gpt-6-2-astra", "gpt-6-2-sol", "gpt-6-astra", "gpt-6-1-sol"].includes(input.value)) input.click();
  }
  await settle();
  check();
  document.querySelector("#models-all").click();
  await settle();
  return "Cost labels clear every visible point/series and have leader lines, default and filtered";
})();
