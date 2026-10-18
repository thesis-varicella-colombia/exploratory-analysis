"use strict";

const DATA_URL = "data_processed/annual_series_2007_2025.csv";
const AGE_DATA_URL = "data_processed/age_group_series_2007_2025.csv";
const WEEKLY_DATA_URL = "data_processed/weekly_series_2007_2025.csv?v=20261017-2";
const NUMBER = new Intl.NumberFormat("es-CO");
const RATE = new Intl.NumberFormat("es-CO", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const SCHEMA = "https://vega.github.io/schema/vega-lite/v6.json";
const CHART_WIDTH = window.matchMedia("(max-width: 700px)").matches ? 650 : "container";
const AGE_LABELS = {
  under_1: "Menor de 1 año",
  "1_4": "1–4 años",
  "5_14": "5–14 años",
  "15_49": "15–49 años",
  "50_plus": "50 años o más",
  unknown: "Sin edad",
};
const AGE_ORDER = Object.values(AGE_LABELS);
const AGE_COLORS = ["#197f7a", "#d97736", "#7541a4", "#3569b0", "#b34b70"];
const EVENT_COLOR = "#596b75";
const PANDEMIC_COLOR = "#e8eef1";
const EMBED_OPTIONS = { renderer: "svg", actions: { export: true, source: false, compiled: false, editor: false } };
const ICONS = {
  expand: '<path d="M8 3H3v5m0-5 7 7m6 11h5v-5m0 5-7-7"/>',
  copy: '<rect x="8" y="8" width="12" height="12" rx="1"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"/>',
};
const modal = document.querySelector("#chart-modal");
const modalChart = document.querySelector("#chart-modal-chart");
const modalControls = document.querySelector("#chart-modal-controls");
const modalTooltip = document.querySelector("#chart-modal-tooltip");
let modalView = null;

document.querySelector("#chart-modal-close").addEventListener("click", () => modal.close());
modal.addEventListener("close", () => {
  if (modalView) modalView.finalize();
  modalView = null;
  modalChart.replaceChildren();
  modalControls.replaceChildren();
  modalTooltip.hidden = true;
  modalTooltip.replaceChildren();
});

function showModalTooltip(handler, event, item, value) {
  if (value == null || value === "") {
    modalTooltip.hidden = true;
    return;
  }
  modalTooltip.replaceChildren();
  if (typeof value === "object" && !Array.isArray(value)) {
    const list = document.createElement("dl");
    for (const [label, content] of Object.entries(value)) {
      const name = document.createElement("dt");
      name.textContent = label;
      const detail = document.createElement("dd");
      detail.textContent = String(content);
      list.append(name, detail);
    }
    modalTooltip.append(list);
  } else {
    modalTooltip.textContent = String(value);
  }
  modalTooltip.hidden = false;
  const bounds = modalTooltip.getBoundingClientRect();
  modalTooltip.style.left = `${Math.max(8, Math.min(event.clientX + 12, window.innerWidth - bounds.width - 8))}px`;
  modalTooltip.style.top = `${Math.max(8, Math.min(event.clientY + 12, window.innerHeight - bounds.height - 8))}px`;
}

async function visibleChartPng(view, chart, zoom) {
  const svgBounds = chart.querySelector("svg").getBoundingClientRect();
  const viewport = chart.getBoundingClientRect();
  const left = Math.max(svgBounds.left, viewport.left);
  const top = Math.max(svgBounds.top, viewport.top);
  const right = Math.min(svgBounds.right, viewport.left + chart.clientWidth);
  const bottom = Math.min(svgBounds.bottom, viewport.top + chart.clientHeight);
  if (right <= left || bottom <= top) throw new Error("The chart is outside the visible area");

  const source = await view.toCanvas(2 * zoom);
  const scaleX = source.width / svgBounds.width;
  const scaleY = source.height / svgBounds.height;
  const cropped = document.createElement("canvas");
  cropped.width = Math.round((right - left) * scaleX);
  cropped.height = Math.round((bottom - top) * scaleY);
  const context = cropped.getContext("2d");
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, cropped.width, cropped.height);
  context.drawImage(
    source,
    (left - svgBounds.left) * scaleX,
    (top - svgBounds.top) * scaleY,
    (right - left) * scaleX,
    (bottom - top) * scaleY,
    0, 0, cropped.width, cropped.height,
  );
  return new Promise((resolve, reject) => {
    cropped.toBlob((blob) => blob ? resolve(blob) : reject(new Error("PNG export failed")), "image/png");
  });
}

