// Run in the generated page with agent-browser eval --stdin.
(async () => {
  const assert = (condition, message) => { if (!condition) throw new Error(message); };
  const settle = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(resolve))));
  document.querySelector("#models-all").click();
  document.querySelector("#levels-all").click();
  for (const mode of ["effort", "cost"]) {
    document.querySelector(`label[for="x-${mode}"]`).click();
    await settle();
    const outside = [];
    for (const panel of document.querySelectorAll(".panel:not([hidden])")) {
      const card = panel.getBoundingClientRect();
      for (const label of panel.querySelectorAll(":scope > .plot[data-row-height] .end text")) {
        const bounds = label.getBoundingClientRect();
        if (bounds.width && (bounds.left < card.left + 4 || bounds.right > card.right - 4)) {
          outside.push(`${panel.querySelector("h3").textContent}: ${label.textContent} (${bounds.right - card.right}px)`);
        }
      }
    }
    assert(!outside.length, `${mode}: every bar score and effort label must stay inside its card: ${outside.join(", ")}`);
  }
  document.querySelector('label[for="x-effort"]').click();
  await settle();
  return "Bar metadata checks passed in both views";
})();
