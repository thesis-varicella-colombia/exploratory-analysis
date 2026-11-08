"use strict";
const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm"),path=require("node:path");
const root=path.resolve(__dirname,"..");
const context=vm.createContext({});
vm.runInContext(fs.readFileSync(path.join(root,"docs/annual_territories.js"),"utf8"),context);
const directory=path.join(root,"docs/data_processed/varicela_totales_por_anio");
const manifest=JSON.parse(fs.readFileSync(path.join(directory,"manifest.json"),"utf8"));
assert.equal(context.annualTerritoryMatch(manifest.all_label,manifest).id,"all");
assert.equal(context.annualTerritoryMatch("05",manifest).id,"dep_05");
assert.equal(context.annualTerritoryMatch("05001",manifest).id,"05001");
assert.equal(context.annualTerritoryMatch("medellin",manifest).id,"05001");
assert.equal(context.annualTerritoryMatch("Departamento · ANTIOQUIA · 05",manifest).id,"dep_05");
assert.equal(context.annualTerritoryMatch("no existe",manifest),null);
const municipality=JSON.parse(fs.readFileSync(path.join(directory,"05001.json"),"utf8"));
const rows=context.annualTerritoryPayload(municipality,"05001","Medellín");
assert.equal(rows.length,19);assert.equal(rows[0].year,2007);assert.equal(rows.at(-1).year,2025);
assert.ok(rows.every(row=>row.official_2007_cases===null));
assert.ok(rows.every(row=>row.territory_label==="Medellín"));
const invalid=JSON.parse(JSON.stringify(municipality));invalid.rows[0].official_2007_cases=69695;
assert.throws(()=>context.annualTerritoryPayload(invalid,"05001","Medellín"),/solo corresponde a Colombia/);
const missing=JSON.parse(fs.readFileSync(path.join(directory,"27493.json"),"utf8"));
assert.equal(context.annualTerritoryPayload(missing,"27493","Bajirá").find(row=>row.year===2009).notification_rate_per_100k,null);
console.log("Annual territory selection: national/department/municipality search, dates, official reference scope and missing denominators OK.");

async function testFilterWithoutSelectionNote(){
  const html=fs.readFileSync(path.join(root,"docs/index.html"),"utf8");
  const elements=new Map([...html.matchAll(/\bid="([^"]+)"/g)].map(match=>[`#${match[1]}`,{
    textContent:"",value:"",listeners:{},append(){},setAttribute(){},
    addEventListener(event,handler){this.listeners[event]=handler;},
  }]));
  assert.equal(elements.has("#annual-territory-selection"),false);
  assert.equal(elements.has("#annual-table"),false);
  assert.equal(elements.has("#annual-table-caption"),false);
  const errors=[],views=[0,1].map(()=>({
    change(name,changes){this.rows=changes.rows;return this;},async runAsync(){},
  }));
  const browser=vm.createContext({
    document:{querySelector:selector=>elements.get(selector)??null,createElement:()=>({})},
    fetch:async url=>({ok:true,json:async()=>JSON.parse(fs.readFileSync(path.join(root,"docs",url.split("?")[0]),"utf8"))}),
    vega:{changeset:()=>({remove(){return this;},insert(rows){this.rows=rows;return this;}})},
    console:{error:error=>errors.push(error)},
  });
  vm.runInContext(fs.readFileSync(path.join(root,"docs/annual_territories.js"),"utf8"),browser);
  await browser.initAnnualTerritoryFilter(views);
  assert.equal(errors.length,0);
  assert.match(elements.get("#annual-territory-status").textContent,/2007–2025/);
  const input=elements.get("#annual-territory-search");
  input.value="05001";
  await input.listeners.input();
  assert.equal(errors.length,0);
  assert.ok(views.every(view=>view.rows.length===19));
  assert.equal(elements.get("#annual-official-legend").hidden,true);
  console.log("Annual territory filter: initialization and municipality change without removed selection note OK.");
}
testFilterWithoutSelectionNote().catch(error=>{console.error(error);process.exitCode=1;});