async function copyChartImage(view, status, visibleArea) {
  if (!navigator.clipboard?.write || typeof ClipboardItem === "undefined") {
    status.textContent = "La copia de imágenes requiere HTTPS o localhost y un navegador compatible.";
    return;
  }
  try {
    const image = visibleArea
      ? visibleChartPng(view, visibleArea.chart, visibleArea.zoom)
      : view.toImageURL("png", 2)
        .then((url) => fetch(url))
        .then((response) => response.blob());
    await navigator.clipboard.write([new ClipboardItem({ "image/png": image })]);
    status.textContent = "Imagen copiada";
  } catch (error) {
    status.textContent = "No se pudo copiar la imagen. Comprueba el permiso del portapapeles.";
    console.error(error);
  }
}

function addChartControls(container, chart, view, openModal) {
  const toolbar = document.createElement("div");
  toolbar.className = "chart-toolbar";
  const status = document.createElement("span");
  status.className = "chart-status";
  status.setAttribute("role", "status");
  const svg = chart.querySelector("svg");
  const baseWidth = Number(svg.getAttribute("width"));
  const baseHeight = Number(svg.getAttribute("height"));
  let zoom = 1;

  function button(label, title, action, icon, parent = toolbar) {
    const control = document.createElement("button");
    control.type = "button";
    control.setAttribute("aria-label", title);
    if (icon) {
      const graphic = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      graphic.setAttribute("class", "control-icon");
      graphic.setAttribute("viewBox", "0 0 24 24");
      graphic.setAttribute("aria-hidden", "true");
      graphic.innerHTML = ICONS[icon];
      control.append(graphic);
    }
    if (label) control.append(document.createTextNode(label));
    control.addEventListener("click", action);
    parent.append(control);
    return control;
  }

  let zoomOut;
  let zoomIn;
  let zoomValue;
  if (openModal) {
    button("Ampliar", "Ampliar gráfico", openModal, "expand").className = "expand-button";
  } else {
    const zoomGroup = document.createElement("span");
    zoomGroup.className = "zoom-group";
    zoomOut = button("−", "Alejar gráfico", () => changeZoom(-0.25), null, zoomGroup);
    zoomValue = document.createElement("output");
    zoomValue.className = "zoom-value";
    zoomValue.textContent = "100%";
    zoomGroup.append(zoomValue);
    zoomIn = button("+", "Acercar gráfico", () => changeZoom(0.25), null, zoomGroup);
    toolbar.append(zoomGroup);
  }
  button(openModal ? "" : "Copiar", "Copiar gráfico como imagen PNG", () => {
    const visibleArea = openModal ? null : { chart, zoom };
    copyChartImage(view, status, visibleArea);
  }, "copy");
  toolbar.append(status);
  container.append(toolbar);

  function changeZoom(step) {
    const next = Math.max(0.75, Math.min(2.5, zoom + step));
    if (next === zoom) return;
    svg.style.width = `${Math.round(baseWidth * next)}px`;
    svg.style.height = `${Math.round(baseHeight * next)}px`;
    zoom = next;
    zoomValue.textContent = `${Math.round(zoom * 100)}%`;
    zoomOut.disabled = zoom <= 0.75;
    zoomIn.disabled = zoom >= 2.5;
  }
}

async function openChartModal(title, description, spec) {
  if (modal.open) return;
  document.querySelector("#chart-modal-title").textContent = title;
  modalChart.setAttribute("aria-label", description);
  modalChart.textContent = "Cargando gráfico…";
  modal.showModal();
  try {
    const modalSpec = { ...spec, width: CHART_WIDTH };
    const result = await vegaEmbed(modalChart, modalSpec, { ...EMBED_OPTIONS, tooltip: showModalTooltip });
    if (!modal.open) {
      result.view.finalize();
      return;
    }
    modalView = result.view;
    addChartControls(modalControls, modalChart, modalView, null);
  } catch (error) {
    modalChart.textContent = `No se pudo ampliar el gráfico: ${error.message}`;
    console.error(error);
  }
}

async function renderChart(selector, title, spec) {
  const chart = document.querySelector(selector);
  if (!chart.getAttribute("aria-label").includes("Marcas de contexto")) {
    chart.setAttribute("aria-label", `${chart.getAttribute("aria-label")}. Marcas de contexto: vacuna introducida en 2015, refuerzo introducido en 2019 y pandemia en 2020–2021.`);
  }
  const result = await vegaEmbed(chart, spec, EMBED_OPTIONS);
  const controls = document.createElement("div");
  controls.className = "chart-controls";
  chart.before(controls);
  addChartControls(controls, chart, result.view, () => openChartModal(title, chart.getAttribute("aria-label"), spec));
  return result.view;
}

function csvObjects(text) {
  const lines = text.trim().split(/\r?\n/);
  const columns = lines.shift().split(",");
  return lines.map((line) => {
    const values = line.split(",");
    return Object.fromEntries(columns.map((column, index) => [column, values[index]]));
  });
}

