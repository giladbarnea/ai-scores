// Run in the generated page with agent-browser eval --stdin.
(async () => {
  const assert = (condition, message) => { if (!condition) throw new Error(message); };
  const settle = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(resolve))));
  document.querySelector("#models-all").click();
  document.querySelector("#levels-all").click();
  for (const mode of ["effort", "cost"]) {
    document.querySelector(`label[for="x-${mode}"]`).click();
    await settle();
    const plot = document.querySelector('.panel > .plot[data-metric="vals-index-vals-reasoning-study"]');
    const ticks = [...plot.querySelectorAll(".score-axis text, .fitted-score-axis text")]
      .filter(node => node.getBoundingClientRect().width).map(node => Number(node.textContent));
    assert(Math.min(...ticks) <= 55.9 && Math.max(...ticks) >= 71 && Math.max(...ticks) - Math.min(...ticks) <= 25,
      `${mode}: default Vals reasoning scores 55.9–71 must fill the score axis, got ${ticks}`);
  }
  document.querySelector('label[for="x-effort"]').click();
  await settle();
  return "Default score fit passed in both views without changing scores";
})();
