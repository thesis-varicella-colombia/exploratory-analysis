"use strict";

const municipalPriorityNumber = new Intl.NumberFormat("es-CO", {minimumFractionDigits:2, maximumFractionDigits:2});
const municipalPriorityInteger = new Intl.NumberFormat("es-CO");
const municipalPriorityMeasures = [
  ["first_dose_valid_admin", "Primera dosis administrativa"],
  ["first_dose_calculated", "Primera dosis calculada"],
  ["booster_valid_admin", "Segunda dosis administrativa"],
  ["booster_calculated", "Segunda dosis calculada"],
];

const municipalPriorityAgeLabels = {municipal:"Municipal ajustada", under_1:"<1 año", "1_4":"1–4 años", "5_14":"5–14 años"};

function parseMunicipalPriority(text, metadata) {
  const children = metadata.criteria?.children, municipal = metadata.criteria?.municipal;
  if (metadata.years?.join(",") !== "2024,2025" || metadata.coverage_strict_upper_bound !== 80 ||
      children?.baseline_fraction !== .8 || !children.strict || children.groups.join(",") !== "under_1,1_4,5_14" ||
      municipal?.baseline_fraction !== .95 || !municipal.strict || municipal.groups.join(",") !== "municipal") {
    throw new Error("Las reglas del archivo no corresponden a la selección por edad en 2024 Y 2025");
  }
  const rows = vega.read(text, {type:"csv"});
  const seen = new Set();
  let municipalCount = 0, childrenCount = 0;
  for (const row of rows) {
    if (!/^\d{5}$/.test(row.code) || seen.has(row.code) || row.candidate_union !== "True" || !["True","False"].includes(row.candidate_children) || !["True","False"].includes(row.candidate_municipal)) {
      throw new Error("Lista municipal duplicada o con años de selección incorrectos");
    }
    seen.add(row.code);
    const fields = ["cases_2024_2025", "sort_group", "sort_baseline_pct", "sort_undefined_comparisons",
      "sort_group_eb", "sort_baseline_pct_eb", "sort_undefined_comparisons_eb",
      "sort_group_eb_local", "sort_baseline_pct_eb_local", "sort_undefined_comparisons_eb_local",
      ...["municipal",...children.groups].flatMap(age=>[`baseline_${age}`,`incidence_${age}_2024`,`incidence_${age}_2025`,
        `baseline_eb_${age}`,`incidence_eb_${age}_2024`,`incidence_eb_${age}_2025`,
        `baseline_eb_local_${age}`,`incidence_eb_local_${age}_2024`,`incidence_eb_local_${age}_2025`]),
      ...[2024,2025].flatMap(year=>municipalPriorityMeasures.map(([field])=>`${field}_${year}`))];
    for (const field of fields) {
      row[field] = row[field] === "" ? null : Number(row[field]);
      if (row[field] !== null && (!Number.isFinite(row[field]) || row[field] < 0)) throw new Error("Valor municipal inválido");
    }
    if (row.cases_2024_2025 === null) throw new Error("Faltan conteos municipales");
    let municipalPass = true, childrenPass = true;
    for (const year of [2024,2025]) {
      for (const age of children.groups) {
        const baseline = row[`baseline_${age}`], current = row[`incidence_${age}_${year}`];
        const valid = baseline !== null && current !== null;
        if (children.groups.includes(age) && (!valid || current <= Number((.8*baseline).toFixed(8)))) {
          childrenPass = false;
        }
      }
      const baseline = row.baseline_municipal, current = row[`incidence_municipal_${year}`];
      if (baseline === null || current === null || current <= Number((.95*baseline).toFixed(8))) municipalPass = false;
      if (!municipalPriorityLow(row,year).length) throw new Error("Falta cobertura <80 % en uno de los años");
    }
    if (!childrenPass && !municipalPass) throw new Error("Un municipio no cumple ninguno de los dos criterios");
    if (municipalPass !== (row.candidate_municipal === "True") || childrenPass !== (row.candidate_children === "True")) throw new Error("Los indicadores de criterio no coinciden con sus tasas");
    if ((municipalPass && row.qualifying_years_municipal !== "2024;2025") || (childrenPass && row.qualifying_years_children !== "2024;2025")) throw new Error("Falta cumplir un criterio completo en ambos años");
    if (row.sort_group !== (childrenPass ? 0 : 1) || row.selection_group !== (childrenPass ? "Infantil" : "Municipal")) throw new Error("El grupo de orden no coincide con los criterios");
    row.passesChildren = childrenPass;
    if (childrenPass) childrenCount++;
    row.passesMunicipal = municipalPass;
    if (municipalPass) municipalCount++;
  }
  if (rows.length !== metadata.union_candidates || childrenCount !== children.candidates || municipalCount !== municipal.candidates) throw new Error("La lista no coincide con los recuentos por criterio");
  return rows;
}

function municipalPriorityRateSuffix(rate) {
  return rate === "eb" ? "_eb" : rate === "eb_local" ? "_eb_local" : "";
}

function municipalPrioritySort(rows, rate) {
  const suffix = municipalPriorityRateSuffix(rate);
  const pct = row => row[`sort_baseline_pct${suffix}`];
  const grp = row => row[`sort_group${suffix}`];
  return [...rows].sort((a,b)=>grp(a)-grp(b) || (pct(a) ?? Infinity)-(pct(b) ?? Infinity) ||
    a.department.localeCompare(b.department,"es") || a.name.localeCompare(b.name,"es"));
}

