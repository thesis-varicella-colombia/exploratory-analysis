"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.resolve(__dirname, "..");
class Element {
  constructor() { this.value = ""; this.children = []; this.listeners = {}; this.attributes = {}; this.textContent = ""; this.dataset = {}; this.classList = {toggle() {}}; }
  append(child) { this.children.push(child); }
  after(child) { nodes[`#${child.id}`] = child; }
  replaceChildren(...children) { this.children = children; this.textContent = ""; }
  removeAttribute(key) { delete this.attributes[key]; }
  select() {}
  blur() { this.listeners.blur?.(); }
  scrollIntoView() {}
  querySelectorAll() { return this.children.filter(child => child.attributes.role === "option"); }
  setAttribute(key, value) { this.attributes[key] = value; }
  addEventListener(event, callback) { this.listeners[event] = callback; }
}
const ids = ["rt-filters", "rt-dimension", "rt-department", "rt-municipality", "rt-municipality-options", "rt-full-scale", "rt-filter-status",
  "rt-territory-control", "rt-notification-title", "rt-symptom-title", "chart-rt-national", "chart-rt-onset", "chart-rt-onset-detail"];
const nodes = Object.fromEntries(ids.map(id => [`#${id}`, new Element()]));
nodes["#rt-dimension"].value = "national";
const rendered = new Map();
const requests = [];
const instances = new Map();
const updateCounts = new Map();
const liveSpecs = new Map();
let staleRelease;
const context = vm.createContext({
  console, Intl, Response, Blob, DecompressionStream, TextDecoder, Uint8Array,
  NUMBER: new Intl.NumberFormat("es-CO"), SCHEMA: "", CHART_WIDTH: 900, PANDEMIC_COLOR: "gray", EVENT_COLOR: "gray",
  document: { querySelector: id => nodes[id], createElement: () => new Element() },
  fetch: async (url) => {
    const file = url.split("?")[0];
    requests.push(file);
    if (staleRelease && file.includes("department_11")) await new Promise(resolve => staleRelease.push(resolve));
    return new Response(fs.readFileSync(path.join(root, "docs", file)));
  },
  renderChart: async (id, title, spec, options) => {
    instances.set(id, (instances.get(id) || 0) + 1);
    liveSpecs.set(id, spec);
    rendered.set(id, options.modalSpec());
    return {
      signal(name, value) { this[name] = value; return this; },
      data(name, values) { assert.equal(name, "rt_series"); this.values = values; return this; },
      async runAsync() {
        rendered.set(id, options.modalSpec());
        assert.equal(options.modalTitle(), rendered.get(id).title);
        assert.equal(this.rt_title, rendered.get(id).title);
        if (this.values) assert.equal(this.values, rendered.get(id).data.values);
        updateCounts.set(id, (updateCounts.get(id) || 0) + 1);
      },
      finalize() { throw new Error("Filtering must reuse the chart instance"); },
    };
  },
  loadRtChart: async () => {throw new Error("Unexpected national fallback");},
  loadOnsetRtChart: async () => {throw new Error("Unexpected onset fallback");},
});
const charts = fs.readFileSync(path.join(root, "docs/charts.js"), "utf8");
vm.runInContext(charts.slice(charts.indexOf("function rtSpec("), charts.indexOf("function parseRtDailyRows(")), context);
const source = fs.readFileSync(path.join(root, "docs/rt_filters.js"), "utf8").replace(/\ninitRtFilters\(\);\s*$/, "");
vm.runInContext(source, context);

