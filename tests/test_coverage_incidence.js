"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
const context = vm.createContext({Intl, document: {addEventListener() {}}});
vm.runInContext(fs.readFileSync(path.join(root, "docs/coverage_incidence.js"), "utf8"), context);
const data = JSON.parse(fs.readFileSync(path.join(root, "docs/data_processed/cobertura_vacunacion/coverage_incidence/05001.json"), "utf8"));
const labels = JSON.parse(fs.readFileSync(path.join(root,"docs/data_processed/cobertura_vacunacion/coverage_incidence/manifest.json"),"utf8")).age_groups;
const multiple = context.coverageIncidenceSelection(data, ["all","1_4"], ["first_dose","booster"], ["reference","administrative"], labels);
const unique = rows => new Set(rows.map(row=>row.id));
assert.equal(unique(multiple.filter(row=>row.kind==="incidence")).size,2);
assert.equal(unique(multiple.filter(row=>row.kind==="coverage")).size,4);
assert.equal(multiple.filter(row=>row.kind==="coverage").length,72);
assert.equal(multiple.filter(row=>row.kind==="incidence").length,36);
const noAges = context.coverageIncidenceSelection(data, [], ["first_dose","booster"], ["reference","administrative"], labels);
assert.equal(noAges.length,72);
assert.deepEqual(noAges.map(x=>x.value),multiple.filter(x=>x.kind==="coverage").map(x=>x.value));
assert.equal(context.coverageIncidenceSelection(data, ["all"], [], ["reference"], labels).length,18);
assert.equal(context.coverageIncidenceSelection(data, ["all"], ["booster"], [], labels).length,18);
assert.equal(context.coverageIncidenceSelection(data, [], [], [], labels).length,0);
const onlyBooster = context.coverageIncidenceSelection(data, ["5_14"], ["booster"], ["reference"], labels);
assert.equal(Math.min(...onlyBooster.map(row=>row.year)),2008);
assert.equal(Math.max(...onlyBooster.map(row=>row.year)),2025);
assert.ok(onlyBooster.filter(row=>row.kind==="coverage"&&row.year<2019).every(row=>row.value===null));
assert.ok(onlyBooster.some(row=>row.kind==="incidence"&&row.year===2008&&row.value!==null));
assert.equal(onlyBooster.find(row=>row.kind==="coverage"&&row.year===2019).value,null);
const aggregate = JSON.parse(fs.readFileSync(path.join(root,"docs/data_processed/cobertura_vacunacion/coverage_incidence/all.json"),"utf8"));
const grouped = context.coverageIncidenceSelection(aggregate,["all"],["booster"],["administrative"],labels);
assert.equal(grouped.filter(row=>row.kind==="incidence").length,18);
assert.ok(grouped.some(row=>row.kind==="coverage"&&row.year===2025&&row.entities>1000));
assert.ok(grouped.filter(row=>row.kind==="coverage").every(row=>row.label.includes("ponderada por metas PAI")));
const axes = context.coverageIncidenceSpec(900).axes;
assert.equal(axes.find(axis=>axis.scale==="incidenceY").orient,"left");
assert.equal(axes.find(axis=>axis.scale==="coverageY").orient,"right");
const doseDetail = grouped.find(row=>row.kind==="coverage"&&row.year===2025);
assert.equal(doseDetail.reference_age,"5 años");
assert.ok(doseDetail.doses>0);
assert.ok(doseDetail.reference_population>0);
assert.ok(doseDetail.pai_target_population>0);
const referenceAggregate = context.coverageIncidenceSelection(aggregate,["1_4"],["booster"],["reference"],labels);
const refDetail = referenceAggregate.find(row=>row.kind==="coverage"&&row.year===2025);
assert.ok(Math.abs(refDetail.value-100*refDetail.doses/refDetail.reference_population)<1e-7);
const incidenceDetail = referenceAggregate.find(row=>row.kind==="incidence"&&row.year===2025);
assert.equal(incidenceDetail.age_label,labels["1_4"]);
assert.equal(incidenceDetail.population,aggregate.population["1_4"].at(-1));
console.log("Coverage/incidence: multiple checkbox selections, unique coverage series, hidden categories, missingness and existing lag OK.");
const survivorSeries=context.coverageIncidenceSelection(data,[],["first_dose","booster"],["survivors"],labels);
assert.equal(survivorSeries.length,18);
assert.ok(survivorSeries.every(row=>row.id==="coverage/first_dose/survivors"));
const survivorDetail=survivorSeries.find(row=>row.year===2016);
assert.equal(survivorDetail.survivor_population,28968);
assert.ok(Math.abs(survivorDetail.value-100*survivorDetail.doses/survivorDetail.survivor_population)<1e-8);
const survivorAggregate=context.coverageIncidenceSelection(aggregate,[],["first_dose"],["survivors"],labels);
for(const row of survivorAggregate.filter(row=>row.value!==null)) {
  assert.ok(row.entities>1000);
  assert.ok(Math.abs(row.value-100*row.doses/row.survivor_population)<1e-8);
}