function municipalPriorityLow(row, year) {
  return municipalPriorityMeasures.filter(([field])=>row[`${field}_${year}`] !== null && row[`${field}_${year}`] < 80)
    .map(([field,label])=>({label,value:row[`${field}_${year}`]}));
}

async function initMunicipalPriority() {
  const status = document.querySelector("#municipal-priority-status");
  const body = document.querySelector("#municipal-priority-table");
  if (!status || !body) return;
  try {
    const responses = await Promise.allSettled([
      fetch("data_processed/cobertura_vacunacion/municipal_priority_union_2024_2025.csv?v=20261103-eb2"),
      fetch("data_processed/cobertura_vacunacion/municipal_priority_age_2024_2025.metadata.json?v=20261103-eb2"),
    ]);
    for (const response of responses) {
      if (response.status === "rejected") throw response.reason;
      if (!response.value.ok) throw new Error("No se pudo cargar la lista de municipios para revisión");
    }
    const parsed = await Promise.allSettled([responses[0].value.text(), responses[1].value.json()]);
    for (const value of parsed) if (value.status === "rejected") throw value.reason;
    const rows = parseMunicipalPriority(parsed[0].value, parsed[1].value);
    const metadata = parsed[1].value;
    const render = () => {
      const rate = document.querySelector('input[name="municipal-priority-rate"]:checked')?.value ?? "crude";
      renderMunicipalPriority(rows, rate, body, metadata, status);
    };
    const rateControl = document.querySelector("#municipal-priority-rate");
    if (rateControl) rateControl.addEventListener("change", render);
    render();
  } catch (error) {body.replaceChildren(); status.textContent = `No se pudo mostrar la lista: ${error.message}`; console.error(error);}
}

function renderMunicipalPriority(rows, rate, body, metadata, status) {
  const eb = rate === "eb" || rate === "eb_local";
  const suffix = municipalPriorityRateSuffix(rate);
  const pctField = `sort_baseline_pct${suffix}`, refField = `sort_reference${suffix}`, undefField = `sort_undefined_comparisons${suffix}`, groupField = `sort_group${suffix}`;
  body.replaceChildren();
  let previousGroup = null;
  for (const row of municipalPrioritySort(rows, rate)) {
    const tr = document.createElement("tr");
    tr.dataset.selectionGroup = row.selection_group;
    tr.dataset.orderPercentage = row[pctField] === null ? "" : String(row[pctField]);
    if (previousGroup !== null && row[groupField] !== previousGroup) tr.classList.add("municipal-priority-group-start");
    previousGroup = row[groupField];
    const cell = (value, header=false) => {
      const td = document.createElement(header ? "th" : "td");
      if (header) td.scope = "row";
      td.textContent = value; tr.append(td); return td;
    };
    cell(`${row.name} · ${row.code}`, true);
    cell(row.department);
    const marker = cell("");
    if (row.passesChildren) {const line=document.createElement("div");line.textContent="Infantil >80 %";marker.append(line);}
    if (row.passesMunicipal) {const line=document.createElement("strong");line.textContent="Municipal >95 %";marker.append(line);}
    const order = cell(row[pctField] === null ? "Sin porcentaje calculable" : municipalPriorityNumber.format(row[pctField]) + " %");
    const reference = document.createElement("small"); reference.textContent = row[refField];
    reference.style.display = "block"; order.append(reference);
    order.title = row[undefField] ? `${row[undefField]} comparaciones sin porcentaje calculable (basal cero o dato ausente), omitidas del mínimo.` : row[refField];
    for (const year of [null,2024,2025]) {
      const td = cell("");
      for (const [age,label] of Object.entries(municipalPriorityAgeLabels)) {
        const field = year === null ? `baseline${suffix}_${age}` : `incidence${suffix}_${age}_${year}`;
        const line = document.createElement("div");
        line.textContent = `${label}: ${(row[field] === null ? "Sin dato" : municipalPriorityNumber.format(row[field]))}`;
        td.append(line);
      }
    }
    for (const year of [2024,2025]) {
      const td = cell("");
      for (const [field,label] of municipalPriorityMeasures) {
        const value = row[`${field}_${year}`];
        const line = document.createElement(value !== null && value < 80 ? "strong" : "div");
        line.textContent = `${label}: ${value === null ? "Sin dato válido" : municipalPriorityNumber.format(value) + " %"}`;
        td.append(line);
      }
    }
    cell(municipalPriorityInteger.format(row.cases_2024_2025));
    body.append(tr);
  }
  const rateNote = rate === "eb" ? "Tasa suavizada EB (nacional). " : rate === "eb_local" ? "Tasa suavizada EB (vecinos). " : "";
  status.textContent = `${municipalPriorityInteger.format(rows.length)} municipios únicos para revisión de ${municipalPriorityInteger.format(metadata.municipalities)} comparables. ${rateNote}${municipalPriorityCounts(metadata)} Valores redondeados para mostrar.`;
}

function municipalPriorityCounts(metadata) {
  return `Criterio infantil >80 %: ${metadata.criteria.children.candidates}; municipal >95 %: ${metadata.criteria.municipal.candidates}; ambos criterios: ${metadata.intersection_candidates}.`;
}

document.addEventListener("DOMContentLoaded", initMunicipalPriority);
