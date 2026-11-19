// Run in the generated page: agent-browser --session ai-scores-versions eval --stdin < test_versions.js
(async () => {
  const assert = (condition, message) => { if (!condition) throw new Error(message); };
  const settle = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(resolve))));
  const visible = node => node.getClientRects().length > 0;
  document.querySelector("#levels-none").click();
  await settle();
  assert(![...document.querySelectorAll(".panel")].some(visible), "No thinking levels must hide every chart, not leave empty cards");
  assert(![...document.querySelectorAll("main > section")].some(visible), "A section with no charts must disappear too");
  document.querySelector("#levels-all").click();
  await settle();
  assert([...document.querySelectorAll(".panel")].some(visible), "Selecting levels again must restore charts");
  document.querySelector("#models-all").click();
  await settle();
  const panel = name => document.querySelector(`.panel[data-chart="${name}"]`);
  const latest = panel("terminal-bench-4-1-provider-agents");
  const older = panel("terminal-bench-2-1");
  assert(visible(latest) && !visible(older) && !visible(panel("terminal-bench-4-0")),
    "A benchmark family must show only its newest version with data, not older runner charts");
  const notice = latest.querySelector(".older-versions");
  assert(visible(notice) && notice.textContent === "Some of the selected models have scores in older versions",
    "The current chart must quietly name available historical coverage");
  notice.click();
  const chooser = document.querySelector("#benchmark-versions");
  assert(chooser.open, "Pressing the older-version line must open its model/version list");
  const row = chooser.querySelector('[data-version-choice="terminal-bench-2-1"]');
  assert(row?.textContent.includes("GPT-6 Astra") && row.textContent.includes("Terminal-Bench 2.1"),
    "Each historical-version row must identify its selected models and version");
  const before = location.href;
  row.click();
  await settle();
  assert(!chooser.open && visible(older) && !visible(latest), "Choosing a row must replace the chart with that version");
  assert(older.dataset.temporary === "true" && older.textContent.includes("Older version"), "Historical browsing must be clearly temporary and marked old");
  assert(location.href === before && document.querySelector("#show-gpt-6-astra").checked,
    "A historical-version visit must not change filters or their shared URL");
  older.querySelector(".version-reset").click();
  await settle();
  assert(visible(latest) && !visible(older), "One reset must return to the newest version with data");
  const setModels = names => document.querySelectorAll('input[id^="show-"]').forEach(input => {
    if (input.checked !== names.includes(input.value)) input.click();
  });
  setModels(["mai-code-2"]);
  await settle();
  const microsoft = panel("terminal-bench-2-1-microsoft");
  assert(visible(microsoft) && !visible(latest) && !visible(older), "MAI alone must automatically fall back to its Microsoft TB2.1 chart");
  assert(microsoft.textContent.includes("Older version") && microsoft.dataset.temporary === "false",
    "An automatic fallback is old but not a manual temporary visit");
  assert([...document.querySelectorAll(".panel:not([hidden]) > .plot")].every(plot =>
    [...plot.querySelectorAll(".marker, .bar")].some(visible)), "Sparse-model selection must never leave an empty chart card");
  document.querySelector('label[for="show-gpt-6-2-astra"]').click();
  await settle();
  assert(visible(latest) && !visible(microsoft), "A model with TB4.1 must restore the new version and hide MAI's old runner lane");
  latest.querySelector(".older-versions").click();
  const microsoftRow = chooser.querySelector('[data-version-choice="terminal-bench-2-1-microsoft"]');
  assert(microsoftRow.textContent.includes("MAI Code 2") && microsoftRow.textContent.includes("Microsoft Copilot CLI"),
    "The old-score row must identify both the model and the runner");
  const filters = location.href;
  microsoftRow.click();
  await settle();
  assert(visible(microsoft) && !visible(latest) && location.href === filters, "Visiting MAI's old lane must not change either model filter");
  document.querySelector("#levels-none").click();
  document.querySelector('label[for="level-low"]').click();
  await settle();
  assert(visible(panel("terminal-bench-4-0")) && !visible(microsoft) && !visible(latest),
    "A low-only filter must clear the temporary visit and fall back to Astra's AA TB4.0 low point");

  setModels(["fable-5-2"]);
  document.querySelector("#levels-none").click();
  document.querySelector('label[for="level-high"]').click();
  await settle();
  assert(!visible(latest) && visible(panel("terminal-bench-4-0")) && visible(panel("terminal-bench-4-0-vals")),
    "When TB4.1 has no high point, both populated TB4.0 runner charts must show without mixing their points");
  assert(panel("terminal-bench-4-0").textContent.includes("Older version"), "A fallback from 4.1 to 4.0 must be marked old");
  document.querySelector("#models-all").click();
  document.querySelector("#levels-all").click();
  await settle();
  assert(visible(latest) && !visible(microsoft), "Clearing filters must restore the current version");
  setModels(["gemini-4-neon"]);
  document.querySelector('label[for="x-cost"]').click();
  await settle();
  assert(!visible(latest) && visible(panel("terminal-bench-4-0")),
    "Cost mode must fall back when the newest version has no price for the selected model");
  setModels(["mai-code-2"]);
  await settle();
  assert(visible(microsoft), "MAI's old cost point must remain available in Cost mode");
  document.querySelector('label[for="x-effort"]').click();
  document.querySelector("#models-all").click();
  await settle();
  return "Version checks passed: hidden empty cards, newest populated version, runner lanes, old-score dialog, automatic fallback, temporary visits, Cost and reset";
})();
