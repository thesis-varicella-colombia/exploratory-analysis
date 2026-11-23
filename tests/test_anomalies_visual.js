"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.resolve(__dirname, "..");
const source = fs.readFileSync(path.join(root, "docs/anomalies.js"), "utf8")
  .replace(/\nloadAnomalyMatrix\(\);\s*$/, "");
const controls = {
  "#anomaly-period": { value: "2022-2025" },
  "#anomaly-dose": { value: "booster" },
  "#anomaly-pc": { value: "92.9" },
};
const context = vm.createContext({
  document: { querySelector: (selector) => controls[selector] },
  Intl,
});
vm.runInContext(source, context);

const csv = fs.readFileSync(path.join(
  root, "docs/data_processed/anomalias_cobertura/age_standardized_sir_coverage_periods.csv",
), "utf8");
const rows = context.parseAnomalyCsv(csv);
const state = context.getAnomalyState(rows);
assert.equal(state.selected.length, 1102);
assert.equal(state.eligible.length, 1102);
assert.equal(state.over100.length, 474);
assert.equal(state.missing.length, 0);
const boundaries = JSON.parse(fs.readFileSync(path.join(
  root, "docs/data_processed/cartografia/municipal_boundaries_dane.geojson",
), "utf8"));
const mapped = new Set(boundaries.features.filter((feature) =>
  feature.properties.kind === "MUNICIPIO").map((feature) => feature.properties.code));
assert.equal(state.selected.filter((row) => mapped.has(row.code)).length, 1102);

const counts = {};
for (const row of state.selected) {
  const category = context.anomalyClass(row, state);
  counts[category] = (counts[category] || 0) + 1;
}
assert.deepEqual(counts, {
  low_low: 587,
  low_high: 267,
  high_low: 158,
  high_high: 90,
});

const names = new Map();
const validSpec = context.anomalyScatterSpec(state, names, false);
const allSpec = context.anomalyScatterSpec(state, names, true);
assert.equal(validSpec.layer[2].data.values.length, 1102);
assert.equal(validSpec.layer[3].data.values.length, 1102);
assert.equal(allSpec.layer[2].data.values.length, 1102);
assert.equal(allSpec.layer[3].data.values.length, 1102);
assert.equal(allSpec.layer[3].transform[0].loess, "sir");
assert.equal(allSpec.layer[3].transform[0].on, "coverage");
assert.equal(allSpec.layer[0].data.values[0].coverage, 92.9);
assert.equal(allSpec.layer[1].data.values[0].sir, 1);
controls["#anomaly-period"].value = "2015-2019";
controls["#anomaly-dose"].value = "first_dose";
const firstDoseState = context.getAnomalyState(rows);
assert.equal(firstDoseState.eligible.length, 1102);
assert.equal(firstDoseState.over100.length, 654);
controls["#anomaly-period"].value = "2020-2021";
controls["#anomaly-dose"].value = "booster";
const pandemicState = context.getAnomalyState(rows);
assert.equal(pandemicState.eligible.length, 1102);
assert.equal(pandemicState.over100.length, 170);
controls["#anomaly-pc"].value = "";
const invalidThresholdState = context.getAnomalyState(rows);
assert.equal(context.anomalyClass(invalidThresholdState.eligible[0], invalidThresholdState),
  "unclassified");
for (const value of [92.89999999999999, 92.9, 92.90000000000001]) {
  assert.equal(context.anomalyCoverageHigh(value, 92.9), true);
}
assert.equal(context.anomalyCoverageHigh(92.89999999, 92.9), false);
const bogota = state.byCode.get("11001");
assert.equal(Number(bogota.coverage_booster_valid_years), 4);
assert.equal(context.anomalyClass(bogota, state), "low_high");
assert.equal(context.anomalyClass(state.byCode.get("08137"), state), "low_low");
console.log("Anomaly visual data and chart specification OK");
