// Run in the generated page, then open its returned URL in a fresh tab and run again.
(async () => {
  if (document.readyState !== "complete") await new Promise(resolve => window.addEventListener("load", resolve, { once: true }));
  const assert = (condition, message) => { if (!condition) throw new Error(message); };
  const models = [...document.querySelectorAll('input[id^="show-"]')];
  const levels = [...document.querySelectorAll('input[name="thinking-level"]')];
  const selected = inputs => inputs.filter(input => input.checked).map(input => input.value).sort().join(",");
  const wantedModels = "fable-5-2,gpt-6-2-sol";
  const wantedLevels = "high,max";
  const incoming = new URL(location.href).searchParams;
  if (incoming.has("models")) {
    assert(selected(models) === wantedModels, `A shared URL did not restore its models: ${selected(models)}`);
    assert(selected(levels) === wantedLevels, `A shared URL did not restore its levels: ${selected(levels)}`);
    assert(document.getElementById("x-cost").checked, "A shared Cost URL opened in effort mode");
    const plot = document.querySelector('.plot[data-metric="aa-intelligence-index"]');
    const points = [...plot.querySelectorAll(".marker")].filter(node => getComputedStyle(node).display !== "none");
    assert(points.length === 4, `The shared two-model, two-level view must show four AA Index points, got ${points.length}`);
  }
  models.forEach(input => { if (input.checked !== wantedModels.split(",").includes(input.value)) input.click(); });
  document.getElementById("levels-none").click();
  document.querySelector('label[for="level-high"]').click();
  document.querySelector('label[for="level-max"]').click();
  document.querySelector('label[for="x-cost"]').click();
  const params = new URL(location.href).searchParams;
  assert(params.get("axis") === "cost", "Changing the x axis must update the URL");
  assert(params.get("models")?.split(",").sort().join(",") === wantedModels, "The URL must contain exactly the selected models");
  assert(params.get("levels")?.split(",").sort().join(",") === wantedLevels, "The URL must contain exactly the selected levels");
  const shared = location.href;
  history.pushState(history.state, "", shared);
  document.getElementById("levels-none").click();
  models.forEach(input => { if (input.checked) input.click(); });
  const empty = new URL(location.href).searchParams;
  assert(empty.has("models") && empty.get("models") === "", "No models must be explicit, not confused with the all-models default");
  assert(empty.has("levels") && empty.get("levels") === "", "No levels must be explicit, not confused with the all-levels default");
  const back = new Promise(resolve => window.addEventListener("popstate", resolve, { once: true }));
  history.back();
  await back;
  assert(selected(models) === wantedModels && selected(levels) === wantedLevels,
    "Browser Back must restore the model and level selection from the URL");
  assert(document.getElementById("x-cost").checked, "Browser Back must restore the cost axis too");
  return location.href;
})();
