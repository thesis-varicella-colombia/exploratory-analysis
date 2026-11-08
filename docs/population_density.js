"use strict";

const POPULATION_DENSITY_URL="data_processed/varicela_totales_por_anio/population_density_2007_2025.csv?v=20261107";
const densityMeasures={cases:{title:"Casos notificados",axis:"Casos notificados (raíz cuadrada)",format:",.0f"},
  incidence_per_100k:{title:"Incidencia notificada",axis:"Incidencia por 100.000 habitantes (raíz cuadrada)",format:",.2f"}};

function parsePopulationDensityCsv(text){
  const rows=vega.read(text,{type:"csv"});
  const seen=new Set();
  for(const row of rows){
    for(const field of ["year","area_km2","population","cases","density_per_km2","incidence_per_100k"]){
      row[field]=row[field]===""?null:Number(row[field]);
      if(row[field]!==null&&(!Number.isFinite(row[field])||row[field]<0))throw new Error("Valor inválido de densidad poblacional");
    }
    if(row.notification_record_present!=="True"&&row.notification_record_present!=="False")throw new Error("Indicador de registro de notificación inválido");
    row.notification_record_present=row.notification_record_present==="True";
    const key=`${row.code}/${row.year}`;
    if(!/^\d{5}$/.test(row.code)||seen.has(key))throw new Error("Clave municipal inválida o duplicada");
    seen.add(key);
  }
  return rows;
}

function populationDensityRows(rows,year){
  return rows.filter(row=>row.year===Number(year)&&row.status==="available"&&row.density_per_km2>0);
}

function populationDensityDomains(rows){
  const valid=rows.filter(row=>row.status==="available"&&row.density_per_km2>0);
  return {x:[Math.min(...valid.map(row=>row.density_per_km2)),Math.max(...valid.map(row=>row.density_per_km2))],
    cases:[0,Math.max(...valid.map(row=>row.cases))],incidence_per_100k:[0,Math.max(...valid.map(row=>row.incidence_per_100k))]};
}

function populationDensitySpec(rows,field,domains=null){
  if(!densityMeasures[field])throw new Error("Medida de densidad inválida");
  return {$schema:"https://vega.github.io/schema/vega-lite/v6.json",width:"container",height:340,
    autosize:{type:"fit",contains:"padding"},data:{name:"municipal_density",values:rows},
    mark:{type:"circle",size:45,opacity:.55,color:field==="cases"?"#197f7a":"#7541a4",clip:true},
    encoding:{
      x:{field:"density_per_km2",type:"quantitative",title:"Densidad poblacional (habitantes/km²; escala logarítmica)",
        scale:{type:"log",zero:false,...(domains?{domain:domains.x}:{})},axis:{format:",~g",tickCount:6}},
      y:{field,type:"quantitative",title:densityMeasures[field].axis,scale:{type:"sqrt",zero:true,...(domains?{domain:domains[field]}:{})},axis:{format:",.0f",tickCount:6}},
      tooltip:[{field:"name",type:"nominal",title:"Municipio o entidad"},{field:"code",type:"nominal",title:"DIVIPOLA"},
        {field:"department",type:"nominal",title:"Departamento"},{field:"kind",type:"nominal",title:"Tipo de entidad"},
        {field:"year",type:"ordinal",title:"Año"},{field:"population",type:"quantitative",title:"Población",format:",.0f"},
        {field:"area_km2",type:"quantitative",title:"Área (km²)",format:",.2f"},
        {field:"density_per_km2",type:"quantitative",title:"Habitantes/km²",format:",.2f"},
        {field:"cases",type:"quantitative",title:"Casos notificados",format:",.0f"},
        {field:"incidence_per_100k",type:"quantitative",title:"Incidencia por 100.000",format:",.2f"}]},
    config:{background:"transparent",view:{stroke:null},axis:{labelFont:"system-ui",titleFont:"system-ui",titlePadding:12,labelFontSize:11,titleFontSize:12}}};
}

