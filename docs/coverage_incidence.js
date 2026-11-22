"use strict";

const COVERAGE_INCIDENCE_ROOT = "data_processed/cobertura_vacunacion/coverage_incidence";

const COVERAGE_INCIDENCE_RATE_LABELS = {crude:"Cruda", eb:"Suavizada EB (nacional)", eb_local:"Suavizada EB (vecinos)"};

function coverageIncidenceSelection(data, ages, doses, metrics, labels, rate = "crude") {
  const series = [];
  const years = data.years;
  const ageColors = {all:"#bb4c16", under_1:"#a52a2a", "1_4":"#c65d00", "5_14":"#a47d00", "15_49":"#8b3e78", "50_plus":"#9b6b43"};
  const source = rate === "eb" ? data.incidence_eb : rate === "eb_local" ? data.incidence_eb_local : null;
  const useEb = Boolean(source);
  const rateKind = COVERAGE_INCIDENCE_RATE_LABELS[rate] ?? "Cruda";
  for (const age of ages) {
    if (!data.incidence[age]) throw new Error("Grupo de edad inválido");
    const incidence = useEb && source[age] ? source[age] : data.incidence[age];
    const rateLabel = useEb ? ` (${rate === "eb_local" ? "EB vecinos" : "EB"})` : "";
    // Distinct line pattern per rate variant: crude solid, EB national dotted,
    // EB neighbours dash-dot, so the three can be told apart in the chart.
    const rateDash = rate === "eb" ? [2,2] : rate === "eb_local" ? [8,3,2,3] : [];
    for (const year of years) {
      const i = data.years.indexOf(year);
      series.push({id:`incidence/${age}/${rate}`, kind:"incidence", label:`Incidencia · ${labels[age]}${rateLabel}`, age_label:labels[age], year,
        value:incidence[i], crude:data.incidence[age][i], smoothed:useEb ? incidence[i] : null,
        cases:data.cases[age][i], population:data.population[age][i], rate_kind:rateKind,
        record:data.notification_record_present[i], entities:data.incidence_entities?.[age][i] ?? 1,
        missing_records:data.missing_notification_entities?.[age][i] ?? (data.notification_record_present[i] ? 0 : 1), color:ageColors[age], dash:rateDash, unit:"Por 100.000"});
    }
  }
  for (const dose of doses) for (const metric of metrics) {
    if (metric === "survivors" && dose !== "first_dose") continue;
    if (!data.coverage[dose]?.[metric]) throw new Error("Cobertura inválida");
    const doseLabel = dose === "booster" ? "Refuerzo" : "Primera dosis";
    const metricLabel = metric === "survivors" ? "Cobertura Sobrevivientes" : metric === "reference" ? "dosis / población de " + (dose === "booster" ? "5 años" : "1 año") : (data.aggregate ? "administrativa ponderada por metas PAI" : "administrativa");
    for (const year of years) {
      const i = data.years.indexOf(year);
      series.push({id:`coverage/${dose}/${metric}`, kind:"coverage", label:`${doseLabel} · ${metricLabel}`, year,
        value:data.coverage[dose][metric][i], cases:null, population:null, record:null,
        doses:data.coverage_details[dose][metric].doses[i],
        reference_population:data.coverage_details[dose][metric].reference_population[i],
        pai_target_population:data.coverage_details[dose][metric].pai_target_population[i],
        survivor_population:data.coverage_details[dose][metric].survivor_population?.[i] ?? null,
        reference_age:dose === "booster" ? "5 años" : "1 año",
        entities:data.coverage_entities?.[dose][metric][i] ?? (data.coverage[dose][metric][i] === null ? 0 : 1),
        color:metric === "survivors" ? "#16784b" : dose === "booster" ? (metric === "reference" ? "#4c509e" : "#797fc4") : (metric === "reference" ? "#146a8a" : "#3b8eaf"),
        dash:metric === "administrative" ? [6,3] : [], unit:"%"});
    }
  }
  return series;
}

