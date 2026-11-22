"use strict";

const VACCINE_COMPARISON_URL = "data_processed/cobertura_vacunacion/vaccine_coverage_comparison.csv?v=20261105-survivors-label";
const VACCINE_COMPARISON_GEOMETRY = "data_processed/cartografia/municipal_boundaries_dane.geojson";
const VACCINE_COMPARISON_COLORS = ["#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#08519c", "#08306b"];
const VACCINE_COMPARISON_MISSING = "#c9cfd3";
const vaccineComparisonDecimal = new Intl.NumberFormat("es-CO", {maximumFractionDigits:2});
const vaccineComparisonMetrics = {
  administrative: {field:"administrative_coverage_pct",label:"Cobertura administrativa publicada",status:"administrative_status"},
  survivors: {field:"survivor_coverage_pct",label:"Cobertura Sobrevivientes",status:"survivor_status"},
  reference: {field:"reference_coverage_pct",label:"Dosis / población de referencia",status:"reference_status"},
};
const vaccineComparisonDoses = {first_dose:"Primera dosis",booster:"Segunda dosis / refuerzo"};
const vaccineComparisonMissing = {
  not_applicable_before_2019:"Refuerzo no disponible antes de 2019",
  missing_source_record:"Sin registro PAI para esta entidad y año",
  missing_admin_percentage:"Sin porcentaje administrativo publicado",
  invalid_admin_percentage:"Porcentaje administrativo inválido",
  missing_admin_target_for_merge:"Sin metas PAI suficientes para homologar el porcentaje",
  missing_or_invalid_doses:"Sin cantidad de dosis válida",
  not_applicable_to_booster:"Cobertura Sobrevivientes solo se estima para primera dosis",
  missing_survivors:"Sin población de sobrevivientes válida",
  nonpositive_survivors:"Población de sobrevivientes igual a cero o inválida",
  missing_population:"Sin población de referencia",
  nonpositive_population:"Población de referencia igual a cero o inválida",
};

function parseVaccineComparisonCsv(text) {
  const [header,...lines] = text.trim().split(/\r?\n/);
  const fields = header.split(",");
  const required = ["code","year","dose","doses","reference_population","administrative_coverage_pct","reference_coverage_pct","survivor_population","survivor_coverage_pct"];
  if(required.some(field=>!fields.includes(field))) throw new Error("Faltan columnas en la comparación de coberturas");
  const seen = new Set();
  return lines.map(line=>{
    const parts = line.split(",");
    if(parts.length!==fields.length) throw new Error("Fila incompleta en la comparación de coberturas");
    const row = Object.fromEntries(fields.map((field,i)=>[field,parts[i]]));
    for(const field of ["year","source_analysis_year","dose_source_year","source_rows","doses","pai_target_population",
      "reference_population","administrative_coverage_pct","reference_coverage_pct","survivor_population","survivor_coverage_pct"]){
      row[field] = row[field]==="" ? null : Number(row[field]);
      if(row[field]!==null && (!Number.isFinite(row[field]) || row[field]<0)) throw new Error("Valor inválido en la comparación de coberturas");
    }
    if(!vaccineComparisonDoses[row.dose] || !/^\d{5}$/.test(row.code)) throw new Error("Clave inválida de cobertura");
    const key = `${row.code}/${row.year}/${row.dose}`;
    if(seen.has(key)) throw new Error("Cobertura municipal duplicada");
    seen.add(key);
    row.merged_geography = row.merged_geography==="True";
    return row;
  });
}

function vaccineComparisonColor(value) {
  if(value===null || value===undefined || !Number.isFinite(value) || value<0) return VACCINE_COMPARISON_MISSING;
  const position = Math.min(value,200)/200*(VACCINE_COMPARISON_COLORS.length-1);
  const left = Math.min(Math.floor(position),VACCINE_COMPARISON_COLORS.length-2);
  const fraction = position-left;
  const rgb = hex=>hex.match(/[a-f\d]{2}/gi).map(value=>parseInt(value,16));
  const a=rgb(VACCINE_COMPARISON_COLORS[left]),b=rgb(VACCINE_COMPARISON_COLORS[left+1]);
  return `rgb(${a.map((value,i)=>Math.round(value+(b[i]-value)*fraction)).join(",")})`;
}

