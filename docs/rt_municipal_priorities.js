"use strict";

const RT_MUNICIPAL_PRIORITIES_URL = "data_processed/numero_reproductivo/municipal_priorities/web_tables.json?v=20261109-7days-rt5-symptom-sort";

function initRtPrioritySorting(body, group, records) {
  const fields = group === "sustained"
    ? ["code", "name", "department", "notification_start", "notification_days",
      "notification_peak", "symptom_start", "symptom_days", "symptom_peak"]
    : ["code", "name", "department", "notification_peak_date", "notification_peak",
      "symptom_peak_date", "symptom_peak"];
  const headers = [...body.closest("table").querySelectorAll("thead th")];
  const collator = new Intl.Collator("es", { sensitivity: "base", numeric: true });
  let active = fields.indexOf("symptom_peak");
  let ascending = false;
  const controls = headers.map((header, index) => {
    const label = header.dataset.sortLabel || header.textContent.trim();
    header.dataset.sortLabel = label;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "rt-priority-sort";
    const name = document.createElement("span");
    name.textContent = label;
    const arrow = document.createElement("span");
    arrow.className = "sort-arrow";
    arrow.setAttribute("aria-hidden", "true");
    button.append(name, arrow);
    header.replaceChildren(button);
    button.addEventListener("click", () => {
      ascending = index === active ? !ascending : true;
      active = index;
      sort();
    });
    return { header, button, arrow, label };
  });
  function sort() {
    const field = fields[active];
    const ordered = [...records].sort((a, b) => {
      const left = a.data[field], right = b.data[field];
      let comparison = typeof left === "number" && typeof right === "number"
        ? left - right : collator.compare(left, right);
      // Date ranges are ordered by start date, then end date.
      if (comparison === 0 && field.endsWith("_start")) {
        comparison = collator.compare(a.data[field.replace("_start", "_end")],
          b.data[field.replace("_start", "_end")]);
      }
      return (ascending ? comparison : -comparison) || collator.compare(a.data.code, b.data.code);
    });
    const fragment = document.createDocumentFragment();
    for (const record of ordered) fragment.append(record.element);
    body.replaceChildren(fragment);
    controls.forEach(({ header, button, arrow, label }, index) => {
      if (index === active) header.setAttribute("aria-sort", ascending ? "ascending" : "descending");
      else header.removeAttribute("aria-sort");
      arrow.textContent = index === active ? (ascending ? "↑" : "↓") : "↕";
      button.setAttribute("aria-label", `${label}: ordenar de ${index === active && !ascending ? "menor a mayor" : index === active ? "mayor a menor" : "menor a mayor"}`);
    });
  }
  sort();
}

function renderRtMunicipalPriorities(data) {
  if (data.version !== 1 || data.period !== "2022-2025" ||
      data.sustained_min_days !== 7 || data.peak_min_rt !== 5 ||
      !Array.isArray(data.sustained) || !Array.isArray(data.peaks)) {
    throw new Error("Formato de prioridades municipales no válido");
  }
  const number = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 2 });
  const date = new Intl.DateTimeFormat("es-CO", {
    day: "2-digit", month: "2-digit", year: "numeric", timeZone: "UTC",
  });
  const day = value => {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(value) || !Number.isFinite(Date.parse(value))) {
      throw new Error("Fecha municipal no válida");
    }
    return date.format(new Date(`${value}T00:00:00Z`));
  };
  const sets = [];
  const tables = [];
  for (const [group, selector] of [
    ["sustained", "#rt-priority-sustained-table"],
    ["peaks", "#rt-priority-peaks-table"],
  ]) {
    const codes = new Set();
    const fragment = document.createDocumentFragment();
    const records = [];
    for (const row of data[group]) {
      if (!/^\d{5}$/.test(row.code) || codes.has(row.code) || !row.name || !row.department) {
        throw new Error("Municipio repetido o incompleto");
      }
      codes.add(row.code);
      for (const method of ["notification", "symptom"]) {
        const peak = row[`${method}_peak`];
        if (!Number.isFinite(peak) || peak < (group === "sustained" ? 2 : 5) ||
            !(row[`${method}_peak_lo`] > 1) || row[`${method}_peak_hi`] < peak) {
          throw new Error("Pico municipal fuera de los criterios");
        }
        if (group === "sustained" &&
            (!Number.isInteger(row[`${method}_days`]) || row[`${method}_days`] < 7)) {
          throw new Error("Tramo municipal demasiado corto");
        }
      }
      const values = [row.code, row.name, row.department];
      for (const method of ["notification", "symptom"]) {
        if (group === "sustained") {
          values.push(`${day(row[`${method}_start`])} – ${day(row[`${method}_end`])}`,
            number.format(row[`${method}_days`]), number.format(row[`${method}_peak`]));
        } else {
          values.push(day(row[`${method}_peak_date`]), number.format(row[`${method}_peak`]));
        }
      }
      const tr = document.createElement("tr");
      values.forEach((value, index) => {
        const cell = document.createElement(index === 0 ? "th" : "td");
        if (index === 0) cell.scope = "row";
        cell.textContent = value;
        tr.append(cell);
      });
      fragment.append(tr);
      records.push({ element: tr, data: row });
    }
    if (codes.size !== data[group === "sustained" ? "sustained_count" : "peak_count"]) {
      throw new Error("Recuento de municipios inconsistente");
    }
    sets.push(codes);
    tables.push([selector, fragment, group, records]);
  }
  const unique = new Set([...sets[0], ...sets[1]]).size;
  const overlap = [...sets[0]].filter(code => sets[1].has(code)).length;
  if (unique !== data.unique_municipalities || overlap !== data.overlap_count) {
    throw new Error("Solapamiento de listas inconsistente");
  }
  for (const [selector, fragment, group, records] of tables) {
    const body = document.querySelector(selector);
    body.replaceChildren(fragment);
    initRtPrioritySorting(body, group, records);
  }
  document.querySelector("#rt-priority-sustained-caption").textContent =
    `${sets[0].size} municipios · tramos de al menos siete días en ambas fechas · 2022–2025`;
  document.querySelector("#rt-priority-peaks-caption").textContent =
    `${sets[1].size} municipios · picos de Rₜ de al menos cinco en ambas fechas · 2022–2025`;
  document.querySelector("#rt-municipal-priorities-status").textContent =
    `${sets[0].size} municipios con señales sostenidas y ${sets[1].size} con picos muy altos; ` +
    `${overlap} aparecen en ambas listas (${unique} municipios distintos), ` +
    "más dos casos de descensos sostenidos que no se muestran en estas tablas.";
}

async function loadRtMunicipalPriorities() {
  const status = document.querySelector("#rt-municipal-priorities-status");
  if (!status) return;
  try {
    const response = await fetch(RT_MUNICIPAL_PRIORITIES_URL);
    if (!response.ok) throw new Error("No se pudieron descargar las prioridades municipales");
    renderRtMunicipalPriorities(await response.json());
  } catch (error) {
    status.textContent = `No se pudieron cargar las tablas municipales: ${error.message}`;
    console.error(error);
  }
}

document.addEventListener("DOMContentLoaded", loadRtMunicipalPriorities);