function coverageIncidenceSpec(width) {
  const tooltip = "datum.kind === 'coverage' ? {'Serie':datum.label,'Año de análisis':datum.year,'Hoja PAI':datum.year-1,'Cobertura (%)':isValid(datum.value)?format(datum.value,'.2f'):'Sin dato','Dosis administradas':isValid(datum.doses)?format(datum.doses,',.0f'):'Sin dato','Edad de referencia':datum.reference_age,'Población de referencia DANE':isValid(datum.reference_population)?format(datum.reference_population,',.0f'):'Sin dato','Sobrevivientes de 1 año':isValid(datum.survivor_population)?format(datum.survivor_population,',.0f'):'Sin dato','Año de nacimientos y defunciones <1':datum.year-1,'Meta PAI original':isValid(datum.pai_target_population)?format(datum.pai_target_population,',.2f'):'Sin dato','Entidades incluidas':datum.entities} : {'Serie':datum.label,'Año de análisis':datum.year,'Incidencia por 100.000':isValid(datum.value)?format(datum.value,'.2f'):'Sin dato','Grupo de edad':datum.age_label,'Tasa':datum.rate_kind,'Incidencia cruda por 100.000':isValid(datum.crude)?format(datum.crude,'.2f'):'Sin dato','Notificaciones':datum.cases,'Población del grupo':datum.population,'Entidades incluidas':datum.entities,'Registro de notificación':datum.missing_records>0?datum.missing_records+' entidades sin registro; cero asignado':'Presente'}";
  const marks = [], sources = [];
  for (const [kind, scale] of [["coverage", "coverageY"], ["incidence", "incidenceY"]]) {
    sources.push({name:kind+"Rows", source:"series", transform:[{type:"filter", expr:`datum.kind === '${kind}'`}]},
      {name:kind+"Points", source:kind+"Rows", transform:[{type:"filter", expr:"isValid(datum.value)"}]});
    marks.push({type:"group", from:{facet:{name:kind+"Lines", data:kind+"Rows", groupby:"id"}}, marks:[{
      type:"line", from:{data:kind+"Lines"}, encode:{update:{
        x:{scale:"x",field:"year"}, y:{scale,field:"value"}, defined:{signal:"isValid(datum.value)"},
        stroke:{field:"color"}, strokeDash:{field:"dash"}, strokeWidth:{value:2.5}
      }}
    }]});
    marks.push({type:"symbol", from:{data:kind+"Points"}, encode:{update:{
      x:{scale:"x",field:"year"}, y:{scale,field:"value"}, fill:{field:"color"},
      shape:{value:kind === "coverage" ? "circle" : "diamond"}, size:{value:65}, tooltip:{signal:tooltip}
    }}});
  }
  return {$schema:"https://vega.github.io/schema/vega/v6.json", width, height:360,
    autosize:{type:"fit",contains:"padding",resize:true}, padding:{left:65,right:70,top:15,bottom:45},
    data:[{name:"series",values:[]}, ...sources],
    scales:[{name:"x",type:"linear",domain:[2008,2025],range:"width",zero:false,nice:false},
      {name:"coverageY",type:"linear",domain:{signal:"length(data('coveragePoints')) ? extent(pluck(data('coveragePoints'),'value')) : [0,100]"},range:"height",zero:true,nice:true},
      {name:"incidenceY",type:"linear",domain:{signal:"length(data('incidencePoints')) ? extent(pluck(data('incidencePoints'),'value')) : [0,1]"},range:"height",zero:true,nice:true}],
    axes:[{orient:"bottom",scale:"x",title:"Año de análisis",format:"d",tickMinStep:1,
      tickCount:{signal:"max(2,floor(width/55))"},labelOverlap:"greedy"},
      {orient:"right",scale:"coverageY",title:"Cobertura (%)",titleColor:"#146a8a",labelColor:"#146a8a"},
      {orient:"left",scale:"incidenceY",title:"Incidencia por 100.000",titleColor:"#bb4c16",labelColor:"#bb4c16",grid:true,gridOpacity:.15}],marks};
}