function parseCsv(text) {
  return csvObjects(text).map((row) => ({
      year: Number(row.year),
      notifications: Number(row.notifications),
      reporting_entities: Number(row.reporting_entities),
      population: Number(row.population),
      notification_rate_per_100k: Number(row.notification_rate_per_100k),
      official_2007_cases: row.official_2007_cases ? Number(row.official_2007_cases) : null,
  }));
}

function parseAgeCsv(text) {
  return csvObjects(text).map((row) => ({
    year: Number(row.year),
    age_group: row.age_group,
    age_label: AGE_LABELS[row.age_group],
    notifications: Number(row.notifications),
    population: row.population ? Number(row.population) : null,
    notification_rate_per_100k: row.notification_rate_per_100k ? Number(row.notification_rate_per_100k) : null,
  }));
}

function parseWeeklyCsv(text) {
  return csvObjects(text).map((row) => ({
    year: Number(row.year),
    week: Number(row.week),
    week_position: Number(row.week_position),
    age_group: row.age_group,
    age_label: row.age_group === "all" ? "Todas las edades" : AGE_LABELS[row.age_group],
    notifications: row.notifications === "" ? null : Number(row.notifications),
    population: Number(row.population),
    notification_rate_per_100k: row.notification_rate_per_100k === ""
      ? null : Number(row.notification_rate_per_100k),
  }));
}

function fillTable(rows) {
  const body = document.querySelector("#annual-table");
  body.replaceChildren();
  for (const row of rows) {
    const tr = document.createElement("tr");
    if (row.year === 2007) tr.className = "questioned";
    for (const value of [
      row.year,
      NUMBER.format(row.notifications),
      NUMBER.format(row.population),
      RATE.format(row.notification_rate_per_100k),
      NUMBER.format(row.reporting_entities),
    ]) {
      const td = document.createElement("td");
      td.textContent = value;
      tr.append(td);
    }
    body.append(tr);
  }
}

function sharedSpec(rows, yField, yTitle) {
  return {
    $schema: SCHEMA,
    width: CHART_WIDTH,
    height: 290,
    background: "transparent",
    data: { values: rows },
    encoding: {
      x: {
        field: "year", type: "ordinal", title: "Año epidemiológico",
        axis: { labelAngle: -45, labelColor: "#425c68", titleColor: "#425c68" },
      },
      y: {
        field: yField, type: "quantitative", title: yTitle,
        scale: { zero: true },
        axis: { gridColor: "#e4ecee", labelColor: "#425c68", titleColor: "#425c68" },
      },
    },
    config: { view: { stroke: null }, font: "system-ui, sans-serif" },
  };
}

function eventLabelMark() {
  return {
    type: "text", align: "left", dx: 5, baseline: "top", fontSize: 12, fontWeight: 700,
    color: "#173042",
  };
}

function annualEventLayers() {
  return [
    {
      data: { values: [{ year: 2020 }, { year: 2021 }] },
      mark: { type: "rect", color: PANDEMIC_COLOR, opacity: 0.7 },
      encoding: { x: { field: "year", type: "ordinal" }, y: { value: 0 }, y2: { value: 290 } },
    },
    {
      data: { values: [{ year: 2015 }, { year: 2019 }] },
      mark: { type: "rule", color: EVENT_COLOR, strokeDash: [4, 3], strokeWidth: 1.5 },
      encoding: { x: { field: "year", type: "ordinal" }, y: { value: 0 }, y2: { value: 290 } },
    },
    ...[
      { year: 2015, label: "Vacuna", y: 12 },
      { year: 2019, label: "Refuerzo", y: 30 },
      { year: 2020, label: "Pandemia 2020–21", y: 48 },
    ].map(({ year, label, y }) => ({
      data: { values: [{ year, label }] },
      mark: eventLabelMark(),
      encoding: { x: { field: "year", type: "ordinal" }, y: { value: y }, text: { field: "label" } },
    })),
  ];
}

