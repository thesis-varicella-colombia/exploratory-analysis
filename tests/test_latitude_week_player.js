"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function control(value = "") {
  return { value, listeners: {}, textContent: "",
    addEventListener(name, handler) { this.listeners[name] = handler; },
    setAttribute() {} };
}

const nodes = Object.fromEntries(["play", "timeline", "frame", "speed"]
  .map((name) => [`#latitude-week-${name}`, control(name === "speed" ? "1" : "")]));
const horizon = control("2016–2019");
horizon.options = ["2008–2014", "2016–2019", "2022–2025",
  ...Array.from({ length: 19 }, (_, index) => String(2025 - index))].map((value) => ({ value }));
const timers = new Map();
let nextTimer = 0;
let renders = 0;
const documentEvents = {};
const windowEvents = {};
const context = vm.createContext({
  Intl, console,
  document: { hidden: false, querySelector: (id) => nodes[id],
    addEventListener: (name, handler) => { documentEvents[name] = handler; } },
  window: { addEventListener: (name, handler) => { windowEvents[name] = handler; } },
  setTimeout: (handler, delay) => { timers.set(++nextTimer, { handler, delay }); return nextTimer; },
  clearTimeout: (id) => timers.delete(id),
});
const source = fs.readFileSync(path.join(__dirname, "../docs/charts.js"), "utf8");
vm.runInContext(source.slice(source.indexOf("function initLatitudeWeekPlayer("),
  source.indexOf("async function loadLatitudeHeatmap(")), context);
context.initLatitudeWeekPlayer(horizon, async () => { renders += 1; });

async function advance() {
  assert.equal(timers.size, 1);
  const [id, timer] = [...timers][0];
  timers.delete(id);
  await timer.handler();
}

(async () => {
  nodes["#latitude-week-play"].listeners.click();
  assert.equal([...timers.values()][0].delay, 1200);
  await advance();
  assert.equal(horizon.value, "2022–2025");
  await advance();
  assert.equal(horizon.value, "2008–2014");
  nodes["#latitude-week-speed"].value = "0.5";
  nodes["#latitude-week-speed"].listeners.change();
  assert.equal([...timers.values()][0].delay, 2400);
  nodes["#latitude-week-speed"].value = "2";
  nodes["#latitude-week-speed"].listeners.change();
  assert.equal([...timers.values()][0].delay, 600);
  horizon.value = "2025";
  await horizon.listeners.change();
  assert.equal(timers.size, 0);
  assert.equal(nodes["#latitude-week-timeline"].max, "18");
  nodes["#latitude-week-play"].listeners.click();
  await advance();
  assert.equal(horizon.value, "2007");
  nodes["#latitude-week-timeline"].value = "7";
  await nodes["#latitude-week-timeline"].listeners.input();
  assert.equal(horizon.value, "2014");
  assert.equal(timers.size, 0);
  nodes["#latitude-week-play"].listeners.click();
  context.document.hidden = true;
  documentEvents.visibilitychange();
  assert.equal(timers.size, 0);
  assert(renders >= 5);
  context.document.hidden = false;
  nodes["#latitude-week-play"].listeners.click();
  windowEvents.pagehide();
  assert.equal(timers.size, 0);
  assert.equal(nodes["#latitude-week-play"].textContent, "▶ Reproducir");
  console.log("Latitude heatmap playback, wrapping, speed, scrubbing and cleanup verified.");
})().catch((error) => { console.error(error); process.exitCode = 1; });
