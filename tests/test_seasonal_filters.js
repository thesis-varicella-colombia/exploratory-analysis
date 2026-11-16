"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const weeks = Array.from({ length: 18 }, (_, year) => Array.from({ length: 52 }, (_, week) => [2008 + year, week + 1])).flat();
const entities = [{ id: "national", name: "Colombia", dimension: "national" },
  ...Array.from({ length: 33 }, (_, i) => ({ id: `department_${String(i).padStart(2, "0")}`,
    name: `Departamento ${i}`, dimension: "department", code: String(i).padStart(2, "0") })),
  ...Array.from({ length: 1122 }, (_, i) => ({ id: `municipality_${String(i).padStart(5, "0")}`,
    name: `Municipio ${i}`, dimension: "municipality", code: String(i).padStart(5, "0"), department: "00" }))];
const payload = (id) => ({ id, series: Object.fromEntries(["notification", "symptom"].map((method) =>
  [method, Object.fromEntries(["all", "5_14", "15_49"].map((group) =>
    [group, Array(weeks.length).fill(id === "national" ? 1 : method === "symptom" ? 3 : 2)]))])) });
const label = "Municipio 1 · Departamento 0 (00001)";

function control(value = "") {
  return { value, textContent: "", disabled: true, hidden: false, listeners: {}, children: [],
    selectedOptions: [{ textContent: "Notificación" }],
    addEventListener(event, handler) { this.listeners[event] = handler; },
    append(child) { this.children.push(child); },
    setAttribute(name, value) { this[name] = value; },
    querySelector() { return {}; } };
}
const nodes = Object.fromEntries(["#seasonal-filters", "#seasonal-date", "#seasonal-territory",
  "#seasonal-filter-status", "#seasonal-territory-options",
  "#chart-seasonal-total", "#chart-seasonal-2008-2014", "#chart-seasonal-2016-2019",
  "#chart-seasonal-2022-2025"].map((id) => [id, control()]));
nodes["#seasonal-date"].value = "notification";
const updates = [];
const context = vm.createContext({
  console, Intl, Number, Map, Set, Promise, TextDecoder,
  SEASONAL_TERRITORY_ROOT: "data_processed/estacionalidad/seasonal_territories",
  SEASONAL_PERIODS: [{ label: "2008–2014", start: 2008, end: 2014 },
    { label: "2016–2019", start: 2016, end: 2019 }, { label: "2022–2025", start: 2022, end: 2025 }],
  SEASONAL_CHART_IDS: ["#chart-seasonal-total", "#chart-seasonal-2008-2014",
    "#chart-seasonal-2016-2019", "#chart-seasonal-2022-2025"],
  AGE_LABELS: { "5_14": "5–14 años", "15_49": "15–49 años" },
  SCHEMA: "vega-lite", CHART_WIDTH: 650, vegaEmbed: () => {},
  document: { querySelector: (id) => nodes[id], createElement: () => control() },
  fetch: async (url) => ({ ok: true, json: async () => ({ version: 1, weeks, entities }),
    arrayBuffer: async () => Buffer.from(JSON.stringify(payload(url.match(/(national|municipality_00001)\.json/)[1]))) }),
  renderChart: async (_id, _title, spec) => {
    assert.equal(spec.data.name, "seasonal_data");
    return { change(name, changes) { assert.equal(name, "seasonal_data"); updates.push(changes.rows);
      return this; }, runAsync: async () => {} };
  },
  vega: { changeset: () => ({ remove() { return this; }, insert(rows) { this.rows = rows; return this; } }) },
});
const source = fs.readFileSync("docs/charts.js", "utf8");
vm.runInContext(source.slice(source.indexOf("function linearQuantile("), source.indexOf("function sharedSpec(")), context);

(async () => {
  await context.loadSeasonalCharts([]);
  assert.equal(nodes["#seasonal-filters"].disabled, false);
  assert.equal(nodes["#seasonal-territory"].value, "Colombia");
  assert.equal(nodes["#seasonal-territory-options"].children.length, 1156);
  nodes["#seasonal-territory"].value = label;
  nodes["#seasonal-territory"].listeners.input();
  for (let i = 0; i < 10 && !updates.length; i++) await new Promise((resolve) => setImmediate(resolve));
  assert.equal(updates.length, 4);
  assert.equal(updates[0][0].median, 2);
  nodes["#seasonal-date"].value = "symptom";
  nodes["#seasonal-date"].selectedOptions[0].textContent = "Inicio de síntomas";
  nodes["#seasonal-date"].listeners.change();
  for (let i = 0; i < 10 && updates.length < 8; i++) await new Promise((resolve) => setImmediate(resolve));
  assert.equal(updates.length, 8);
  assert.equal(updates[4][0].median, 3);
  assert.match(nodes["#seasonal-filter-status"].textContent, /inicio de síntomas/);
  nodes["#seasonal-territory"].value = "Colombia";
  nodes["#seasonal-date"].value = "notification";
  nodes["#seasonal-territory"].listeners.input();
  for (let i = 0; i < 10 && updates.length < 12; i++) await new Promise((resolve) => setImmediate(resolve));
  assert.equal(updates[8][0].median, 1);
  console.log("Seasonal date and territory filters update all four charts.");
})().catch((error) => { console.error(error); process.exitCode = 1; });
