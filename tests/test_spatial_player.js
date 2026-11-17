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
  .map((name) => [`#spatial-${name}`, control(name === "speed" ? "1" : "")]));
const horizon = control("2015-2019");
horizon.options = ["2008-2014", "2015-2019", "2020-2021", "2022-2025",
  ...Array.from({ length: 18 }, (_, index) => String(2025 - index))].map((value) => ({ value }));
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
const source = fs.readFileSync(path.join(__dirname, "../docs/spatial.js"), "utf8");
vm.runInContext(source.slice(source.indexOf("function initSpatialPlayer("),
  source.indexOf("async function loadSpatialMap(")), context);
context.initSpatialPlayer(horizon, async () => { renders += 1; });

async function advance() {
  assert.equal(timers.size, 1);
  const [id, timer] = [...timers][0];
  timers.delete(id);
  await timer.handler();
}

(async () => {
  nodes["#spatial-play"].listeners.click();
  assert.equal([...timers.values()][0].delay, 1200);
  await advance();
  assert.equal(horizon.value, "2020-2021");
  await advance();
  assert.equal(horizon.value, "2022-2025");
  await advance();
  assert.equal(horizon.value, "2008-2014");
  nodes["#spatial-speed"].value = "0.5";
  nodes["#spatial-speed"].listeners.change();
  assert.equal([...timers.values()][0].delay, 2400);
  nodes["#spatial-speed"].value = "2";
  nodes["#spatial-speed"].listeners.change();
  assert.equal([...timers.values()][0].delay, 600);
  horizon.value = "2025";
  await horizon.listeners.change();
  assert.equal(timers.size, 0);
  assert.equal(nodes["#spatial-timeline"].max, "17");
  nodes["#spatial-play"].listeners.click();
  await advance();
  assert.equal(horizon.value, "2008");
  nodes["#spatial-timeline"].value = "7";
  await nodes["#spatial-timeline"].listeners.input();
  assert.equal(horizon.value, "2015");
  assert.equal(timers.size, 0);
  nodes["#spatial-play"].listeners.click();
  context.document.hidden = true;
  documentEvents.visibilitychange();
  assert.equal(timers.size, 0);
  assert(renders >= 5);
  context.document.hidden = false;
  nodes["#spatial-play"].listeners.click();
  windowEvents.pagehide();
  assert.equal(timers.size, 0);
  assert.equal(nodes["#spatial-play"].textContent, "▶ Reproducir");
  console.log("Municipal incidence playback, wrapping, speed, scrubbing and cleanup verified.");
})().catch((error) => { console.error(error); process.exitCode = 1; });
