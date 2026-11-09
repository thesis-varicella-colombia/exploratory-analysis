"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
class Element {
  constructor(value = "") { this.value = value; this.children = []; this.textContent = ""; }
  append(...children) { this.children.push(...children); }
  replaceChildren() { this.children = []; }
}
const nodes = Object.fromEntries(["rt-information-table", "rt-information-width", "rt-information-status"]
  .map(id => ["#" + id, new Element(id === "rt-information-width" ? "1" : "")]));
const context = vm.createContext({
  Intl, console,
  document: { querySelector: id => nodes[id], createElement: () => new Element(), addEventListener() {} },
});
vm.runInContext(fs.readFileSync(path.join(__dirname, "../docs/comparability.js"), "utf8"), context);
context.fixture = JSON.parse(fs.readFileSync(path.join(__dirname,
  "../docs/data_processed/numero_reproductivo/rt_information/national.json"), "utf8"));
vm.runInContext("rtInformationData = fixture;", context);
for (const limit of [0.5, 1, 2]) {
  nodes["#rt-information-width"].value = String(limit);
  context.renderRtInformation();
  const rendered = nodes["#rt-information-table"].children;
  const source = context.fixture.rows.filter(row => row.width_limit === limit);
  assert.equal(rendered.length, 8);
  source.forEach((row, index) => {
    const cells = rendered[index].children;
    assert.equal(cells.length, 8);
    assert.equal(cells[0].scope, "row");
    assert.equal(cells[1].textContent, row.period.replaceAll("-", "–"));
    assert.equal(cells[6].textContent, [row.interval_above_one, row.interval_below_one,
      row.interval_includes_one].map(value => new Intl.NumberFormat("es-CO").format(value)).join(" / "));
    assert.equal(row.interval_above_one + row.interval_below_one + row.interval_includes_one,
      row.information_days);
    assert.ok(cells[7].textContent.includes(row.longest_days ? "días" : "Sin tramo"));
  });
}
assert.match(nodes["#rt-information-status"].textContent, /Colombia/);
console.log("Rt precision table: all periods, both dates, all three thresholds and interval directions verified.");