async function initCoverageIncidence() {
  const section = document.querySelector("#coverage-incidence-controls");
  const status = document.querySelector("#coverage-incidence-status");
  const chart = document.querySelector("#coverage-incidence-chart");
  const municipality = document.querySelector("#coverage-incidence-municipality");
  const age = document.querySelector("#coverage-incidence-age");
  const dose = document.querySelector("#coverage-incidence-dose");
  const metric = document.querySelector("#coverage-incidence-metric");
  const cache = new Map();
  let version = 0, queue = Promise.resolve();
  try {
    const response = await fetch(`${COVERAGE_INCIDENCE_ROOT}/manifest.json?v=20261105-survivors-label`);
    if (!response.ok) throw new Error("No se pudo cargar el catálogo de municipios");
    const manifest = await response.json();
    const options = document.querySelector("#coverage-incidence-municipalities");
    const entities = [manifest.aggregate, ...manifest.entities];
    const allOption = document.createElement("option"); allOption.value = manifest.aggregate.name; options.append(allOption);
    for (const entity of [...manifest.entities].sort((a,b) => a.department.localeCompare(b.department,"es") || a.name.localeCompare(b.name,"es"))) {
      const option = document.createElement("option");
      option.value = `${entity.code} · ${entity.name} · ${entity.department}`;
      options.append(option);
    }
    for (const [value, label] of Object.entries(manifest.age_groups)) {
      const item = document.createElement("label"), input = document.createElement("input");
      input.type = "checkbox"; input.value = value; input.checked = value === "all";
      item.append(input, document.createTextNode(" " + label)); age.append(item);
    }
    const tooltip = document.createElement("div");
    tooltip.id = "coverage-incidence-tooltip"; tooltip.className = "modal-tooltip";
    tooltip.setAttribute("role", "tooltip"); tooltip.hidden = true; document.body.append(tooltip);
    const hideTooltip = () => {tooltip.hidden = true;};
    chart.addEventListener("mouseleave", hideTooltip);
    window.addEventListener("scroll", hideTooltip, true);
    window.addEventListener("resize", hideTooltip);
    const view = new vega.View(vega.parse(coverageIncidenceSpec(Math.max(300, chart.clientWidth))), {renderer: "svg", hover: true}).initialize(chart);
    view.tooltip((handler, event, item, value) => showChartTooltip(tooltip, event, value));
    await view.runAsync();
    const controls = document.createElement("div");
    controls.className = "chart-controls";
    chart.before(controls);
    addChartControls(controls, chart, view, () => {
      hideTooltip();
      const rows = view.data("series").map(row => ({...row}));
      const selected = [...new Map(rows.map(row => [row.id, row])).values()];
      const spec = coverageIncidenceSpec(900);
      spec.data[0].values = rows;
      spec.scales.push({name:"selectedSeries", type:"ordinal", domain:selected.map(row=>row.label), range:selected.map(row=>row.color)});
      spec.legends = [{fill:"selectedSeries", orient:"bottom", columns:2, title:"Series seleccionadas", labelLimit:300}];
      return openChartModal(
        `Cobertura e incidencia · ${document.querySelector("#coverage-incidence-selection").textContent}`,
        chart.getAttribute("aria-label"), spec);
    });
    const expand = controls.querySelector(".expand-button");
    expand.disabled = true;
    const checked = group => Array.from(group.querySelectorAll('input[type="checkbox"]:checked'), input => input.value);
    const legend = document.querySelector("#coverage-incidence-legend");
    const clear = () => {
      legend.replaceChildren(); document.querySelector("#coverage-incidence-selection").textContent = "";
      expand.disabled = true;
      hideTooltip();
      queue = queue.then(async () => {view.change("series", vega.changeset().remove(() => true)); await view.runAsync();});
    };
    async function update() {
      const current = ++version;
      const input = municipality.value.trim();
      const normalize = text => text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("es");
      const matches = entities.filter(entity => entity.code === input || entity.code === input.match(/^(\d{5}) ·/)?.[1] || normalize(entity.name) === normalize(input));
      clear();
      if (matches.length !== 1) {status.textContent = "Elige «Todos los municipios», selecciona una entidad de la lista o escribe su código DIVIPOLA completo."; return;}
      const entity = matches[0];
      status.textContent = `Cargando series de ${entity.name}…`;
      try {
        if (!cache.has(entity.code)) {
          const pending = fetch(`${COVERAGE_INCIDENCE_ROOT}/${entity.code}.json?v=20261105-survivors-label`).then(async result => {
            if (!result.ok) throw new Error("No se pudieron cargar las series municipales");
            const data = await result.json();
            if (data.code !== entity.code) throw new Error("Serie de otra entidad");
            return data;
          }).catch(error => {cache.delete(entity.code); throw error;});
          cache.set(entity.code, pending);
          if (cache.size > 12) cache.delete(cache.keys().next().value);
        }
        const data = await cache.get(entity.code);
        if (current !== version) return;
        const selectedAges = checked(age), selectedDoses = checked(dose), selectedMetrics = checked(metric);
        const selectedRate = document.querySelector('input[name="coverage-incidence-rate"]:checked')?.value ?? "crude";
        const rows = coverageIncidenceSelection(data, selectedAges, selectedDoses, selectedMetrics, manifest.age_groups, selectedRate);
        queue = queue.then(async () => {
          if (current !== version) return;
          view.change("series", vega.changeset().remove(() => true).insert(rows)); await view.runAsync();
          if (current !== version) return;
          const unique = [...new Map(rows.map(row => [row.id,row])).values()];
          expand.disabled = unique.length === 0;
          legend.replaceChildren();
          for (const series of unique) {
            const item = document.createElement("span"), swatch = document.createElement("i");
            swatch.style.cssText = `display:inline-block;width:1.6rem;border-top:3px ${series.dash.length ? "dashed" : "solid"} ${series.color}`;
            swatch.setAttribute("aria-hidden","true");
            item.append(swatch, document.createTextNode(series.label)); legend.append(item);
          }
          document.querySelector("#coverage-incidence-selection").textContent = `${entity.name}${data.aggregate ? " · Agregado territorial" : ` · ${entity.department} (${entity.code})`} · ${unique.filter(x=>x.kind === "incidence").length} series de incidencia y ${unique.filter(x=>x.kind === "coverage").length} de cobertura`;
          chart.setAttribute("aria-label", `Series seleccionadas de cobertura e incidencia notificada en ${entity.name}`);
          if (!rows.length) {status.textContent = "No hay series seleccionadas. Marca una edad para ver incidencia, o al menos una dosis y una medida para ver cobertura."; return;}
          const years = [...new Set(rows.map(row=>row.year))].sort();
          const noRecord = years.filter(year=>!data.notification_record_present[data.years.indexOf(year)]).length;
          status.textContent = `${years[0]}–${years.at(-1)} · ${unique.length} series seleccionadas. ` +
            (data.aggregate ? "Agregado de las entidades de la cartografía con datos válidos para cada medida; la tabla indica cuántas incluye cada línea y año. No es un promedio simple de porcentajes o incidencias municipales. " : `${noRecord} años sin registro de notificación, con cero asignado por convención. `) +
            "Los valores ausentes interrumpen las líneas; no se interpolan. La cobertura no se duplica al marcar varias edades.";
        });
        await queue;
      } catch (error) {if (current === version) {status.textContent = error.message; clear();} console.error(error);}
    }
    municipality.value = manifest.aggregate.name;
    const rateControl = document.querySelector("#coverage-incidence-rate");
    for (const control of [municipality, age, dose, metric, rateControl]) control.addEventListener(control === municipality ? "input" : "change", update);
    if (typeof ResizeObserver !== "undefined") new ResizeObserver(() => {
      queue = queue.then(async () => {view.width(Math.max(300, chart.clientWidth)); await view.resize().runAsync();});
    }).observe(chart);
    section.disabled = false;
    await update();
  } catch (error) {status.textContent = error.message; console.error(error);}
}

document.addEventListener("DOMContentLoaded", () => {
  const target = document.querySelector("#coverage-incidence-chart");
  if (!target) return;
  if (typeof IntersectionObserver === "undefined") {initCoverageIncidence(); return;}
  const observer = new IntersectionObserver(entries => {
    if (entries.some(entry => entry.isIntersecting)) {observer.disconnect(); initCoverageIncidence();}
  }, {rootMargin: "300px"});
  observer.observe(target);
});