function weeklyEventLayers(rows) {
  const start = (year) => rows.find((row) => row.year === year && row.week === 1).week_position;
  return [
    {
      data: { values: [{ start: start(2020), end: start(2022) }] },
      mark: { type: "rect", color: PANDEMIC_COLOR, opacity: 0.7 },
      encoding: {
        x: { field: "start", type: "quantitative" }, x2: { field: "end" },
        y: { value: 0 }, y2: { value: 300 },
      },
    },
    {
      data: { values: [{ position: start(2015) }, { position: start(2019) }] },
      mark: { type: "rule", color: EVENT_COLOR, strokeDash: [4, 3], strokeWidth: 1.5 },
      encoding: { x: { field: "position", type: "quantitative" }, y: { value: 0 }, y2: { value: 300 } },
    },
    ...[
      { year: 2015, label: "Vacuna", y: 12 },
      { year: 2019, label: "Refuerzo", y: 30 },
      { year: 2020, label: "Pandemia 2020–21", y: 48 },
    ].map(({ year, label, y }) => ({
      data: { values: [{ position: start(year), label }] },
      mark: eventLabelMark(),
      encoding: { x: { field: "position", type: "quantitative" }, y: { value: y }, text: { field: "label" } },
    })),
  ];
}

function casesSpec(rows) {
  const [eventBand, ...eventMarks] = annualEventLayers();
  return {
    ...sharedSpec(rows, "notifications", "Notificaciones"),
    layer: [
      eventBand,
      {
        mark: { type: "bar", cornerRadiusTopLeft: 2, cornerRadiusTopRight: 2 },
        encoding: {
          color: { condition: { test: "datum.year === 2007", value: "#d97736" }, value: "#197f7a" },
          tooltip: [
            { field: "year", title: "Año" },
            { field: "notifications", title: "Notificaciones", format: ",d" },
            { field: "reporting_entities", title: "Entidades con registros" },
          ],
        },
      },
      {
        transform: [{ filter: "datum.year === 2007" }],
        mark: { type: "point", shape: "diamond", filled: true, size: 240, color: "#7541a4" },
        encoding: {
          y: { field: "official_2007_cases", type: "quantitative" },
          tooltip: [
            { field: "year", title: "Año" },
            { field: "official_2007_cases", title: "Documento oficial: casos", format: ",d" },
          ],
        },
      },
      ...eventMarks,
    ],
  };
}

function ratesSpec(rows) {
  const [eventBand, ...eventMarks] = annualEventLayers();
  return {
    ...sharedSpec(rows, "notification_rate_per_100k", "Notificaciones por 100.000 habitantes"),
    layer: [
      eventBand,
      {
        transform: [{ filter: "datum.year >= 2008" }],
        mark: { type: "line", color: "#197f7a", strokeWidth: 3, point: { filled: true, fill: "#197f7a", size: 65 } },
        encoding: {
          tooltip: [
            { field: "year", title: "Año" },
            { field: "notification_rate_per_100k", title: "Tasa por 100.000", format: ".2f" },
            { field: "notifications", title: "Notificaciones", format: ",d" },
          ],
        },
      },
      {
        transform: [{ filter: "datum.year === 2007" }],
        mark: { type: "point", filled: true, size: 170, color: "#d97736" },
        encoding: {
          tooltip: [
            { field: "year", title: "Año cuestionado" },
            { field: "notification_rate_per_100k", title: "Tasa observada", format: ".2f" },
          ],
        },
      },
      ...eventMarks,
    ],
  };
}

function weeklySpec(rows, field) {
  const isRate = field === "notification_rate_per_100k";
  const [eventBand, ...eventMarks] = weeklyEventLayers(rows);
  const yearTicks = rows.filter((row) => row.week === 1).map((row) => row.week_position);
  const tooltip = [
    { field: "age_label", title: "Grupo de edad" },
    { field: "year", title: "Año epidemiológico" },
    { field: "week", title: "Semana epidemiológica" },
    { field: "notifications", title: "Notificaciones", format: ",d" },
  ];
  if (isRate) tooltip.push({ field, title: "Tasa semanal por 100.000", format: ".2f" });
  return {
    $schema: SCHEMA,
    title: `${isRate ? "Incidencia notificada" : "Notificaciones"} por semana · ${rows[0].age_label}`,
    width: CHART_WIDTH,
    height: 300,
    background: "transparent",
    data: { values: rows },
    encoding: {
      x: {
        field: "week_position", type: "quantitative", title: "Año epidemiológico",
        scale: { domain: [1, rows.at(-1).week_position], nice: false, zero: false },
        axis: {
          values: yearTicks,
          labelExpr: `2007 + indexof(${JSON.stringify(yearTicks)}, datum.value)`,
          labelAngle: -45, labelColor: "#425c68", titleColor: "#425c68",
        },
      },
      y: {
        field, type: "quantitative",
        title: isRate ? "Notificaciones semanales por 100.000" : "Notificaciones semanales",
        scale: { zero: true },
        axis: { gridColor: "#e4ecee", labelColor: "#425c68", titleColor: "#425c68" },
      },
    },
    layer: [
      eventBand,
      {
        transform: [{ filter: "datum.year >= 2008" }],
        mark: { type: "line", color: "#197f7a", strokeWidth: 1.7 },
      },
      {
        transform: [{ filter: "datum.year === 2007" }],
        mark: { type: "line", color: "#d97736", strokeWidth: 1.7 },
      },
      {
        transform: [{ filter: `datum.${field} != null` }],
        mark: { type: "point", filled: true, opacity: 0.01, size: 110 },
        encoding: { tooltip },
      },
      ...eventMarks,
    ],
    config: { view: { stroke: null }, font: "system-ui, sans-serif" },
  };
}

