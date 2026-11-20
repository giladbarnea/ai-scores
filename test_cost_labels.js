// Run in the generated page with agent-browser eval --stdin.
(async () => {
  const assert = (condition, message) => { if (!condition) throw new Error(message); };
  const settle = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(resolve))));
  const data = JSON.parse(document.getElementById("chart-data").textContent);
  const visible = node => node.getBoundingClientRect().width > 0;
  const setModels = names => document.querySelectorAll('input[id^="show-"]').forEach(input => {
    if (input.checked !== names.includes(input.value)) input.click();
  });
  document.querySelector("#models-all").click();
  document.querySelector("#levels-all").click();
  document.querySelector('label[for="x-cost"]').click();
  await settle();
  const check = () => {
    for (const plot of document.querySelectorAll('.panel:not([hidden]) > .plot[data-mode="cost"]')) {
      const svg = plot.querySelector("svg.chart");
      const chart = svg.getBoundingClientRect();
      const [left, , width] = plot.dataset.axes.split(",").map(Number);
      const bounds = {left: chart.left + chart.width * left / 100, right: chart.left + chart.width * (left + width) / 100};
      assert(Number(plot.dataset.axes.split(",")[2]) > 75,
        `${plot.dataset.metric}: Cost must use the plot width, not reserve a right-hand label column`);
      const labels = [...plot.querySelectorAll(".end text, .filtered-labels > text")].filter(visible);
      assert(labels.length, `${plot.dataset.metric}: Cost must retain score/model labels`);
      for (const label of labels) {
        const box = label.getBoundingClientRect();
        assert(box.left >= bounds.left - 1 && box.right <= bounds.right + 1,
          `${plot.dataset.metric}: ${label.textContent} must sit inside the plot`);
        assert(!/\b(low|medium|high|xhigh|max)\b/.test(label.textContent),
          `${plot.dataset.metric}: Cost end labels must omit effort: ${label.textContent}`);
      }
      const filtered = plot.querySelector(".filtered-labels");
      if (!filtered) continue;
      const metric = data.metrics[plot.dataset.metric];
      for (const model of data.models) {
        if (!document.getElementById(`show-${model.slug}`).checked) continue;
        const points = [...plot.querySelectorAll(`.marker.m-${model.slug}`)].filter(visible)
          .map(marker => data.levels.indexOf(marker.dataset.level));
        if (!points.length) continue;
        const costliest = points.sort((first, second) => metric.costs[model.slug][first] - metric.costs[model.slug][second]).at(-1);
        const label = labels.find(label => label.textContent.endsWith(model.name));
        const expected = metric.scores[model.slug][costliest].toFixed(metric.decimals);
        assert(label?.textContent === `${expected}${model.name}`,
          `${plot.dataset.metric}: ${model.name} must label its costliest visible point, expected ${expected}, got ${label?.textContent}`);
      }
    }
  };
  check();
  setModels(["opus-5-5", "gpt-6-2-astra", "gpt-6-2-sol", "gpt-6-astra", "gpt-6-1-sol"]);
  await settle();
  check();
  setModels(["gemini-4-carbon"]);
  await settle();
  const cursor = document.querySelector('.panel[data-chart="cursorbench-4-1"] > .plot');
  assert(cursor.querySelector(".filtered-labels").textContent.includes("55.0Gemini 4 Carbon"),
    "Carbon's costliest CursorBench point is low ($8.64, 55.0), not its highest-effort high point ($8.52, 61.5)");
  document.querySelector("#models-all").click();
  await settle();
  return "Cost labels sit in the plot, omit effort, and follow each model's costliest visible point";
})();
