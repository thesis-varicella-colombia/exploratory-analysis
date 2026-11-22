"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
function control(value=""){
  return {value, listeners:{}, attributes:{}, textContent:"",
    addEventListener(name,handler){this.listeners[name]=handler;},
    setAttribute(name,value){this.attributes[name]=value;}};
}
const nodes=Object.fromEntries(["play","speed","timeline","frame","status"].map(name=>[`#vaccine-comparison-${name}`,control(name==="speed"?"1":"")]));
const year=control("2025"),dose=control("first_dose"),metric=control("reference");
const setYears=start=>{year.options=Array.from({length:2026-start},(_,i)=>({value:String(2025-i)}));};
setYears(2016);
const timers=new Map(),documentEvents={},windowEvents={};let next=0,renders=0;
const context=vm.createContext({Intl,document:{hidden:false,querySelector:id=>nodes[id],addEventListener:(name,handler)=>{documentEvents[name]=handler;}},
  window:{setTimeout:(handler,delay)=>{timers.set(++next,{handler,delay});return next;},clearTimeout:id=>timers.delete(id),addEventListener:(name,handler)=>{windowEvents[name]=handler;}}});
vm.runInContext(fs.readFileSync(path.join(__dirname,"../docs/vaccine_coverage_comparison.js"),"utf8"),context);
context.initVaccineComparisonPlayer(year,dose,metric,()=>renders++);
function tick(){assert.equal(timers.size,1);const [id,timer]=[...timers][0];timers.delete(id);timer.handler();}
function click(){nodes["#vaccine-comparison-play"].listeners.click();}
assert.equal(nodes["#vaccine-comparison-timeline"].min,"2016");
click();assert.equal([...timers.values()][0].delay,1500);
assert.equal(nodes["#vaccine-comparison-play"].attributes["aria-pressed"],"true");
assert.equal(nodes["#vaccine-comparison-status"].attributes["aria-live"],"off");
tick();assert.equal(year.value,"2016");tick();assert.equal(year.value,"2017");
assert.equal(nodes["#vaccine-comparison-frame"].textContent,"Año: 2017");
for(const [speed,delay] of [["0.5",3000],["2",750],["1",1500]]){
  nodes["#vaccine-comparison-speed"].value=speed;nodes["#vaccine-comparison-speed"].listeners.change();
  assert.equal(timers.size,1);assert.equal([...timers.values()][0].delay,delay);
}
click();assert.equal(timers.size,0);assert.equal(nodes["#vaccine-comparison-status"].attributes["aria-live"],"polite");
click();nodes["#vaccine-comparison-timeline"].value="2022";nodes["#vaccine-comparison-timeline"].listeners.input();
assert.equal(year.value,"2022");assert.equal(timers.size,0);
click();year.value="2016";year.listeners.change();assert.equal(timers.size,0);
click();dose.value="booster";setYears(2019);year.value="2019";dose.listeners.change();
assert.equal(timers.size,0);assert.equal(nodes["#vaccine-comparison-timeline"].min,"2019");
click();tick();assert.equal(year.value,"2020");year.value="2025";tick();assert.equal(year.value,"2019");
metric.value="administrative";metric.listeners.change();assert.equal(timers.size,0);
click();context.document.hidden=true;documentEvents.visibilitychange();assert.equal(timers.size,0);
context.document.hidden=false;click();windowEvents.pagehide();assert.equal(timers.size,0);
assert.equal(nodes["#vaccine-comparison-play"].attributes["aria-pressed"],"false");assert.equal(renders,5);
console.log("Vaccination animation: ascending years, wrap, dose range, 0.5x/1x/2x, pause, scrubbing and cleanup OK");