function ageSpec(rows, field) {
  const isRate = field === "notification_rate_per_100k";
  const [eventBand, ...eventMarks] = annualEventLayers();
  return {
    $schema: SCHEMA,
    width: CHART_WIDTH,
    height: 290,
    background: "transparent",
    data: { values: rows.filter((row) => row.age_group !== "unknown") },
    encoding: {
      x: {
        field: "year", type: "ordinal", title: "Año epidemiológico",
        axis: { labelAngle: -45, labelColor: "#425c68", titleColor: "#425c68" },
      },
      y: {
        field, type: "quantitative",
        title: isRate ? "Notificaciones por 100.000" : "Notificaciones",
        scale: { zero: true },
        axis: { gridColor: "#e4ecee", labelColor: "#425c68", titleColor: "#425c68" },
      },
    },
    layer: [
      eventBand,
      {
        mark: { type: "line", strokeWidth: 2.5, point: { filled: true, size: 55 } },
        encoding: {
          color: {
            field: "age_label", type: "nominal",
            scale: { domain: AGE_ORDER.slice(0, 5), range: AGE_COLORS },
            legend: { title: null, orient: "bottom", direction: "horizontal", columns: 3 },
          },
          tooltip: isRate
            ? [
                { field: "year", title: "Año" },
                { field: "age_label", title: "Grupo de edad" },
                { field: "notification_rate_per_100k", title: "Tasa por 100.000", format: ".2f" },
                { field: "notifications", title: "Notificaciones", format: ",d" },
                { field: "population", title: "Población", format: ",d" },
              ]
            : [
                { field: "year", title: "Año" },
                { field: "age_label", title: "Grupo de edad" },
                { field: "notifications", title: "Notificaciones", format: ",d" },
              ],
        },
      },
      ...eventMarks,
    ],
    config: { view: { stroke: null }, font: "system-ui, sans-serif" },
  };
}

function ageShiftSpec(rows) {
  const totals = new Map();
  for (const row of rows) totals.set(row.year, (totals.get(row.year) ?? 0) + row.notifications);
  const values = rows.map((row) => ({
    year: row.year,
    age_label: row.age_label,
    age_order: AGE_ORDER.indexOf(row.age_label),
    notifications: row.notifications,
    total: totals.get(row.year),
    share: row.notifications / totals.get(row.year),
  }));
  const [eventBand, ...eventMarks] = annualEventLayers();
  return {
    $schema: SCHEMA,
    width: CHART_WIDTH,
    height: 290,
    background: "transparent",
    data: { values },
    encoding: {
      x: {
        field: "year", type: "ordinal", title: "Año epidemiológico",
        axis: { labelAngle: -45, labelColor: "#425c68", titleColor: "#425c68" },
      },
      y: {
        field: "share", type: "quantitative", title: "Porcentaje de notificaciones",
        stack: "zero", scale: { domain: [0, 1] },
        axis: { format: ".0%", gridColor: "#e4ecee", labelColor: "#425c68", titleColor: "#425c68" },
      },
    },
    layer: [
      eventBand,
      {
        mark: { type: "bar", opacity: 0.9 },
        encoding: {
          color: {
            field: "age_label", type: "nominal",
            scale: { domain: AGE_ORDER, range: [...AGE_COLORS, "#91a0a8"] },
            legend: { title: "Grupo de edad", orient: "bottom", direction: "horizontal", columns: 3 },
          },
          order: { field: "age_order", type: "quantitative" },
          tooltip: [
            { field: "year", title: "Año" },
            { field: "age_label", title: "Grupo de edad" },
            { field: "notifications", title: "Notificaciones", format: ",d" },
            { field: "total", title: "Total anual", format: ",d" },
            { field: "share", title: "Participación", format: ".1%" },
          ],
        },
      },
      ...eventMarks,
    ],
    config: { view: { stroke: null }, font: "system-ui, sans-serif" },
  };
}

