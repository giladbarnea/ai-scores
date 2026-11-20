// Run in the generated page with agent-browser eval --stdin.
(async () => {
  const assert = (condition, message) => { if (!condition) throw new Error(message); };
  const settle = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(resolve))));
  const visible = node => node.getBoundingClientRect().width > 0;
  const click = id => document.querySelector(`label[for="${id}"]`).click();
  document.querySelector("#models-all").click();
  document.querySelector("#levels-all").click();
  click("x-effort");
  await settle();
  const plot = name => document.querySelector(`.panel > .plot[data-metric="${name}"]`);
  const count = (chart, score) => [...chart.querySelectorAll(".start text, .end text, .meeting text, .filtered-labels text")]
    .filter(visible).filter(node => node.textContent === score).length;
  assert(count(plot("aa-intelligence-index"), "34.8") === 1,
    `A shared start point must print 34.8 once, got ${count(plot("aa-intelligence-index"), "34.8")}`);
  for (const input of document.querySelectorAll('input[id^="show-"]')) {
    if (input.checked !== ["opus-5-5", "sonnet-5-5"].includes(input.value)) click(input.id);
  }
  await settle();
  const nyt = plot("extended-nyt-connections-newest-100");
  assert(count(nyt, "83.40") === 1 && count(nyt, "79.10") === 1,
    `Start/meeting/end roles must label each NYT point once: 83.40=${count(nyt, "83.40")}, 79.10=${count(nyt, "79.10")}`);
  document.querySelector("#levels-none").click();
  click("level-high");
  await settle();
  assert(count(nyt, "90.60") === 1 && count(nyt, "79.10") === 1,
    "Single-level endpoints must not gain a duplicate meeting score");
  document.querySelector("#levels-all").click();
  for (const input of document.querySelectorAll('input[id^="show-"]')) {
    if (input.checked !== (input.value === "opus-5-5")) click(input.id);
  }
  await settle();
  assert(count(plot("aa-intelligence-index"), "34.8") === 1,
    "Hiding the other model at a shared start must retain the remaining model's start score");
  document.querySelector("#models-all").click();
  await settle();
  return "Score-label checks passed: shared starts, meetings and single-point endpoints";
})();
