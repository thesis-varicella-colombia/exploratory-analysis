"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.resolve(__dirname, "..");
const payload = JSON.parse(fs.readFileSync(path.join(root,
  "docs/data_processed/numero_reproductivo/municipal_priorities/web_tables.json"), "utf8"));
class Element {
  constructor() {
    this.children = []; this.textContent = ""; this.dataset = {};
    this.attributes = {}; this.listeners = {};
  }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) {
    this.children = children.flatMap(child => child.isFragment ? child.children : [child]);
  }
  setAttribute(name, value) { this.attributes[name] = value; }
  removeAttribute(name) { delete this.attributes[name]; }
  addEventListener(name, listener) { this.listeners[name] = listener; }
  closest(selector) { assert.equal(selector, "table"); return this.table; }
}
const ids = ["rt-priority-sustained-table", "rt-priority-peaks-table",
  "rt-priority-sustained-caption", "rt-priority-peaks-caption", "rt-municipal-priorities-status"];
const nodes = Object.fromEntries(ids.map(id => ["#" + id, new Element()]));
const fields = {
  sustained: ["code", "name", "department", "notification_start", "notification_days",
    "notification_peak", "symptom_start", "symptom_days", "symptom_peak"],
  peaks: ["code", "name", "department", "notification_peak_date", "notification_peak",
    "symptom_peak_date", "symptom_peak"],
};
const headers = {};
for (const group of Object.keys(fields)) {
  headers[group] = fields[group].map(field => {
    const header = new Element();
    header.textContent = field;
    return header;
  });
  nodes[`#rt-priority-${group}-table`].table = {
    querySelectorAll(selector) { assert.equal(selector, "thead th"); return headers[group]; },
  };
}
const errors = [];
let fail = false;
const context = vm.createContext({
  Intl,
  document: { querySelector: id => nodes[id], createElement: () => new Element(),
    createDocumentFragment: () => Object.assign(new Element(), { isFragment: true }), addEventListener() {} },
  fetch: async url => {
    assert.match(url, /municipal_priorities\/web_tables\.json/);
    return { ok: !fail, json: async () => payload };
  },
  console: { error: error => errors.push(error) },
});
vm.runInContext(fs.readFileSync(path.join(root, "docs/rt_municipal_priorities.js"), "utf8"), context);

(async () => {
  await context.loadRtMunicipalPriorities();
  assert.equal(errors.length, 0);
  for (const [group, columns] of [["sustained", 9], ["peaks", 7]]) {
    const rows = nodes[`#rt-priority-${group}-table`].children;
    assert.equal(rows.length, 44);
    assert.ok(rows.every(row => row.children.length === columns));
    const expected = [...payload[group]].sort((a, b) => b.symptom_peak - a.symptom_peak || a.code.localeCompare(b.code));
    assert.deepEqual(Array.from(rows, row => row.children[0].textContent), expected.map(row => row.code));
  }
  const collator = new Intl.Collator("es", { sensitivity: "base", numeric: true });
  const codes = group => nodes[`#rt-priority-${group}-table`].children.map(row => row.children[0].textContent);
  for (const group of Object.keys(fields)) {
    const other = group === "sustained" ? "peaks" : "sustained";
    const unchanged = codes(other);
    const initialHeader = headers[group].at(-1);
    assert.equal(initialHeader.attributes["aria-sort"], "descending");
    assert.equal(initialHeader.children[0].children[1].textContent, "↓");
    for (const [index, field] of fields[group].entries()) {
      const button = headers[group][index].children[0];
      assert.equal(button.type, "button");
      for (const ascending of [true, false]) {
        button.listeners.click();
        const expected = [...payload[group]].sort((a, b) => {
          let comparison = typeof a[field] === "number" ? a[field] - b[field] : collator.compare(a[field], b[field]);
          if (!comparison && field.endsWith("_start")) {
            const end = field.replace("_start", "_end");
            comparison = collator.compare(a[end], b[end]);
          }
          return (ascending ? comparison : -comparison) || collator.compare(a.code, b.code);
        });
        assert.deepEqual(codes(group), expected.map(row => row.code), `${group}: ${field}, ascending=${ascending}`);
        assert.equal(headers[group][index].attributes["aria-sort"], ascending ? "ascending" : "descending");
        assert.equal(button.children[1].textContent, ascending ? "↑" : "↓");
        assert.match(button.attributes["aria-label"], ascending ? /mayor a menor/ : /menor a mayor/);
        assert.equal(headers[group].filter(header => header.attributes["aria-sort"]).length, 1);
        assert.deepEqual(codes(other), unchanged);
      }
    }
  }
  context.renderRtMunicipalPriorities(payload);
  for (const group of Object.keys(fields)) {
    assert.ok(headers[group].every(header => header.children.length === 1 && header.children[0].children.length === 2));
    assert.equal(headers[group].at(-1).attributes["aria-sort"], "descending");
    assert.equal(headers[group][0].children[0].children[0].textContent, "code");
  }
  assert.match(nodes["#rt-municipal-priorities-status"].textContent, /15 aparecen en ambas listas \(73 municipios distintos\)/);
  const wrongCount = structuredClone(payload);
  wrongCount.peak_count++;
  assert.throws(() => context.renderRtMunicipalPriorities(wrongCount), /Recuento/);
  const duplicate = structuredClone(payload);
  duplicate.sustained[1].code = duplicate.sustained[0].code;
  assert.throws(() => context.renderRtMunicipalPriorities(duplicate), /repetido/);
  const belowThreshold = structuredClone(payload);
  belowThreshold.peaks[0].symptom_peak = 4.9;
  assert.throws(() => context.renderRtMunicipalPriorities(belowThreshold), /criterios/);
  fail = true;
  await context.loadRtMunicipalPriorities();
  assert.equal(errors.length, 1);
  assert.match(nodes["#rt-municipal-priorities-status"].textContent, /No se pudieron cargar/);
  const html = fs.readFileSync(path.join(root, "docs/index.html"), "utf8");
  assert.equal((html.match(/class="table-scroll rt-priority-scroll"/g) || []).length, 2);
  assert.match(html, /\.rt-priority-scroll\s*\{[^}]*max-height:\s*25rem;[^}]*overflow:\s*auto;/);
  assert.match(html, /municipal_priorities\/README_data\.md/);
  console.log("Municipal Rt priorities: 44 + 44 rows, all columns sortable in both directions, independent tables, accessible controls, reloads and load failures verified.");
})().catch(error => { console.error(error); process.exitCode = 1; });
