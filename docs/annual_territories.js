"use strict";

const annualTerritoryState={id:"all",label:"Todos los municipios y departamentos",rows:[]};
const ANNUAL_TERRITORY_ROOT="data_processed/varicela_totales_por_anio";

function annualTerritoryPayload(payload,id,label){
  if(payload.id!==id || !Array.isArray(payload.rows) || payload.rows.length!==19)throw new Error("Serie territorial incompleta");
  return payload.rows.map((row,index)=>{
    if(row.year!==2007+index)throw new Error("Calendario anual incompleto");
    for(const field of ["notifications","population","notification_rate_per_100k","reporting_entities","selected_entities","missing_population_entities","zero_population_entities"]){
      if(row[field]!==null && (!Number.isFinite(row[field]) || row[field]<0))throw new Error("Valor anual inválido");
    }
    if(!Number.isInteger(row.notifications) || row.reporting_entities>row.selected_entities)throw new Error("Conteos anuales inválidos");
    if(id!=="all" && row.official_2007_cases!==null)throw new Error("La referencia oficial de 2007 solo corresponde a Colombia");
    if((row.population===null || row.population<=0) && row.notification_rate_per_100k!==null)throw new Error("Tasa sin denominador válido");
    return {...row,territory_label:label};
  });
}

function annualTerritoryMatch(input,manifest){
  const normalize=value=>value.normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLocaleLowerCase("es").trim();
  if([normalize(manifest.all_label),"todos","colombia"].includes(normalize(input)))return {id:"all",label:manifest.all_label};
  const entities=[...manifest.departments.map(row=>({...row,label:`Departamento · ${row.name} · ${row.code}`})),
    ...manifest.municipalities.map(row=>({...row,label:`${row.code} · ${row.name} · ${row.department}`}))];
  const matched=entities.filter(row=>input===row.id || input===row.code || normalize(input)===normalize(row.label) || normalize(input)===normalize(row.name));
  return matched.length===1?matched[0]:null;
}

async function initAnnualTerritoryFilter(views){
  const controls=document.querySelector("#annual-territory-controls"),input=document.querySelector("#annual-territory-search");
  const status=document.querySelector("#annual-territory-status");
  const cache=new Map();let version=0,queue=Promise.resolve();
  try{
    const fetched=await Promise.allSettled([
      fetch(`${ANNUAL_TERRITORY_ROOT}/manifest.json?v=20261103`),
      fetch(`${ANNUAL_TERRITORY_ROOT}/all.json?v=20261103`),
    ]);
    for(const result of fetched){if(result.status==="rejected")throw result.reason;if(!result.value.ok)throw new Error("No se pudieron cargar los filtros territoriales");}
    const parsed=await Promise.allSettled(fetched.map(result=>result.value.json()));
    for(const result of parsed)if(result.status==="rejected")throw result.reason;
    const manifest=parsed[0].value;
    if(manifest.years?.join(",")!==Array.from({length:19},(_,i)=>2007+i).join(",") || manifest.departments.length!==33 || manifest.municipalities.length!==1122)throw new Error("Catálogo territorial incompleto");
    cache.set("all",Promise.resolve(parsed[1].value));
    const options=document.querySelector("#annual-territory-options");
    for(const label of [manifest.all_label,...manifest.departments.map(row=>`Departamento · ${row.name} · ${row.code}`),
      ...manifest.municipalities.map(row=>`${row.code} · ${row.name} · ${row.department}`)]){
      const option=document.createElement("option");option.value=label;options.append(option);
    }
    async function update(){
      const current=++version;
      const territory=annualTerritoryMatch(input.value.trim(),manifest);
      if(!territory){status.textContent=`Busca y selecciona una opción de la lista. Vista actual: ${annualTerritoryState.label}.`;return;}
      status.textContent=`Cargando ${territory.label}…`;
      try{
        if(!cache.has(territory.id)){
          const pending=fetch(`${ANNUAL_TERRITORY_ROOT}/${territory.id}.json?v=20261103`).then(async response=>{
            if(!response.ok)throw new Error("No se pudo cargar la serie territorial");return response.json();
          }).catch(error=>{cache.delete(territory.id);throw error;});
          cache.set(territory.id,pending);
          if(cache.size>16){const oldest=[...cache.keys()].find(key=>key!=="all");cache.delete(oldest);}
        }
        const payload=await cache.get(territory.id);
        if(current!==version)return;
        const rows=annualTerritoryPayload(payload,territory.id,territory.label);
        queue=queue.then(async()=>{
          if(current!==version)return;
          Object.assign(annualTerritoryState,{id:territory.id,label:territory.label,rows});
          await Promise.all(views.map(view=>view.change("annual_territory",vega.changeset().remove(()=>true).insert(rows)).runAsync()));
          if(current!==version)return;
          document.querySelector("#chart-cases").setAttribute("aria-label",`Notificaciones por año · ${territory.label}; 2007 solo diagnóstico`);
          document.querySelector("#chart-rates").setAttribute("aria-label",`Tasa anual de notificación por 100.000 · ${territory.label}; 2007 solo diagnóstico`);
          document.querySelector("#annual-official-legend").hidden=territory.id!=="all";
          const incomplete=rows.filter(row=>row.missing_population_entities>0 || row.zero_population_entities>0);
          status.textContent=`${territory.label} · 2007–2025 · ${rows[0].selected_entities.toLocaleString("es-CO")} entidades en la selección. `+
            (incomplete.length?`${incomplete.length} años tienen alguna entidad sin población válida. Al pasar el cursor sobre los puntos de la gráfica de tasas, puedes consultar la población disponible y cuántas entidades tienen población ausente o igual a cero. `:"")+
            "Sin población total positiva, la tasa queda sin dato. Los ceros asignados por falta de registro no demuestran ausencia de enfermedad. La cifra oficial de 2007 se muestra solo en el conjunto nacional.";
        });
        await queue;
      }catch(error){if(current===version)status.textContent=`No se pudo cambiar la selección: ${error.message}`;console.error(error);}
    }
    input.value=manifest.all_label;controls.disabled=false;input.addEventListener("input",update);
    await update();
  }catch(error){status.textContent=`No se pudieron cargar los filtros: ${error.message}. Las gráficas muestran el conjunto nacional.`;console.error(error);}
}
