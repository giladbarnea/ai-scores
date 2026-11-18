// Keep inactive SVG layouts out of the live document; large benchmark collections otherwise stall on resize.
(() => {
  const data = JSON.parse(document.getElementById("chart-data").textContent);
  const { layouts } = data;
  const levelInputs = [...document.querySelectorAll('input[name="thinking-level"]')];
  const pointCache = new WeakMap();
  const entries = [...document.querySelectorAll("template[data-layout]")].map(template => ({
    template, plot: template.content.firstElementChild, layout: template.dataset.layout,
  }));
  let active;

  function mountLayout() {
    const layout = layouts.findLast(layout => innerWidth >= layout.minViewport).name;
    const mode = document.getElementById("x-cost").checked ? "cost" : "effort";
    const selection = `${layout} ${mode}`;
    if (selection === active) return;
    for (const entry of entries) {
      if (entry.layout === layout && entry.plot.classList.contains(mode)) {
        entry.template.before(entry.plot);
        continue;
      }
      entry.template.content.append(entry.plot);
    }
    active = selection;
    applyFilters();
  }

  // With a mouse, drag to zoom. On touch screens, hold still first so a quick swipe can still scroll.
  const dialog = document.getElementById("zoom");
  const plotHost = dialog.querySelector(".zoom-plot");
  const SVG = "http://www.w3.org/2000/svg";
  const MINIMUM_DRAG_PIXELS = 8;
  const LONG_PRESS_MILLISECONDS = 1000;
  const LONG_PRESS_TOLERANCE_PIXELS = 8;  // a finger that moves farther before the press completes is scrolling
  const LABEL_GAP_PIXELS = 21;
  const MARGIN = { left: 60, right: 170, top: 16, bottom: 44 };
  // Below this plot width the zoom drops the model names beside the points (its legend names the colors) to give the plot room.
  const COMPACT_WIDTH = 520;
  const COMPACT_MARGIN = { left: 40, right: 44, top: 12, bottom: 36 };
  let drag = null;
  let press = null;
  let shown = null;

  document.body.classList.add("zoomable");

  const clamp = (value, low, high) => Math.min(high, Math.max(low, value));

  function axesBox(plot) {
    const box = plot.getBoundingClientRect();
    const [left, top, width, height] = plot.dataset.axes.split(",").map(Number);
    return { x: box.left + box.width * left / 100, y: box.top + box.height * top / 100,
             width: box.width * width / 100, height: box.height * height / 100 };
  }

  function toData(metric, axes, clientX, clientY) {
    const [xLow, xHigh] = data.xLimits;
    const [yLow, yHigh] = metric.yRange;
    return {
      level: xLow + clamp((clientX - axes.x) / axes.width, 0, 1) * (xHigh - xLow),
      score: yHigh - clamp((clientY - axes.y) / axes.height, 0, 1) * (yHigh - yLow),
    };
  }

  function startDrag(plot, clientX, clientY) {
    const box = document.createElement("div");
    box.className = "selection";
    plot.append(box);
    document.body.classList.add("dragging");
    drag = { plot, box, startX: clientX, startY: clientY, endX: clientX, endY: clientY };
  }

  function endDrag() {
    const finished = drag;
    drag = null;
    finished.box.remove();
    document.body.classList.remove("dragging");
    return finished;
  }

  function cancelPress() {
    clearTimeout(press?.timer);
    press = null;
  }

  function pressAndHold(plot, event) {
    const { clientX, clientY } = event;
    press = { clientX, clientY, timer: setTimeout(() => {
      press = null;
      startDrag(plot, clientX, clientY);
      navigator.vibrate?.(10);
    }, LONG_PRESS_MILLISECONDS) };
  }

  document.addEventListener("pointerdown", event => {
    const plot = event.target.closest(".plot.effort[data-metric]");
    if (!plot || !event.isPrimary) return;
    if (event.pointerType !== "mouse") return pressAndHold(plot, event);
    if (event.button !== 0) return;
    event.preventDefault();
    startDrag(plot, event.clientX, event.clientY);
  });

  // Once a touch selection starts, the finger draws the rectangle instead of scrolling the page.
  document.addEventListener("touchmove", event => { if (drag) event.preventDefault(); }, { passive: false });
  document.addEventListener("contextmenu", event => { if (press || drag) event.preventDefault(); });
  document.addEventListener("pointercancel", () => {
    cancelPress();
    if (drag) endDrag();
  });

  document.addEventListener("pointermove", event => {
    if (press && Math.hypot(event.clientX - press.clientX, event.clientY - press.clientY) > LONG_PRESS_TOLERANCE_PIXELS) {
      cancelPress();
    }
    if (!drag) return;
    drag.endX = event.clientX;
    drag.endY = event.clientY;
    const plotBox = drag.plot.getBoundingClientRect();
    Object.assign(drag.box.style, {
      left: `${Math.min(drag.startX, drag.endX) - plotBox.left}px`,
      top: `${Math.min(drag.startY, drag.endY) - plotBox.top}px`,
      width: `${Math.abs(drag.endX - drag.startX)}px`,
      height: `${Math.abs(drag.endY - drag.startY)}px`,
    });
  });

  document.addEventListener("pointerup", () => {
    cancelPress();
    if (!drag) return;
    const finished = endDrag();
    const tooSmall = Math.abs(finished.endX - finished.startX) < MINIMUM_DRAG_PIXELS
      || Math.abs(finished.endY - finished.startY) < MINIMUM_DRAG_PIXELS;
    if (tooSmall) return;
    const metric = data.metrics[finished.plot.dataset.metric];
    const axes = axesBox(finished.plot);
    const topLeft = toData(metric, axes, Math.min(finished.startX, finished.endX), Math.min(finished.startY, finished.endY));
    const bottomRight = toData(metric, axes, Math.max(finished.startX, finished.endX), Math.max(finished.startY, finished.endY));
    const points = selectedPoints(metric, topLeft, bottomRight);
    if (!points.length) return;
    shown = { metric, points };
    dialog.showModal();
    dialog.focus();  // the close button would otherwise take focus and show its ring
    render();
  });

  function selectedPoints(metric, topLeft, bottomRight) {
    const visible = data.models.filter(model =>
      model.slug in metric.scores && document.getElementById(`show-${model.slug}`).checked);
    return visible.flatMap(model => metric.scores[model.slug]
      .map((score, level) => ({ model, level, score }))
      .filter(point => point.score !== null && levelIsShown(data.levels[point.level])
        && point.level >= topLeft.level && point.level <= bottomRight.level
        && point.score <= topLeft.score && point.score >= bottomRight.score));
  }

  // Round tick values that cover the scores with a little headroom, about five steps.
  function niceTicks(low, high) {
    const padding = Math.max((high - low) * 0.12, Math.abs(high) * 0.01, 0.5);
    const paddedLow = low - padding;
    const paddedHigh = high + padding;
    const rawStep = (paddedHigh - paddedLow) / 5;
    const magnitude = 10 ** Math.floor(Math.log10(rawStep));
    const step = [1, 2, 2.5, 5, 10].map(factor => factor * magnitude).find(candidate => candidate >= rawStep);
    const first = Math.floor(paddedLow / step) * step;
    const last = Math.ceil(paddedHigh / step) * step;
    const decimals = (String(Number(step.toFixed(10))).split(".")[1] || "").length;
    const values = [];
    for (let value = first; value <= last + step / 2; value += step) values.push(value);
    return { low: first, high: last, values, decimals };
  }

  // Spread sorted positions so neighbors sit at least minimumGap apart, each crowded group centered on its mean.
  function spread(positions, minimumGap) {
    const layout = group => {
      const center = group.reduce((sum, value) => sum + value, 0) / group.length;
      return group.map((_, offset) => center + (offset - (group.length - 1) / 2) * minimumGap);
    };
    const groups = [];
    for (const position of [...positions].sort((a, b) => a - b)) {
      groups.push([position]);
      while (groups.length > 1 && layout(groups.at(-1))[0] - layout(groups.at(-2)).at(-1) < minimumGap) {
        groups.splice(-2, 2, [...groups.at(-2), ...groups.at(-1)]);
      }
    }
    return groups.flatMap(layout);
  }

  function element(parent, name, attributes, style = {}) {
    const node = document.createElementNS(SVG, name);
    for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
    Object.assign(node.style, style);
    parent.append(node);
    return node;
  }

  function render() {
    const { metric, points } = shown;
    const levels = points.map(point => point.level);
    const firstLevel = Math.min(...levels);
    const lastLevel = Math.max(...levels);
    const scores = points.map(point => point.score);
    const ticks = niceTicks(Math.min(...scores), Math.max(...scores));
    const models = data.models.filter(model => points.some(point => point.model === model));
    const format = score => score.toFixed(metric.decimals);

    dialog.querySelector("h3").textContent = metric.name;
    dialog.querySelector(".zoom-unit").textContent = metric.unit;
    dialog.querySelector(".zoom-range").textContent =
      `${data.levels[firstLevel]} to ${data.levels[lastLevel]} · scores ${format(Math.min(...scores))} to ${format(Math.max(...scores))}`;
    dialog.querySelector(".zoom-legend").replaceChildren(...models.map(model => {
      const key = document.createElement("span");
      key.style.setProperty("--series", `var(--${model.color})`);
      key.textContent = model.name;
      return key;
    }));

    plotHost.replaceChildren();
    const width = plotHost.clientWidth;
    const height = plotHost.clientHeight;
    const svg = element(plotHost, "svg", { viewBox: `0 0 ${width} ${height}` });
    const compact = width < COMPACT_WIDTH;
    const margin = compact ? COMPACT_MARGIN : MARGIN;
    const x = level => margin.left + (level - firstLevel + 0.5) / (lastLevel - firstLevel + 1) * (width - margin.left - margin.right);
    const y = score => margin.top + (ticks.high - score) / (ticks.high - ticks.low) * (height - margin.top - margin.bottom);
    const text = { fontFamily: "inherit", fontSize: compact ? "13px" : "15px" };

    for (const value of ticks.values) {
      element(svg, "line", { x1: margin.left, x2: width - margin.right, y1: y(value), y2: y(value) },
        { stroke: "var(--grid)", strokeWidth: "1" });
      element(svg, "text", { x: margin.left - 12, y: y(value), "text-anchor": "end", "dominant-baseline": "middle" },
        { ...text, fill: "var(--ink-3)" }).textContent = value.toFixed(ticks.decimals);
    }
    element(svg, "line", { x1: x(firstLevel - 0.35), x2: x(lastLevel + 0.35), y1: y(ticks.low), y2: y(ticks.low) },
      { stroke: "var(--baseline)", strokeWidth: "1" });
    for (let level = firstLevel; level <= lastLevel; level += 1) {
      element(svg, "text", { x: x(level), y: height - margin.bottom + (compact ? 22 : 28), "text-anchor": "middle" },
        { ...text, fill: "var(--ink-3)" }).textContent = data.levels[level];
    }

    for (const model of models) {
      const own = points.filter(point => point.model === model);
      for (const [from, to] of own.slice(0, -1).map((point, index) => [point, own[index + 1]])) {
        if (to.level !== from.level + 1) continue;
        element(svg, "line", { x1: x(from.level), y1: y(from.score), x2: x(to.level), y2: y(to.score) },
          { stroke: `var(--${model.color})`, strokeWidth: "3", strokeLinecap: "round" });
      }
    }
    for (const point of points) {
      const estimated = metric.estimated.some(([slug, level]) => slug === point.model.slug && level === point.level);
      element(svg, "circle", { cx: x(point.level), cy: y(point.score), r: 6.5 }, {
        fill: estimated ? "var(--surface)" : `var(--${point.model.color})`,
        stroke: estimated ? `var(--${point.model.color})` : "var(--surface)",
        strokeWidth: "2",
      });
    }

    // Each level's labels sit right of their points, spread apart vertically; outside compact mode each model's last
    // point also names it.
    for (let level = firstLevel; level <= lastLevel; level += 1) {
      const column = points.filter(point => point.level === level).sort((a, b) => y(a.score) - y(b.score));
      const labelYs = spread(column.map(point => y(point.score)), LABEL_GAP_PIXELS);
      column.forEach((point, index) => {
        const pointX = x(point.level);
        const pointY = y(point.score);
        const labelY = labelYs[index];
        if (Math.abs(labelY - pointY) > 0.5) {
          element(svg, "line", { x1: pointX + 6, y1: pointY, x2: pointX + 14, y2: labelY },
            { stroke: "var(--baseline)", strokeWidth: "1" });
        }
        const label = element(svg, "text", { x: pointX + 16, y: labelY, "dominant-baseline": "middle" }, {
          ...text, fontWeight: "600", fill: "var(--ink-1)",
          stroke: "var(--surface)", strokeWidth: "4px", paintOrder: "stroke", strokeLinejoin: "round",
        });
        label.textContent = format(point.score);
        const isLast = !points.some(other => other.model === point.model && other.level > point.level);
        if (isLast && !compact) {
          const name = element(label, "tspan", { dx: "8" }, {
            fontFamily: "Menlo, monospace", fontSize: "12.5px", fontWeight: "400", fill: "var(--ink-3)",
          });
          name.textContent = point.model.name;
        }
      });
    }
  }

  function levelIsShown(level) {
    return document.getElementById(`level-${level}`).checked;
  }

  function plotPoints(plot, metric) {
    if (pointCache.has(plot)) return pointCache.get(plot);
    const points = data.models.flatMap(model => [...plot.querySelectorAll(`.marker.m-${model.slug}`)].map(marker => {
      const level = data.levels.indexOf(marker.dataset.level);
      const position = marker.querySelector("use");
      return { model, level, score: metric.scores[model.slug][level], cost: metric.costs[model.slug]?.[level], marker,
        x: Number(position.getAttribute("x")), y: Number(position.getAttribute("y")),
        target: plot.querySelector(`.cost-point.m-${model.slug}[data-level="${data.levels[level]}"]`) };
    }));
    pointCache.set(plot, points);
    return points;
  }

  function filteredLabels(plot, metric, points) {
    const svg = plot.querySelector("svg");
    const group = element(svg, "g", { class: "filtered-labels" });
    const ends = data.models.map(model => points.filter(point => point.model === model).at(-1)).filter(Boolean);
    if (!plot.dataset.axes) return filteredCostLabels(svg, group, metric, ends);
    const scoreTemplate = svg.querySelector(".end text");
    const nameTemplate = svg.querySelector(".name text");
    const labelX = Number(scoreTemplate.getAttribute("x"));
    ends.sort((first, second) => first.y - second.y);
    const heights = spread(ends.map(point => point.y), data.endLabelGap);
    ends.forEach((point, index) => {
      element(group, "path", { d: `M${point.x + 5},${point.y} L${labelX - 4},${heights[index]}` },
        { stroke: "var(--baseline)", strokeWidth: "0.6", fill: "none" });
      for (const [role, template, value] of [["end", scoreTemplate, point.score.toFixed(metric.decimals)],
                                           ["name", nameTemplate, point.model.name]]) {
        const parent = element(group, "g", { class: `${role} m-${point.model.slug}`, "data-level": data.levels[point.level] });
        const label = template.cloneNode(true);
        label.setAttribute("y", heights[index]);
        label.setAttribute("dominant-baseline", "middle");
        label.textContent = value;
        parent.append(label);
      }
    });
    filteredMeeting(group, metric, points);
  }

  function filteredCostLabels(svg, group, metric, ends) {
    const bounds = svg.querySelector("clipPath rect");
    const left = Number(bounds.getAttribute("x")) + 4;
    const right = left + Number(bounds.getAttribute("width")) - 8;
    ends.sort((first, second) => first.y - second.y);
    const heights = spread(ends.map(point => point.y - 8), data.endLabelGap);
    ends.forEach((point, index) => {
      const label = element(group, "text", { x: point.x + 7, y: heights[index], "dominant-baseline": "middle",
        "data-level": data.levels[point.level] },
        { fontSize: "9.5px", fontWeight: "500", fill: "var(--ink-1)", stroke: "var(--surface)",
          strokeWidth: "3px", paintOrder: "stroke", strokeLinejoin: "round" });
      label.textContent = point.score.toFixed(metric.decimals);
      element(label, "tspan", { dx: "5" }, { fontFamily: "Menlo, monospace", fontSize: "7.5px", fontWeight: "400",
        fill: "var(--ink-3)" }).textContent = `${point.model.name} · ${data.levels[point.level]}`;
      const box = label.getBBox();
      const x = clamp(point.x + 7, left, right - box.width);
      label.setAttribute("x", x);
      const nearX = clamp(point.x, x, x + box.width);
      const nearY = clamp(point.y, box.y, box.y + box.height);
      if (Math.hypot(nearX - point.x, nearY - point.y) <= 12) return;
      const leader = element(group, "path", { d: `M${point.x},${point.y} L${nearX},${nearY}` },
        { stroke: "var(--baseline)", strokeWidth: ".6", fill: "none" });
      label.before(leader);
    });
  }

  function filteredMeeting(group, metric, points) {
    const models = data.models.filter(model => document.getElementById(`show-${model.slug}`).checked);
    if (models.length !== 2) return;
    const first = points.filter(point => point.model === models[0]);
    const second = points.filter(point => point.model === models[1]);
    const pairs = first.flatMap(from => second.map(to => [from, to]));
    pairs.sort(([firstFrom, firstTo], [secondFrom, secondTo]) =>
      Math.abs(firstFrom.score - firstTo.score) - Math.abs(secondFrom.score - secondTo.score));
    if (!pairs.length || pairs[0][0].level === pairs[0][1].level) return;
    const [from, to] = pairs[0];
    element(group, "line", { x1: from.x, x2: to.x, y1: Math.max(from.y, to.y), y2: Math.max(from.y, to.y) },
      { stroke: "var(--ink-3)", strokeWidth: "0.9", strokeDasharray: "2.5 2.5", opacity: "0.8" });
    for (const point of [from, to]) {
      element(group, "text", { x: point.x, y: point.y - 9, "text-anchor": "middle" },
        { fontSize: "9.5px", fontWeight: "500", fill: "var(--ink-1)", stroke: "var(--surface)",
          strokeWidth: "3px", paintOrder: "stroke" }).textContent = point.score.toFixed(metric.decimals);
    }
  }

  function costFrontier(plot, metric, allPoints, points) {
    plot.querySelectorAll(".frontier").forEach(node => { node.style.display = "none"; });
    plot.querySelector(".filtered-frontier")?.remove();
    const winners = new Map(points.map(point => [point, points.filter(other =>
      other.cost <= point.cost && other.score >= point.score && (other.cost < point.cost || other.score > point.score))]));
    for (const point of allPoints) {
      const beaten = winners.get(point) || [];
      point.marker.style.opacity = beaten.length ? ".22" : "1";
      point.target.querySelectorAll(".beaten").forEach(node => node.remove());
      const cheapest = new Map([...beaten].sort((first, second) => second.cost - first.cost).map(winner => [winner.model, winner]));
      for (const winner of cheapest.values()) {
        const note = document.createElement("span");
        note.className = "beaten";
        const price = winner.target.querySelector(".cost").textContent.split(" · ")[0];
        note.textContent = `beaten by ${winner.model.name} ${data.levels[winner.level]}: ${winner.score.toFixed(metric.decimals)} at ${price}`;
        point.target.querySelector(".tip").append(note);
      }
    }
    const frontier = [...new Map(points.filter(point => !winners.get(point).length)
      .sort((first, second) => first.cost - second.cost).map(point => [`${point.cost}:${point.score}`, point])).values()];
    const svg = plot.querySelector("svg");
    const line = element(svg, "polyline", { class: "filtered-frontier", points: frontier.map(point => `${point.x},${point.y}`).join(" ") },
      { stroke: "var(--ink-2)", strokeWidth: "1.5", opacity: ".6", fill: "none", pointerEvents: "none" });
    svg.querySelector(".series").before(line);
  }

  function applyFilters() {
    const models = data.models.filter(model => document.getElementById(`show-${model.slug}`).checked);
    const partial = data.levels.some(level => !levelIsShown(level));
    for (const { plot } of entries.filter(entry => entry.plot.isConnected)) {
      const metric = data.metrics[plot.dataset.metric];
      if (!metric) {
        const bars = [...plot.querySelectorAll(".bar")].filter(bar => levelIsShown(bar.dataset.level)
          && models.some(model => bar.classList.contains(`m-${model.slug}`)));
        plot.classList.toggle("empty", !bars.length);
        continue;
      }
      const allPoints = plotPoints(plot, metric);
      const points = allPoints.filter(point => models.includes(point.model) && levelIsShown(data.levels[point.level]));
      plot.classList.toggle("empty", !points.length);
      for (const series of plot.querySelectorAll(".series")) {
        const own = points.filter(point => series.classList.contains(`m-${point.model.slug}`));
        series.querySelector("path").setAttribute("d", own.map((point, index) => `${index ? "L" : "M"}${point.x},${point.y}`).join(" "));
      }
      plot.querySelector(".filtered-labels")?.remove();
      plot.querySelectorAll(".start, .end, .name, .leader, .meeting, .meeting-line").forEach(node => {
        node.style.display = partial ? "none" : "";
      });
      if (!plot.dataset.axes) costFrontier(plot, metric, allPoints, points);
      if (partial && points.length) filteredLabels(plot, metric, points);
    }
  }

  for (const [id, checked] of [["levels-all", true], ["levels-none", false]]) {
    document.getElementById(id).addEventListener("click", () => {
      levelInputs.forEach(input => { input.checked = checked; });
      applyFilters();
    });
  }
  document.querySelectorAll('input[type="checkbox"]').forEach(input => input.addEventListener("change", applyFilters));
  mountLayout();
  window.addEventListener("resize", mountLayout);
  document.querySelectorAll('input[name="x-axis"]').forEach(input => input.addEventListener("change", mountLayout));
  dialog.addEventListener("close", () => { shown = null; });
  window.addEventListener("resize", () => { if (shown) render(); });
})();