(async () => {
  await context.initRtFilters();
  assert.equal(nodes["#rt-filters"].disabled, false);
  assert.equal(nodes["#rt-department"].children.length, 33);
  assert.equal(nodes["#rt-department"].children[0].value, "department_88");
  assert.equal(nodes["#rt-department"].children.at(-1).value, "department_91");
  assert.equal(rendered.size, 3);
  assert.equal(nodes["#rt-notification-title"].textContent, "Rₜ nacional por fecha de notificación");
  assert.equal(rendered.get("#chart-rt-onset").encoding.y.scale.domain[1], 2);
  const baseline = rendered.get("#chart-rt-national").data.values;
  assert(baseline.length < 6580);
  assert(baseline.some(row => row.days > 1));
  assert.equal(rendered.get("#chart-rt-onset-detail").data.values.length, 455);
  assert(rendered.get("#chart-rt-onset-detail").data.values.every(row => row.days === 1));
  const gap = baseline.findIndex(row => row.year === 2008 && row.week === 52);
  assert(baseline[gap].segment === null);
  const before = baseline.slice(0, gap).filter(row => row.rt !== null).at(-1);
  const after = baseline.slice(gap).find(row => row.rt !== null);
  assert.notEqual(before.segment, after.segment);

  assert.equal(nodes["#rt-territory-control"].hidden, true);

  nodes["#rt-dimension"].value = "territory";
  nodes["#rt-department"].value = "department_05";
  await nodes["#rt-department"].listeners.change();
  assert.equal(nodes["#rt-municipality"].value, "Todo el departamento");
  nodes["#rt-municipality"].listeners.focus();
  assert(nodes["#rt-municipality-options"].children.some(option => option.dataset.id === "municipality_05001"));
  assert(!nodes["#rt-municipality-options"].children.some(option => option.dataset.id === "municipality_11001"));
  assert(rendered.get("#chart-rt-national").title.includes("ANTIOQUIA"));
  nodes["#rt-municipality"].value = "medellin";
  nodes["#rt-municipality"].listeners.input();
  assert.equal(nodes["#rt-municipality-options"].children.length, 1);
  await nodes["#rt-municipality"].listeners.keydown({key: "Enter", preventDefault() {}});
  assert.equal(nodes["#rt-municipality-options"].hidden, true);
  assert(rendered.get("#chart-rt-national").title.includes("MEDELLÍN"));
  assert(rendered.get("#chart-rt-onset").title.includes("MEDELLÍN"));
  const search = nodes["#rt-municipality"];
  const list = nodes["#rt-municipality-options"];
  search.listeners.focus();
  search.value = "05001";
  search.listeners.input();
  assert.equal(list.children[0].dataset.id, "municipality_05001");
  search.listeners.keydown({key: "ArrowDown", preventDefault() {}});
  assert.equal(search.attributes["aria-activedescendant"], "rt-choice-municipality_05001");
  search.listeners.keydown({key: "Escape", preventDefault() {}});
  assert(search.value.includes("MEDELLÍN"));
  assert.equal(list.hidden, true);
  search.listeners.focus();
  search.value = "no existe este municipio";
  search.listeners.input();
  assert.equal(list.children[0].textContent, "Sin coincidencias");
  search.listeners.blur();
  assert(search.value.includes("MEDELLÍN"));
  assert.equal(search.attributes["aria-expanded"], "false");
  const requestCount = requests.length;
  nodes["#rt-full-scale"].checked = true;
  await nodes["#rt-full-scale"].listeners.change();
  assert.equal(requests.length, requestCount);
  assert.equal(rendered.get("#chart-rt-onset").encoding.y.scale.domain, undefined);
  assert.equal(liveSpecs.get("#chart-rt-onset").data.name, "rt_series");
  assert.equal(liveSpecs.get("#chart-rt-onset").encoding.y.scale.domainRaw.expr, "rt_full_scale ? null : [0, 2]");
  assert([...instances.values()].every(count => count === 1));

  // A slower department request must never overwrite a newer selection.
  staleRelease = [];
  nodes["#rt-department"].value = "department_11";
  const oldRequest = nodes["#rt-department"].listeners.change();
  nodes["#rt-department"].value = "department_05";
  await nodes["#rt-department"].listeners.change();
  for (const resolve of staleRelease) resolve();
  await oldRequest;
  staleRelease = null;
  assert(rendered.get("#chart-rt-national").title.includes("ANTIOQUIA"));
  assert(!rendered.get("#chart-rt-national").title.includes("BOGOTÁ"));

  const manifest = JSON.parse(fs.readFileSync(path.join(root, "docs/data_processed/numero_reproductivo/rt_stratified/manifest.json"), "utf8"));
  const empty = manifest.series.find(row => row.dimension === "municipality" && row.notification.estimated_days === 0);
  nodes["#rt-department"].value = `department_${empty.department}`;
  await nodes["#rt-department"].listeners.change();
  nodes["#rt-municipality"].value = empty.code;
  nodes["#rt-municipality"].listeners.input();
  const choice = nodes["#rt-municipality-options"].children.find(option => option.dataset.id === empty.id);
  await nodes["#rt-municipality-options"].listeners.pointerdown({target: {closest: () => choice}, preventDefault() {}});
  assert(nodes["#chart-rt-national-empty"].textContent.includes("No hay estimaciones"));
  nodes["#rt-dimension"].value = "national";
  await nodes["#rt-dimension"].listeners.change();
  assert(rendered.get("#chart-rt-national").title.includes("Colombia"));
  assert.equal(nodes["#chart-rt-national"].hidden, false);
  assert.equal(nodes["#chart-rt-national-empty"].hidden, true);
  assert.equal([...instances.values()].reduce((sum, count) => sum + count, 0), 3);
  assert(updateCounts.get("#chart-rt-national") > 3);

  assert(!requests.some(file => /\/age_[^/]+\.json\.gz/.test(file)));

  // Already-decompressed hosting responses work as well as .json.gz files.
  const calendar = {date: ["2020-01-01"], year: [2020], week: [1], missing_week: [false]};
  const data = {count: [2], window_cases: [null], rt: [null], rt_lower_95: [null], rt_upper_95: [null]};
  const rows = await context.readRtStratum(new Response(JSON.stringify(data)), calendar, "cases");
  assert.equal(rows[0].cases, 2);
  await assert.rejects(() => context.readRtStratum(new Response(JSON.stringify({...data, rt: [-1]})), calendar, "cases"));
  const missing = {...calendar, missing_week: [true]};
  await assert.rejects(() => context.readRtStratum(new Response(JSON.stringify(data)), missing, "cases"));
  console.log("Rt filters verified: real compressed data, both dates and detail, national/territory selection without age requests, municipality dependency, full scale, cache, gaps, validation and stale requests.");
})().catch(error => { console.error(error); process.exitCode = 1; });