function vaccineComparisonState(rows,year,dose,metric) {
  const selected = rows.filter(row=>row.year===Number(year) && row.dose===dose);
  if(!vaccineComparisonMetrics[metric] || !vaccineComparisonDoses[dose]) throw new Error("Selección de cobertura inválida");
  return {year:Number(year),dose,metric,...vaccineComparisonMetrics[metric],byCode:new Map(selected.map(row=>[row.code,row]))};
}

function vaccineComparisonNumber(value) {
  return value===null || value===undefined ? "sin dato" : vaccineComparisonDecimal.format(value);
}

function vaccineComparisonPopup(feature,row,state) {
  const container=document.createElement("div");
  const title=document.createElement("strong");
  title.textContent=`${feature.properties.name} (${feature.properties.code})`;
  container.append(title);
  const age=state.dose==="first_dose"?"1 año":"5 años";
  const pct=value=>value===null || value===undefined ? "sin dato" : `${vaccineComparisonNumber(value)} %`;
  const lines=[feature.properties.department,
    `Año de análisis: ${state.year} · hoja PAI: ${state.year-1}`,
    vaccineComparisonDoses[state.dose],
    `Dosis: ${vaccineComparisonNumber(row?.doses)}`,
    `Meta PAI original: ${vaccineComparisonNumber(row?.pai_target_population)}`,
    `Población de referencia (${age}): ${vaccineComparisonNumber(row?.reference_population)}`,
    `Cobertura administrativa${row?.merged_geography?" ponderada por metas":" publicada"}: ${pct(row?.administrative_coverage_pct)}`,
    `Dosis / población de referencia: ${pct(row?.reference_coverage_pct)}`,
    ...(state.dose==="first_dose" ? [
      `Sobrevivientes de 1 año (${state.year}; nacimientos − defunciones <1 año de ${state.year-1}): ${vaccineComparisonNumber(row?.survivor_population)}`,
      `Cobertura Sobrevivientes: ${pct(row?.survivor_coverage_pct)}`] : []),
    `Color: ${state.label}`];
  if(!row || row[state.status]!=="available") lines.push(vaccineComparisonMissing[row?.[state.status]] || "Sin dato para esta medida");
  if(row?.merged_geography) lines.push("Códigos territoriales homologados: se suman dosis y poblaciones; el porcentaje publicado se pondera por las metas PAI originales.");
  for(const line of lines){const element=document.createElement("div");element.textContent=line;container.append(element);}
  return container;
}

function renderVaccineComparisonLegend(container,state) {
  container.replaceChildren();
  const title=document.createElement("strong");title.textContent=state.label+" (%)";
  const gradient=document.createElement("div");gradient.className="climate-map-gradient";
  gradient.style.background=`linear-gradient(to right, ${VACCINE_COMPARISON_COLORS.join(",")})`;
  const labels=document.createElement("div");labels.className="climate-map-legend-labels";
  for(const value of ["0 %","50 %","100 %","150 %","≥200 %"]){const label=document.createElement("span");label.textContent=value;labels.append(label);}
  const missing=document.createElement("div");missing.className="climate-map-legend-missing";
  const swatch=document.createElement("span");swatch.className="climate-map-missing-swatch";swatch.style.background=VACCINE_COMPARISON_MISSING;
  missing.append(swatch,document.createTextNode("Sin dato para la medida seleccionada"));
  container.append(title,gradient,labels,missing);
}

