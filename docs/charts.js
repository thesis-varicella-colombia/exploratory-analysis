"use strict";

const DATA_URL = "data_processed/annual_series_2007_2023.csv";
const NUMBER = new Intl.NumberFormat("es-CO");
const RATE = new Intl.NumberFormat("es-CO", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const SCHEMA = "https://vega.github.io/schema/vega-lite/v6.json";
const CHART_WIDTH = window.matchMedia("(max-width: 700px)").matches ? 650 : "container";

function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/);
  const columns = lines.shift().split(",");
  return lines.map((line) => {
    const values = line.split(",");
    const row = Object.fromEntries(columns.map((column, index) => [column, values[index]]));
    return {
      year: Number(row.year),
      notifications: Number(row.notifications),
      reporting_entities: Number(row.reporting_entities),
      population: Number(row.population),
      notification_rate_per_100k: Number(row.notification_rate_per_100k),
      official_2007_cases: row.official_2007_cases ? Number(row.official_2007_cases) : null,
    };
  });
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

function casesSpec(rows) {
  return {
    ...sharedSpec(rows, "notifications", "Notificaciones"),
    layer: [
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
            { field: "official_2007_cases", title: "Protocolo: casos", format: ",d" },
          ],
        },
      },
    ],
  };
}

function ratesSpec(rows) {
  return {
    ...sharedSpec(rows, "notification_rate_per_100k", "Notificaciones por 100.000 habitantes"),
    layer: [
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
    ],
  };
}

async function main() {
  try {
    const response = await fetch(DATA_URL);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const rows = parseCsv(await response.text());
    if (rows.length !== 17 || rows[0].year !== 2007 || rows.at(-1).year !== 2023) {
      throw new Error("The annual series does not contain all expected years");
    }
    fillTable(rows);
    document.querySelector("#count-2007").textContent = NUMBER.format(rows[0].notifications);
    document.querySelector("#official-2007").textContent = NUMBER.format(rows[0].official_2007_cases);
    document.querySelector("#entities-2007").textContent = NUMBER.format(rows[0].reporting_entities);
    if (typeof vegaEmbed !== "function") throw new Error("Vega-Lite could not be loaded");
    const options = { renderer: "svg", actions: { export: true, source: false, compiled: false, editor: false } };
    await Promise.all([
      vegaEmbed("#chart-cases", casesSpec(rows), options),
      vegaEmbed("#chart-rates", ratesSpec(rows), options),
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
