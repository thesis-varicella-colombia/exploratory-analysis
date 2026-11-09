"use strict";
const comparisonRate=new Intl.NumberFormat('es-CO',{minimumFractionDigits:2,maximumFractionDigits:2});
const comparisonNumber=new Intl.NumberFormat('es-CO');
const comparisonRho=new Intl.NumberFormat('es-CO',{minimumFractionDigits:3,maximumFractionDigits:3});
function comparisonValue(value,format=comparisonRate){return value===null||value===undefined||value===''?'No calculable':format.format(Number(value));}
function comparisonRow(body,values){const tr=document.createElement('tr');for(const [index,value] of values.entries()){const cell=document.createElement(index===0?'th':'td');if(index===0)cell.scope='row';cell.textContent=String(value);tr.append(cell);}body.append(tr);}
async function comparisonCsv(url,numbers){const response=await fetch(url);if(!response.ok)throw new Error('No se pudo cargar '+url);return vega.read(await response.text(),{type:'csv'}).map(row=>{for(const field of numbers)row[field]=row[field]===''?null:Number(row[field]);return row;});}

let rtInformationSelection={id:'national',label:'Colombia'};
let rtInformationData=null,rtInformationVersion=0;
const rtInformationCache=new Map();
function renderRtInformation(){
  if(!rtInformationData)return;
  const limit=Number(document.querySelector('#rt-information-width').value),body=document.querySelector('#rt-information-table');body.replaceChildren();
  const selected=rtInformationData.rows.filter(row=>row.width_limit===limit);
  for(const row of selected){
    const interval=row.longest_days?`${row.longest_start} a ${row.longest_end} (${row.longest_days} días)`:'Sin tramo que cumpla';
    comparisonRow(body,[row.method==='notification'?'Notificación':'Inicio de síntomas',row.period.replaceAll('-','–'),comparisonValue(row.estimated_pct)+' %',comparisonValue(row.information_days,comparisonNumber)+' / '+comparisonValue(row.observed_days,comparisonNumber),comparisonValue(row.information_pct_observed)+' %',comparisonValue(row.median_relative_width),comparisonValue(row.interval_above_one,comparisonNumber)+' / '+comparisonValue(row.interval_below_one,comparisonNumber)+' / '+comparisonValue(row.interval_includes_one,comparisonNumber),interval]);
  }
  document.querySelector('#rt-information-status').textContent=`${rtInformationSelection.label} · criterios exploratorios sobre datos diarios originales; no sobre los promedios de la gráfica.`;
}
async function loadRtInformation(selection){
  rtInformationSelection=selection;const version=++rtInformationVersion,status=document.querySelector('#rt-information-status');
  rtInformationData=null;document.querySelector('#rt-information-table').replaceChildren();
  status.textContent=`Cargando diagnóstico de Rₜ · ${selection.label}…`;
  try{
    if(!rtInformationCache.has(selection.id)){
      const pending=fetch(`data_processed/numero_reproductivo/rt_information/${selection.id}.json?v=20261102`).then(async response=>{
        if(!response.ok)throw new Error('No se pudo cargar el diagnóstico de Rₜ');
        const data=await response.json();
        if(data.id!==selection.id||!Array.isArray(data.rows)||data.rows.length!==24)throw new Error('Diagnóstico territorial incompleto');
        return data;
      }).catch(error=>{rtInformationCache.delete(selection.id);throw error;});
      rtInformationCache.set(selection.id,pending);
      if(rtInformationCache.size>12)rtInformationCache.delete(rtInformationCache.keys().next().value);
    }
    const data=await rtInformationCache.get(selection.id);
    if(version!==rtInformationVersion)return;
    rtInformationData=data;renderRtInformation();
  }catch(error){if(version===rtInformationVersion){rtInformationData=null;document.querySelector('#rt-information-table').replaceChildren();status.textContent=error.message;}console.error(error);}
}
document.addEventListener('rt-selection-changed',event=>{rtInformationSelection=event.detail;if(document.readyState!=='loading')loadRtInformation(event.detail);});
document.addEventListener('DOMContentLoaded',()=>{
  document.querySelector('#rt-information-width').addEventListener('change',renderRtInformation);loadRtInformation(rtInformationSelection);
});