function initVaccineComparisonPlayer(yearInput,doseInput,metricInput,update) {
  const play=document.querySelector("#vaccine-comparison-play");
  const speed=document.querySelector("#vaccine-comparison-speed");
  const timeline=document.querySelector("#vaccine-comparison-timeline");
  const frame=document.querySelector("#vaccine-comparison-frame");
  const status=document.querySelector("#vaccine-comparison-status");
  let timer=null;
  const years=()=>Array.from(yearInput.options,option=>Number(option.value)).sort((a,b)=>a-b);
  function sync(){
    const allowed=years();
    timeline.min=String(allowed[0]);timeline.max=String(allowed[allowed.length-1]);
    timeline.value=yearInput.value;frame.textContent=`Año: ${yearInput.value}`;
  }
  function stop(){
    if(timer!==null)window.clearTimeout(timer);
    timer=null;play.textContent="▶ Reproducir";play.setAttribute("aria-pressed","false");
    status.setAttribute("aria-live","polite");
  }
  function schedule(){
    timer=window.setTimeout(()=>{
      const allowed=years();
      const index=allowed.indexOf(Number(yearInput.value));
      yearInput.value=String(allowed[(index+1)%allowed.length]);
      update();sync();schedule();
    },1500/Number(speed.value));
  }
  function start(){
    stop();play.textContent="⏸ Pausar";play.setAttribute("aria-pressed","true");
    status.setAttribute("aria-live","off");schedule();
  }
  play.addEventListener("click",()=>timer===null?start():stop());
  speed.addEventListener("change",()=>{if(timer!==null)start();});
  timeline.addEventListener("input",()=>{
    stop();yearInput.value=timeline.value;update();sync();
  });
  for(const input of [yearInput,doseInput,metricInput])input.addEventListener("change",()=>{stop();sync();});
  document.addEventListener("visibilitychange",()=>{if(document.hidden)stop();});
  window.addEventListener("pagehide",stop);
  sync();
}