function ageShiftRatioRows(rows) {
  const byYear = new Map();
  for (const row of rows) {
    if (!byYear.has(row.year)) byYear.set(row.year, new Map());
    byYear.get(row.year).set(row.age_group, row);
  }
  return [...byYear].map(([year, groups]) => {
    const adult = groups.get("15_49");
    const child = groups.get("1_4");
    const adultIncidence = adult.notifications / adult.population * 100000;
    const childIncidence = child.notifications / child.population * 100000;
    return {
      year,
      adult_incidence: adultIncidence,
      child_incidence: childIncidence,
      asr: adultIncidence / childIncidence,
      inverse: childIncidence / adultIncidence,
    };
  });
}

function ageShiftRatioSpec(rows) {
  const [eventBand, ...eventMarks] = annualEventLayers();
  return {
    $schema: SCHEMA,
    width: CHART_WIDTH,
    height: 290,
    background: "transparent",
    data: { values: rows },
    encoding: {
      x: {
        field: "year", type: "ordinal", title: "Año epidemiológico",
        axis: { labelAngle: -45, labelColor: "#425c68", titleColor: "#425c68" },
      },
      y: {
        field: "asr", type: "quantitative", title: "ASR: incidencia 15–49 / incidencia 1–4",
        scale: { zero: true },
        axis: { gridColor: "#e4ecee", labelColor: "#425c68", titleColor: "#425c68", format: ".2f" },
      },
    },
    layer: [
      eventBand,
      {
        transform: [{ filter: "datum.year >= 2008" }],
        mark: { type: "line", color: "#197f7a", strokeWidth: 3, point: { filled: true, size: 65 } },
        encoding: {
          tooltip: [
            { field: "year", title: "Año" },
            { field: "asr", title: "ASR 15–49 / 1–4", format: ".3f" },
            { field: "inverse", title: "Inversa 1–4 / 15–49", format: ".2f" },
            { field: "adult_incidence", title: "Incidencia 15–49 por 100.000", format: ".2f" },
            { field: "child_incidence", title: "Incidencia 1–4 por 100.000", format: ".2f" },
          ],
        },
      },
      {
        transform: [{ filter: "datum.year === 2007" }],
        mark: { type: "point", filled: true, size: 170, color: "#d97736" },
        encoding: {
          tooltip: [
            { field: "year", title: "Año diagnóstico" },
            { field: "asr", title: "ASR 15–49 / 1–4", format: ".3f" },
            { field: "inverse", title: "Inversa 1–4 / 15–49", format: ".2f" },
          ],
        },
      },
      ...eventMarks,
    ],
    config: { view: { stroke: null }, font: "system-ui, sans-serif" },
  };
}

function fillAgeShiftRatio(rows) {
  const body = document.querySelector("#age-shift-ratio-table");
  body.replaceChildren();
  for (const row of rows) {
    const tr = document.createElement("tr");
    if (row.year === 2007) tr.className = "questioned";
    for (const value of [row.year, RATE.format(row.adult_incidence), RATE.format(row.child_incidence),
      RATE.format(row.asr), RATE.format(row.inverse)]) {
      const td = document.createElement("td");
      td.textContent = value;
      tr.append(td);
    }
    body.append(tr);
  }
  const median = (values) => {
    const sorted = values.toSorted((a, b) => a - b);
    const middle = Math.floor(sorted.length / 2);
    return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
  };
  const before = median(rows.filter((row) => row.year >= 2008 && row.year < 2015).map((row) => row.asr));
  const after = median(rows.filter((row) => row.year >= 2015).map((row) => row.asr));
  const asrIn = (year) => RATE.format(rows.find((row) => row.year === year).asr);
  document.querySelector("#age-shift-ratio-summary").textContent =
    `Mediana de ASR: ${RATE.format(before)} en 2008–2014 y ${RATE.format(after)} en 2015–2025. ` +
    `La razón pasó de ${asrIn(2015)} en 2015 a ${asrIn(2019)} en 2019; cayó a ${asrIn(2021)} en 2021, ` +
    `alcanzó ${asrIn(2024)} en 2024 y fue ${asrIn(2025)} en 2025. `;
}

function infantProtectionSpec(rows) {
  const [eventBand, ...eventMarks] = annualEventLayers();
  return {
    $schema: SCHEMA,
    width: CHART_WIDTH,
    height: 290,
    background: "transparent",
    data: { values: rows.filter((row) => row.year >= 2008 && ["under_1", "1_4"].includes(row.age_group)) },
    encoding: {
      x: {
        field: "year", type: "ordinal", title: "Año epidemiológico",
        axis: { labelAngle: -45, labelColor: "#425c68", titleColor: "#425c68" },
      },
      y: {
        field: "notification_rate_per_100k", type: "quantitative",
        title: "Notificaciones por 100.000 habitantes",
        scale: { zero: true },
        axis: { gridColor: "#e4ecee", labelColor: "#425c68", titleColor: "#425c68" },
      },
    },
    layer: [
      eventBand,
      {
        mark: { type: "line", strokeWidth: 3, point: { filled: true, size: 65 } },
        encoding: {
          color: {
            field: "age_label", type: "nominal",
            scale: { domain: [AGE_LABELS.under_1, AGE_LABELS["1_4"]], range: ["#197f7a", "#3569b0"] },
            legend: { title: "Grupo de edad", orient: "bottom", direction: "horizontal" },
          },
          tooltip: [
            { field: "year", title: "Año" },
            { field: "age_label", title: "Grupo de edad" },
            { field: "notification_rate_per_100k", title: "Tasa por 100.000", format: ".2f" },
            { field: "notifications", title: "Notificaciones", format: ",d" },
            { field: "population", title: "Población", format: ",d" },
          ],
        },
      },
      ...eventMarks,
    ],
    config: { view: { stroke: null }, font: "system-ui, sans-serif" },
  };
}

