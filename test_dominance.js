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
  assert([...arc.querySelectorAll(".dominance-link")].every(arrow => getComputedStyle(arrow).opacity === "0.12"),
    "Unselected comparisons must stay faint at 12% opacity");
  assert(directsTo("high"), "ARC Sol max must point straight to high, not to the nearer but beaten xhigh");
  document.querySelector('label[for="level-high"]').click();
  await settle();
  assert(directsTo("xhigh"), "Hiding high must reroute the arrow to the visible unbeaten xhigh setting");
  document.querySelector('label[for="level-high"]').click();
  await settle();

  arc.scrollIntoView({ block: "center" });
  await settle();
  const hit = arc.querySelector(`.dominance-hit${max}`);
  const middle = hit.getPointAtLength(hit.getTotalLength() / 2).matrixTransform(hit.getScreenCTM());
  const target = arc.querySelector(`.cost-point.m-${sol}[data-level="max"]`);
  const targetBox = target.getBoundingClientRect();
  assert(document.elementFromPoint(targetBox.x + targetBox.width / 2, targetBox.y + targetBox.height / 2).closest(".cost-point"),
    "Point targets must receive input at the marker center instead of a nearby arrow");
  const markers = ["max", "high"].map(level => arc.querySelector(`.marker.m-${sol}[data-level="${level}"]`));
  const [loser, winner] = markers.map(marker => getComputedStyle(marker.querySelector("use")));
  assert(loser.fill === winner.fill && loser.fill !== "rgb(137, 135, 129)", "Beaten settings keep their model color; only the faint arrow marks them");
  assert(loser.stroke === "none" && winner.stroke === "none", "Neither endpoint should gain a ring");
  const bounds = () => markers.map(marker => marker.getBoundingClientRect());
  const before = bounds();
  const pointer = (node, type, pointerType = "mouse", offset = 0) => node.dispatchEvent(new PointerEvent(type, {
    pointerType, clientX: middle.x + offset, clientY: middle.y, bubbles: true, relatedTarget: document.body,
  }));
  const faint = () => [...arc.querySelectorAll(".dominance-link")].every(arrow => getComputedStyle(arrow).opacity === "0.12");
  const single = arrow => document.querySelectorAll(".dominance-link.highlighted").length === 1
    && getComputedStyle(arrow).opacity === "1"
    && [...arc.querySelectorAll(".dominance-link:not(.highlighted)")].every(other => getComputedStyle(other).opacity === "0.12");
  const animationsFinish = async () => {
    getComputedStyle(markers[0]).transform;
    await Promise.all(markers.flatMap(marker => marker.getAnimations().map(animation => animation.finished)));
  };
  pointer(target, "pointerover");
  assert(single(link()), "Hovering a beaten point must strengthen exactly its own arrow");
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
  pointer(target, "pointerout");
  await animationsFinish();
  assert(faint() && bounds().every((box, index) => Math.abs(box.width - before[index].width) < .5),
    "Leaving the comparison must restore faint arrows and both marker sizes");

  pointer(hit, "pointerover");
  assert(single(link()), "Hovering an arrow must strengthen only that comparison");
  const otherHit = arc.querySelector('.dominance-hit[data-loser-model="opus-5-5"][data-loser-level="low"]');
  const otherLink = arc.querySelector('.dominance-link[data-loser-model="opus-5-5"][data-loser-level="low"]');
  const arrowMiddle = otherHit.getPointAtLength(otherHit.getTotalLength() / 2).matrixTransform(otherHit.getScreenCTM());
  assert(document.elementFromPoint(arrowMiddle.x, arrowMiddle.y) === otherHit,
    "A long arrow must remain reachable away from the point targets");
  pointer(otherHit, "pointerover");
  assert(single(otherLink) && !link().classList.contains("highlighted"), "Moving to another comparison must replace, not accumulate, highlights");
  pointer(otherHit, "pointerout");

  pointer(target, "pointerover", "touch");
  pointer(target, "pointerdown", "touch");
  assert(faint(), "Touching down must not highlight before a tap completes");
  pointer(target, "pointerup", "touch");
  assert(single(link()) && getComputedStyle(arc.querySelector(".dominance-hover .tip")).display !== "none",
    "A beaten-point tap must pin one arrow and its tooltip");
  pointer(otherHit, "pointerdown", "touch");
  pointer(otherHit, "pointerup", "touch");
  assert(single(otherLink), "An arrow tap must replace the pinned comparison");
  pointer(document.body, "pointerdown", "touch");
  pointer(document.body, "pointerup", "touch");
  assert(faint() && !arc.querySelector(".dominance-hover"), "Tapping elsewhere must dismiss the pinned comparison");

  pointer(target, "pointerdown", "touch");
  pointer(target, "pointermove", "touch", 20);
  pointer(target, "pointerup", "touch");
  assert(faint(), "A scrolling gesture must not become a tap even if it ends at its starting position");
  pointer(target, "pointerdown", "touch");
  pointer(target, "pointercancel", "touch");
  pointer(target, "pointerup", "touch");
  assert(faint(), "A cancelled touch must not pin a comparison");

  pointer(target, "pointerdown", "touch");
  pointer(target, "pointerup", "touch");
  document.querySelector('label[for="level-high"]').click();
  await settle();
  assert(faint() && !arc.querySelector(".dominance-hover"), "Changing filters must clear pinned comparisons before rerouting them");
  document.querySelector('label[for="level-high"]').click();
  await settle();
  return "Dominance checks passed: faint defaults, single point/arrow hover and taps, dismissal, gesture cancellation, filters and bounded tooltip";
})();