async function initVaccineCoverageComparison() {
  const controls=document.querySelector("#vaccine-comparison-controls");
  const yearInput=document.querySelector("#vaccine-comparison-year");
  const doseInput=document.querySelector("#vaccine-comparison-dose");
  const metricInput=document.querySelector("#vaccine-comparison-metric");
  const status=document.querySelector("#vaccine-comparison-status");
  try{
    if(typeof L==="undefined") throw new Error("No se pudo cargar Leaflet");
    const responses=await Promise.all([fetch(VACCINE_COMPARISON_URL),fetch(VACCINE_COMPARISON_GEOMETRY)]);
    if(responses.some(response=>!response.ok)) throw new Error("No se pudieron cargar las coberturas o la geometría");
    const [csv,boundaries]=await Promise.all([responses[0].text(),responses[1].json()]);
    const rows=parseVaccineComparisonCsv(csv);
    if(boundaries.type!=="FeatureCollection" || !boundaries.features?.length) throw new Error("Geometría municipal incompleta");
    const years=[...new Set(rows.map(row=>row.year))].sort((a,b)=>b-a);
    function setYearOptions(){
      const previous=Number(yearInput.value);
      const allowed=years.filter(year=>doseInput.value!=="booster" || year>=2019);
      yearInput.replaceChildren();
      for(const year of allowed){const option=document.createElement("option");option.value=String(year);option.textContent=String(year);yearInput.append(option);}
      yearInput.value=String(allowed.includes(previous)?previous:previous && previous<2019 && doseInput.value==="booster"?Math.min(...allowed):allowed[0]);
    }
    setYearOptions();
    let state=vaccineComparisonState(rows,yearInput.value,doseInput.value,metricInput.value);
    const map=L.map("vaccine-comparison-map",{scrollWheelZoom:false,preferCanvas:true});
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",{
      maxZoom:18,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);
    const style=feature=>({color:"#617984",weight:.35,fillOpacity:.9,
      fillColor:vaccineComparisonColor(state.byCode.get(feature.properties.code)?.[state.field])});
    const layer=L.geoJSON(boundaries,{style,onEachFeature(feature,polygon){
      polygon.bindPopup(()=>vaccineComparisonPopup(feature,state.byCode.get(feature.properties.code),state));
      polygon.on("mouseover",()=>polygon.setStyle({weight:1.8,color:"#173042"}));
      polygon.on("mouseout",()=>layer.resetStyle(polygon));
    }}).addTo(map);
    map.fitBounds(layer.getBounds(),{padding:[12,12]});
    function update(){
      const survivorOption=metricInput.querySelector('option[value="survivors"]');
      survivorOption.disabled=doseInput.value==="booster";
      if(survivorOption.disabled && metricInput.value==="survivors")metricInput.value="reference";
      state=vaccineComparisonState(rows,yearInput.value,doseInput.value,metricInput.value);
      map.closePopup();layer.setStyle(style);
      renderVaccineComparisonLegend(document.querySelector("#vaccine-comparison-legend"),state);
      let available=0,above100=0;
      for(const feature of boundaries.features){const value=state.byCode.get(feature.properties.code)?.[state.field];
        if(value!==null && value!==undefined && Number.isFinite(value)){available+=1;if(value>100)above100+=1;}}
      const age=state.dose==="first_dose"?"1 año":"5 años";
      document.querySelector("#vaccine-comparison-formula").textContent=state.metric==="survivors"
        ? `Medida coloreada: 100 × primeras dosis etiquetadas ${state.year} / sobrevivientes de 1 año de ${state.year} (nacimientos − defunciones <1 año de ${state.year-1}).`
        : state.metric==="reference"
        ? `Medida coloreada: 100 × dosis etiquetadas ${state.year} / población de ${age} de ${state.year}.`
        : "Medida coloreada: porcentaje administrativo publicado por PAI; en territorios homologados se pondera por las metas originales.";
      status.textContent=`${state.year} · ${vaccineComparisonDoses[state.dose]} · ${state.label}. `+
        `${available.toLocaleString("es-CO")} de ${boundaries.features.length.toLocaleString("es-CO")} entidades con dato; `+
        `${above100.toLocaleString("es-CO")} superan 100 %. `+
        (state.dose==="booster" && state.year===2019?"La fuente no aporta refuerzo etiquetado 2019; se mantiene sin dato por el rezago metodológico. ":"")+
        (state.metric==="reference" && state.dose==="first_dose" && state.year===2016?"La hoja PAI 2015 usa meta de media cohorte; la nueva medida usa la población de 1 año de 2016. ":"")+
        "La escala es fija entre años, dosis y medidas; los valores ≥200 % usan la intensidad máxima, sin alterar su porcentaje en el detalle.";
      document.querySelector("#vaccine-comparison-map").setAttribute("aria-label",`Mapa municipal de ${state.label}, ${vaccineComparisonDoses[state.dose]}, año de análisis ${state.year}`);
    }
    yearInput.addEventListener("change",update);
    doseInput.addEventListener("change",()=>{setYearOptions();update();});
    metricInput.addEventListener("change",update);
    initVaccineComparisonPlayer(yearInput,doseInput,metricInput,update);
    controls.disabled=false;update();
  }catch(error){status.textContent=`No se pudo mostrar la comparación de coberturas: ${error.message}`;console.error(error);}
}

function observeVaccineCoverageComparison(){
  const target=document.querySelector("#vaccine-comparison-title");
  if(!target)return;
  if(typeof IntersectionObserver==="undefined"){initVaccineCoverageComparison();return;}
  const observer=new IntersectionObserver(entries=>{
    if(entries.some(entry=>entry.isIntersecting)){observer.disconnect();initVaccineCoverageComparison();}
  },{rootMargin:"500px"});
  observer.observe(target);
}

document.addEventListener("DOMContentLoaded",observeVaccineCoverageComparison);