function fillInfantProtectionSummary(rows) {
  const infant = rows.filter((row) => row.age_group === "under_1");
  const median = (start, end) => {
    const values = infant.filter((row) => row.year >= start && row.year <= end)
      .map((row) => row.notifications / row.population * 100000).toSorted((a, b) => a - b);
    const middle = Math.floor(values.length / 2);
    return values.length % 2 ? values[middle] : (values[middle - 1] + values[middle]) / 2;
  };
  document.querySelector("#infant-protection-summary").textContent =
    `Mediana de la incidencia notificada en menores de 1 año: ${NUMBER.format(Math.round(median(2008, 2014)))} ` +
    `por 100.000 en 2008–2014, ${NUMBER.format(Math.round(median(2015, 2019)))} en 2015–2019 y ` +
    `${NUMBER.format(Math.round(median(2022, 2025)))} en 2022–2025. ` +
    "La mediana no disminuyó en los primeros años tras 2015. La caída posterior coincide con la pandemia y otros cambios posibles en transmisión o notificación; estos datos no permiten atribuirla a protección indirecta.";
}

function fillAgeTable(rows) {
  const body = document.querySelector("#age-table");
  body.replaceChildren();
  for (const row of rows) {
    const tr = document.createElement("tr");
    for (const value of [
      row.year,
      row.age_label,
      NUMBER.format(row.notifications),
      row.population === null ? "—" : NUMBER.format(row.population),
      row.notification_rate_per_100k === null ? "—" : RATE.format(row.notification_rate_per_100k),
    ]) {
      const td = document.createElement("td");
      td.textContent = value;
      tr.append(td);
    }
    body.append(tr);
  }
}

function fillWeeklyTable(rows) {
  const body = document.querySelector("#weekly-table");
  const fragment = document.createDocumentFragment();
  document.querySelector("#weekly-table-caption").textContent = rows[0].age_label;
  for (const row of rows) {
    const tr = document.createElement("tr");
    if (row.year === 2007) tr.className = "questioned";
    for (const value of [
      row.year,
      row.week,
      row.notifications === null ? "—" : NUMBER.format(row.notifications),
      NUMBER.format(row.population),
      row.notification_rate_per_100k === null ? "—" : RATE.format(row.notification_rate_per_100k),
    ]) {
      const td = document.createElement("td");
      td.textContent = value;
      tr.append(td);
    }
    fragment.append(tr);
  }
  body.replaceChildren(fragment);
}

async function loadAgeCharts() {
  const chartIds = ["#chart-age-cases", "#chart-age-rates", "#chart-age-shift", "#chart-age-shift-ratio", "#chart-infant-protection"];
  try {
    const response = await fetch(AGE_DATA_URL);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const rows = parseAgeCsv(await response.text());
    if (rows.length !== 114 || rows.some((row) => !row.age_label) || rows[0].year !== 2007 || rows.at(-1).year !== 2025) {
      throw new Error("The age-group series is incomplete");
    }
    fillAgeTable(rows);
    const ratioRows = ageShiftRatioRows(rows);
    fillAgeShiftRatio(ratioRows);
    fillInfantProtectionSummary(rows);
    const unknown = rows.filter((row) => row.age_group === "unknown")
      .reduce((total, row) => total + row.notifications, 0);
    document.querySelector("#age-unknown-note").textContent =
      `Entre 2007 y 2025 hay ${NUMBER.format(unknown)} notificaciones sin edad registrada.`;
    if (typeof vegaEmbed !== "function") throw new Error("Vega-Lite could not be loaded");
    await Promise.all([
      renderChart(chartIds[0], "Casos notificados por grupo de edad", ageSpec(rows, "notifications")),
      renderChart(chartIds[1], "Incidencia notificada por grupo de edad", ageSpec(rows, "notification_rate_per_100k")),
      renderChart(chartIds[2], "Composición etaria de las notificaciones", ageShiftSpec(rows)),
      renderChart(chartIds[3], "Razón de incidencias 15–49 / 1–4", ageShiftRatioSpec(ratioRows)),
      renderChart(chartIds[4], "Incidencia en menores de 1 año y de 1–4 años", infantProtectionSpec(rows)),
    ]);
  } catch (error) {
    showError(error);
  }

  function showError(error) {
    for (const id of chartIds) {
      const chart = document.querySelector(id);
      if (!chart.querySelector("svg")) chart.textContent = `No se pudieron cargar los gráficos por edad: ${error.message}`;
    }
    console.error(error);
  }
}

