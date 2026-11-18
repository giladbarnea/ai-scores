// Run in the generated page: agent-browser --session ai-scores-test eval --stdin < test_dominance.js
(async () => {
  if (document.readyState !== "complete") await new Promise(resolve => window.addEventListener("load", resolve, { once: true }));
  const assert = (condition, message) => { if (!condition) throw new Error(message); };
  const settle = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(resolve))));
  const models = ["gpt-6-2-astra", "gpt-6-2-sol", "opus-5-5"];
  document.querySelectorAll('input[id^="show-"]').forEach(input => {
    if (input.checked !== models.includes(input.value)) input.click();
  });
  document.getElementById("levels-all").click();
  document.querySelector('label[for="x-cost"]').click();
  await settle();

  const arc = document.querySelector('.plot[data-mode="cost"][data-metric="arc-agi-2"]');
  const sol = "gpt-6-2-sol";
  const max = `[data-loser-model="${sol}"][data-loser-level="max"]`;
  const link = () => arc.querySelector(`.dominance-link${max}`);
  const directsTo = level => link()?.dataset.winnerModel === sol && link()?.dataset.winnerLevel === level;
  assert(arc.querySelectorAll(".dominance-link").length === 8, "ARC must have one grey arrow for each of eight beaten points");
  assert(directsTo("high"), "ARC Sol max must point straight to high, not to the nearer but beaten xhigh");
  document.querySelector('label[for="level-high"]').click();
  await settle();
  assert(directsTo("xhigh"), "Hiding high must reroute the arrow to the visible unbeaten xhigh setting");
  document.querySelector('label[for="level-high"]').click();
  await settle();

  arc.scrollIntoView({ block: "center" });
  const hit = arc.querySelector(`.dominance-hit${max}`);
  const middle = hit.getPointAtLength(hit.getTotalLength() / 2).matrixTransform(hit.getScreenCTM());
  assert(document.elementFromPoint(middle.x, middle.y) === hit, "The visible arrow must receive pointer input over the point targets");
  const markers = ["max", "high"].map(level => arc.querySelector(`.marker.m-${sol}[data-level="${level}"]`));
  const [loser, winner] = markers.map(marker => getComputedStyle(marker.querySelector("use")));
  assert(loser.fill === "rgb(137, 135, 129)" && winner.fill !== loser.fill, "Only the beaten setting should turn grey");
  assert(loser.stroke === "none" && winner.stroke === "none", "Neither endpoint should gain a ring");
  const bounds = () => markers.map(marker => marker.getBoundingClientRect());
  const before = bounds();
  const pointer = type => hit.dispatchEvent(new PointerEvent(type, { pointerType: "mouse", clientX: middle.x, clientY: middle.y }));
  const animationsFinish = async () => {
    getComputedStyle(markers[0]).transform;
    await Promise.all(markers.flatMap(marker => marker.getAnimations().map(animation => animation.finished)));
  };
  pointer("pointerenter");
  await animationsFinish();
  for (const [index, after] of bounds().entries()) {
    const prior = before[index];
    const growth = after.width / prior.width;
    assert(Math.abs(growth - 1.3) < .02, `A hovered endpoint must grow by 30%, got ${growth}x`);
    assert(Math.hypot(after.x + after.width / 2 - prior.x - prior.width / 2,
      after.y + after.height / 2 - prior.y - prior.height / 2) < .6, "The marker center must stay fixed during enlargement");
  }
  const tooltip = arc.querySelector(".dominance-hover .tip");
  assert(tooltip?.innerText.includes("Beaten by GPT-6.2 Sol high: 85.8 at $0.133"), "Hover must identify the two actual settings");
  const tipBox = tooltip.getBoundingClientRect();
  assert(tipBox.width > 0 && tipBox.left >= 0 && tipBox.right <= innerWidth, "The tooltip must stay within the viewport");
  assert(bounds().every(box => box.bottom <= tipBox.top || box.top >= tipBox.bottom
    || box.right <= tipBox.left || box.left >= tipBox.right), "The tooltip must not hide either highlighted point");
  pointer("pointerleave");
  await animationsFinish();
  assert(bounds().every((box, index) => Math.abs(box.width - before[index].width) < .5), "Leaving the arrow must restore both sizes");
  return "Dominance checks passed: direct links, filter changes, grey points, centered hover and bounded tooltip";
})();