function initPopulationDensityPlayer(yearInput,refresh){
  const play=document.querySelector("#population-density-play"),speed=document.querySelector("#population-density-speed");
  const timeline=document.querySelector("#population-density-timeline"),frame=document.querySelector("#population-density-frame");
  const status=document.querySelector("#population-density-status");
  const years=Array.from(yearInput.options,option=>Number(option.value)).filter(year=>year>=2008).sort((a,b)=>a-b);
  timeline.min=String(Math.min(...Array.from(yearInput.options,option=>Number(option.value))));timeline.max=String(years[years.length-1]);
  let timer=null,playing=false,generation=0;
  function sync(){timeline.value=yearInput.value;frame.textContent=`Año: ${yearInput.value}`;}
  function stop(){
    playing=false;generation+=1;if(timer!==null)window.clearTimeout(timer);timer=null;
    play.textContent="▶ Reproducir";play.setAttribute("aria-pressed","false");status.setAttribute("aria-live","polite");
  }
  function schedule(token){
    timer=window.setTimeout(async()=>{
      timer=null;if(token!==generation||!playing)return;
      const index=years.indexOf(Number(yearInput.value));yearInput.value=String(years[(index+1)%years.length]);
      sync();await refresh();if(token===generation&&playing)schedule(token);
    },1500/Number(speed.value));
  }
  function start(){stop();playing=true;play.textContent="⏸ Pausar";play.setAttribute("aria-pressed","true");status.setAttribute("aria-live","off");schedule(generation);}
  play.addEventListener("click",()=>playing?stop():start());
  speed.addEventListener("change",()=>{if(playing)start();});
  yearInput.addEventListener("change",()=>{stop();sync();});
  timeline.addEventListener("input",()=>{stop();yearInput.value=timeline.value;sync();refresh();});
  document.addEventListener("visibilitychange",()=>{if(document.hidden)stop();});
  window.addEventListener("pagehide",stop);sync();
}

async function initPopulationDensity(){
  const yearInput=document.querySelector("#population-density-year");
  const status=document.querySelector("#population-density-status");
  try{
    const response=await fetch(POPULATION_DENSITY_URL);
    if(!response.ok)throw new Error("No se pudieron cargar los datos municipales");
    const rows=parsePopulationDensityCsv(await response.text());
    const years=[...new Set(rows.map(row=>row.year))].sort((a,b)=>b-a);
    for(const year of years){const option=document.createElement("option");option.value=String(year);option.textContent=year===2007?"2007 (solo diagnóstico)":String(year);yearInput.append(option);}
    yearInput.value=String(years[0]);
    const selected=()=>populationDensityRows(rows,yearInput.value);
    const domains=populationDensityDomains(rows);
    const entries=[["#chart-density-cases","cases"],["#chart-density-incidence","incidence_per_100k"]];
    const views=await Promise.all(entries.map(([id,field])=>renderChart(id,densityMeasures[field].title+" frente a densidad poblacional",populationDensitySpec(selected(),field,domains),
      {annualContext:false,modalSpec:()=>populationDensitySpec(selected(),field,domains),modalTitle:()=>`${densityMeasures[field].title} frente a densidad poblacional · ${yearInput.value}`})));
    function caption(year){
      const all=rows.filter(row=>row.year===year),visible=populationDensityRows(rows,year);
      status.textContent=`${year}: ${visible.length.toLocaleString("es-CO")} de ${all.length.toLocaleString("es-CO")} entidades representadas; `+
        `${(all.length-visible.length).toLocaleString("es-CO")} sin población o área válida. `+
        (year===2007?"2007 se conserva solo como diagnóstico por la discrepancia de notificaciones documentada arriba.":"Cada punto corresponde a una entidad; se conservan los casos e incidencias de cero.");
      for(const [id,field] of entries)document.querySelector(id).setAttribute("aria-label",`${densityMeasures[field].title} frente a densidad poblacional municipal, ${year}`);
    }
    let revision=0,active=null;
    function refresh(){
      revision+=1;if(active)return active;yearInput.setAttribute("aria-busy","true");
      active=(async()=>{
      try{
        while(true){
          const current=revision,year=Number(yearInput.value),values=populationDensityRows(rows,year);
          await Promise.all(views.map(view=>view.change("municipal_density",vega.changeset().remove(()=>true).insert(values)).runAsync()));
          if(current===revision){caption(year);break;}
        }
      }catch(error){status.textContent=`No se pudieron actualizar las gráficas: ${error.message}`;console.error(error);}
      finally{active=null;yearInput.setAttribute("aria-busy","false");}
      })();
      return active;
    }
    yearInput.addEventListener("change",refresh);initPopulationDensityPlayer(yearInput,refresh);
    yearInput.disabled=false;document.querySelector("#population-density-controls").disabled=false;caption(Number(yearInput.value));
  }catch(error){status.textContent=`No se pudieron mostrar las gráficas de densidad: ${error.message}`;
    console.error(error);}
}

document.addEventListener("DOMContentLoaded",initPopulationDensity);