// Empirical-Bayes smoothed incidence option.
const small=JSON.parse(fs.readFileSync(path.join(root,"docs/data_processed/cobertura_vacunacion/coverage_incidence/05021.json"),"utf8"));
const crudeSel=context.coverageIncidenceSelection(small,["1_4"],[],[],labels,"crude");
const ebSel=context.coverageIncidenceSelection(small,["1_4"],[],[],labels,"eb");
assert.equal(crudeSel.length,18);
assert.equal(ebSel.length,18);
assert.ok(ebSel.every(row=>row.id==="incidence/1_4/eb"));
assert.ok(crudeSel.every(row=>row.id==="incidence/1_4/crude"));
assert.ok(ebSel.every(row=>row.rate_kind==="Suavizada EB (nacional)"));
assert.ok(ebSel.every(row=>row.label.includes("(EB)")));
// EB value equals the series' incidence_eb; crude field is preserved for the tooltip.
const ebRow=ebSel.find(row=>row.year===2024), crudeRow=crudeSel.find(row=>row.year===2024);
assert.equal(ebRow.value,small.incidence_eb["1_4"][small.years.indexOf(2024)]);
assert.equal(ebRow.crude,crudeRow.value);
assert.notEqual(ebRow.value,crudeRow.value);          // shrinkage moved the small municipality
// Local EB: third option, reads incidence_eb_local and differs from the national EB.
const localSel=context.coverageIncidenceSelection(small,["5_14"],[],[],labels,"eb_local");
assert.equal(localSel.length,18);
assert.ok(localSel.every(row=>row.id==="incidence/5_14/eb_local"));
assert.ok(localSel.every(row=>row.rate_kind==="Suavizada EB (vecinos)"));
assert.ok(localSel.every(row=>row.label.includes("EB vecinos")));
const localRow=localSel.find(row=>row.year===2024);
assert.equal(localRow.value,small.incidence_eb_local["5_14"][small.years.indexOf(2024)]);
const ebGlobal514=context.coverageIncidenceSelection(small,["5_14"],[],[],labels,"eb").find(row=>row.year===2024);
assert.notEqual(localRow.value,ebGlobal514.value);    // local and national differ for this municipality
// National aggregate: both EB variants equal the pooled crude rate.
const crudeAgg=context.coverageIncidenceSelection(aggregate,["all"],[],[],labels,"crude");
for (const mode of ["eb","eb_local"]) {
  const agg=context.coverageIncidenceSelection(aggregate,["all"],[],[],labels,mode);
  assert.deepEqual(agg.map(r=>r.value),crudeAgg.map(r=>r.value));
}
console.log("Coverage/incidence: Empirical-Bayes smoothed incidence options (national and neighbours) OK.");
