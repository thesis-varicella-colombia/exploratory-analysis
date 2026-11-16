"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

function node(value = "") {
  return { value, disabled: true, textContent: "", placeholder: "", children: [], listeners: {},
    addEventListener(event, listener) { this.listeners[event] = listener; },
    append(child) { this.children.push(child); },
    replaceChildren(...children) { this.children = children; },
    setAttribute(name, value) { this[name] = value; } };
}

const periods = ["2008–2014", "2015–2019", "2022–2025"];
const periodSpecs = periods.map((label, index) => ({ label, chart: `#chart-${index}`, color: "#3569b0" }));
const nodes = Object.fromEntries(["#phase-scatter-filters", "#phase-scatter-level",
  "#phase-scatter-territory", "#phase-scatter-territory-options", "#phase-scatter-status",
  "#phase-detail-20082014", "#phase-detail-20152019", "#phase-detail-20222025",
  ...periodSpecs.map((period) => period.chart)].map((key) => [key, node()]));
nodes["#phase-scatter-level"].value = "department";
const rows = (dimension) => periods.flatMap((period) => ["1", "2"].map((code) => ({
  period, territory_code: code, territory: dimension === "department" ? `Departamento ${code}` : `Municipio ${code}`,
  department_code: code, department: `Departamento ${code}`, dimension,
  latitude: 5, peak_week: 20, amplitude_per_100k: 1, mean_rate_per_100k: 1,
})));
const municipalRows = rows("municipality").filter((row) =>
  !(row.period === "2022–2025" && row.territory_code === "2"));
function csvRead(source, options) {
  assert.equal(options.type, "csv");
  const [header, ...lines] = source.trim().split(/\r?\n/);
  const columns = header.split(",");
  return lines.map((line) => {
    const values = line.split(/,(?=(?:[^"]*"[^"]*")*[^"]*$)/)
      .map((value) => value.replace(/^"|"$/g, "").replace(/""/g, '"'));
    return Object.fromEntries(columns.map((column, index) => [column, values[index]]));
  });
}
const changes = [[], [], []];
const views = changes.map((updates) => ({ change(name, change) {
  assert.equal(name, "phase_scatter_data"); updates.push(change.rows); return this;
}, run() { return this; }, runAsync: async () => {} }));
const context = vm.createContext({
  console, Map, Promise, Number,
  PHASE_PERIODS: periodSpecs, SCHEMA: "vega-lite", CHART_WIDTH: 650,
  document: { querySelector: (selector) => nodes[selector], createElement: () => node() },
  vega: { read: csvRead,
    changeset: () => ({ remove() { return this; }, insert(rows) { this.rows = rows; return this; } }) },
});
const source = fs.readFileSync("docs/phase.js", "utf8");
vm.runInContext(source.slice(source.indexOf("function phaseRowsFromCsv("),
  source.indexOf("function phaseCorrelationSpec(")), context);

async function settled() { for (let index = 0; index < 4; index++) await new Promise(setImmediate); }

(async () => {
  const departmentData = context.phaseRowsFromCsv(fs.readFileSync(
    "docs/data_processed/estacionalidad/department_phase_2008_2025.csv", "utf8"));
  const municipalityData = context.phaseRowsFromCsv(fs.readFileSync(
    "docs/data_processed/estacionalidad/municipal_phase_2008_2025.csv", "utf8"));
  assert.equal(municipalityData.find((row) => row.territory_code === "11001").territory, "BOGOTÁ, D.C.");
  assert.equal(municipalityData.find((row) => row.territory_code === "11001").latitude, 4.31639);
  assert.equal(departmentData.filter((row) => row.territory_code === "05" && periods.includes(row.period)).length, 3);
  const specs = periods.map((label) => context.phaseScatterSpec(rows("department"), { label, color: "#3569b0" }));
  context.initPhaseScatterFilters(rows("department"), municipalRows, views, specs);
  await settled();
  assert.equal(nodes["#phase-scatter-filters"].disabled, false);
  assert.equal(nodes["#phase-scatter-territory-options"].children.length, 2);
  assert.equal(changes[0].at(-1).length, 2);
  assert.equal(specs[0].layer[1].transform[0].filter, "datum.selected");
  nodes["#phase-scatter-territory"].value = "Departamento 2 (2)";
  nodes["#phase-scatter-territory"].listeners.input();
  await settled();
  assert(changes.every((updates) => updates.at(-1).filter((row) => row.selected).length === 1));
  assert.match(nodes["#phase-detail-20082014"].textContent, /Departamento 2: pico en la semana 20/);
  nodes["#phase-scatter-level"].value = "municipality";
  nodes["#phase-scatter-level"].listeners.change();
  await settled();
  assert.equal(changes[0].at(-1)[0].dimension, "municipality");
  nodes["#phase-scatter-territory"].value = "Municipio 2 · Departamento 2 (2)";
  nodes["#phase-scatter-territory"].listeners.input();
  await settled();
  assert.equal(changes[0].at(-1).filter((row) => row.selected).length, 1);
  assert.equal(changes[1].at(-1).filter((row) => row.selected).length, 1);
  assert.equal(changes[2].at(-1).filter((row) => row.selected).length, 0);
  assert.equal(specs[0].data.values.filter((row) => row.selected).length, 1);
  assert.match(nodes["#phase-detail-20152019"].textContent, /semana 20/);
  assert.match(nodes["#phase-detail-20222025"].textContent, /sin pico calculable/);
  nodes["#phase-scatter-territory"].value = "";
  nodes["#phase-scatter-territory"].listeners.input();
  await settled();
  assert(changes.every((updates) => updates.at(-1).every((row) => !row.selected)));
  nodes["#phase-scatter-level"].value = "department";
  context.initPhaseScatterFilters(departmentData, municipalityData, views, specs);
  await settled();
  assert.equal(nodes["#phase-scatter-territory-options"].children.length, 32);
  nodes["#phase-scatter-territory"].value = "Antioquia (05)";
  nodes["#phase-scatter-territory"].listeners.input();
  await settled();
  assert(changes.every((updates) => updates.at(-1).filter((row) => row.selected).length === 1));
  assert.match(nodes["#phase-detail-20222025"].textContent, /Antioquia: pico en la semana/);
  console.log("Phase level and territory filters update the charts and modal specs.");
})().catch((error) => { console.error(error); process.exitCode = 1; });
