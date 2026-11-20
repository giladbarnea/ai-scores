// Run at a desktop width in the generated page with agent-browser eval --stdin.
(async () => {
  if (innerWidth < 960) return "Card packing applies to desktop only";
  const assert = (condition, message) => { if (!condition) throw new Error(message); };
  const settle = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(resolve))));
  for (const mode of ["effort", "cost"]) {
    document.querySelector(`label[for="x-${mode}"]`).click();
    document.querySelector("#models-all").click();
    document.querySelector("#levels-all").click();
    await settle();
    for (const grid of document.querySelectorAll(".grid")) {
      const cards = [...grid.querySelectorAll(".panel")].map(panel => ({name: panel.querySelector("h3").textContent,
        box: panel.getBoundingClientRect()})).filter(card => card.box.width);
      for (const card of cards) {
        const next = cards.filter(other => Math.abs(other.box.left - card.box.left) < 1 && other.box.top > card.box.top)
          .sort((first, second) => first.box.top - second.box.top)[0];
        if (!next) continue;
        const gap = next.box.top - card.box.bottom;
        assert(Math.abs(gap - 16) < 1, `${mode}: ${card.name} must not reserve its neighbour's height: next gap ${gap}px`);
      }
    }
  }
  document.querySelector('label[for="x-effort"]').click();
  await settle();
  return "Desktop cards pack independently in both views";
})();