async function loadWeeklyCharts() {
  const chartIds = ["#chart-weekly-cases", "#chart-weekly-rates"];
  const selector = document.querySelector("#weekly-age-group");
  let views = [];

  async function renderSelected(rows) {
    for (const [index, id] of chartIds.entries()) {
      views[index]?.finalize();
      const chart = document.querySelector(id);
      if (chart.previousElementSibling?.classList.contains("chart-controls")) {
        chart.previousElementSibling.remove();
      }
      chart.replaceChildren();
      const field = index === 0 ? "notifications" : "notification_rate_per_100k";
      const title = `${index === 0 ? "Notificaciones por semana" : "Incidencia notificada por semana"} · ${rows[0].age_label}`;
      chart.setAttribute("aria-label", `${title}, 2007–2025; 2007 es diagnóstico`);
      views[index] = await renderChart(id, title, weeklySpec(rows, field));
    }
  }

  try {
    const response = await fetch(WEEKLY_DATA_URL, { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const rows = parseWeeklyCsv(await response.text());
    if (rows.length < 5880 || rows[0].year !== 2007 || rows[0].week !== 1 ||
        rows.at(-1).year !== 2025 || rows.at(-1).week !== 53 ||
        rows.filter((row) => row.week === 1 && row.age_group === "all").length !== 19 ||
        rows.some((row) => !row.age_label)) {
      throw new Error("The weekly series is incomplete");
    }
    let selectedRows = rows.filter((row) => row.age_group === selector.value);
    fillWeeklyTable(selectedRows);
    selector.addEventListener("change", async () => {
      selector.disabled = true;
      try {
        selectedRows = rows.filter((row) => row.age_group === selector.value);
        fillWeeklyTable(selectedRows);
        if (typeof vegaEmbed !== "function") return;
        await renderSelected(selectedRows);
      } catch (error) {
        for (const id of chartIds) {
          const chart = document.querySelector(id);
          if (!chart.querySelector("svg")) chart.textContent = `No se pudo actualizar el gráfico semanal: ${error.message}`;
        }
        console.error(error);
      } finally {
        selector.disabled = false;
      }
    });
    if (typeof vegaEmbed !== "function") throw new Error("Vega-Lite could not be loaded");
    await renderSelected(selectedRows);
    selector.disabled = false;
  } catch (error) {
    for (const id of chartIds) {
      const chart = document.querySelector(id);
      if (!chart.querySelector("svg")) chart.textContent = `No se pudieron cargar los gráficos semanales: ${error.message}`;
    }
    const body = document.querySelector("#weekly-table");
    if (body.textContent.includes("Cargando datos semanales")) {
      body.innerHTML = `<tr><td colspan="5">No se pudo cargar la tabla semanal.</td></tr>`;
    }
    if (body.textContent.includes("No se pudo cargar")) selector.disabled = true;
    else selector.disabled = false;
    console.error(error);
  }
}

async function main() {
  try {
    const response = await fetch(DATA_URL);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const rows = parseCsv(await response.text());
    if (rows.length !== 19 || rows[0].year !== 2007 || rows.at(-1).year !== 2025) {
      throw new Error("The annual series does not contain all expected years");
    }
    fillTable(rows);
    if (typeof vegaEmbed !== "function") throw new Error("Vega-Lite could not be loaded");
    await Promise.all([
      renderChart("#chart-cases", "Notificaciones por año", casesSpec(rows)),
      renderChart("#chart-rates", "Tasa anual de notificación", ratesSpec(rows)),
    ]);
  } catch (error) {
    for (const id of ["#chart-cases", "#chart-rates"]) {
      const chart = document.querySelector(id);
      if (!chart.querySelector("svg")) chart.textContent = `No se pudieron cargar los gráficos: ${error.message}`;
    }
    const body = document.querySelector("#annual-table");
    if (body.textContent.includes("Cargando")) body.textContent = "No se pudo cargar la tabla de datos.";
    console.error(error);
  }
}

main();
loadWeeklyCharts();
loadAgeCharts();
