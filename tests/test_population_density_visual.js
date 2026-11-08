"use strict";
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
function control(value=''){return {value,listeners:{},attributes:{},addEventListener(name,handler){this.listeners[name]=handler;},setAttribute(name,value){this.attributes[name]=value;}};}
const nodes=Object.fromEntries(['play','speed','timeline','frame','status'].map(name=>['#population-density-'+name,control(name==='speed'?'1':'')]));
const year=control('2025');year.options=Array.from({length:19},(_,i)=>({value:String(2025-i)}));
const timers=new Map(),events={},windowEvents={};let id=0,renders=0,resolveRender=null;
const context=vm.createContext({Intl,document:{hidden:false,querySelector:id=>nodes[id],addEventListener:(name,handler)=>{events[name]=handler;}},window:{setTimeout:(handler,delay)=>{timers.set(++id,{handler,delay});return id;},clearTimeout:id=>timers.delete(id),addEventListener:(name,handler)=>{windowEvents[name]=handler;}}});
vm.runInContext(fs.readFileSync(path.join(__dirname,'../docs/population_density.js'),'utf8'),context);
const records=[{year:2025,status:'available',density_per_km2:10,cases:0},{year:2025,status:'missing_or_nonpositive_population',density_per_km2:null,cases:10}];
assert.equal(context.populationDensityRows(records,2025).length,1);
const spec=context.populationDensitySpec(records.slice(0,1),'cases');
assert.equal(spec.data.name,'municipal_density');assert.equal(spec.encoding.x.scale.type,'log');assert.equal(spec.encoding.y.scale.type,'sqrt');
assert.equal(spec.data.values[0].cases,0);assert.equal(spec.encoding.y.scale.zero,true);
assert.equal(context.populationDensitySpec(records,'incidence_per_100k').encoding.y.field,'incidence_per_100k');
context.initPopulationDensityPlayer(year,async()=>{renders++;if(resolveRender==='pending')await new Promise(resolve=>{resolveRender=resolve;});});
const click=()=>nodes['#population-density-play'].listeners.click();
async function advance(){assert.equal(timers.size,1);const [key,timer]=[...timers][0];timers.delete(key);await timer.handler();}
(async()=>{
click();assert.equal([...timers.values()][0].delay,1500);await advance();assert.equal(year.value,'2008');await advance();assert.equal(year.value,'2009');
for(const [speed,delay] of [['0.5',3000],['2',750]]){nodes['#population-density-speed'].value=speed;nodes['#population-density-speed'].listeners.change();assert.equal(timers.size,1);assert.equal([...timers.values()][0].delay,delay);}
nodes['#population-density-timeline'].value='2007';nodes['#population-density-timeline'].listeners.input();assert.equal(year.value,'2007');assert.equal(timers.size,0);
click();await advance();assert.equal(year.value,'2008');
year.value='2020';year.listeners.change();assert.equal(timers.size,0);
click();resolveRender='pending';const pending=advance();assert.equal(timers.size,0);click();resolveRender();await pending;assert.equal(timers.size,0);
resolveRender=null;click();context.document.hidden=true;events.visibilitychange();assert.equal(timers.size,0);
context.document.hidden=false;click();windowEvents.pagehide();assert.equal(timers.size,0);assert.equal(nodes['#population-density-play'].attributes['aria-pressed'],'false');
assert.equal(renders,5);console.log('Density scatter fields, zero cases, ascending animation, speeds, diagnostic-year exclusion, async pause and cleanup OK');
})().catch(error=>{console.error(error);process.exitCode=1;});
