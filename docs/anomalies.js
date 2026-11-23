"use strict";

const ANOMALY_URL = "data_processed/anomalias_cobertura/age_standardized_sir_coverage_periods.csv?v=20261122-annual-cap-100";
const ANOMALY_BOUNDARIES_URL = "data_processed/cartografia/municipal_boundaries_dane.geojson";
const anomalyNumber = new Intl.NumberFormat("es-CO");
const anomalyDecimal = new Intl.NumberFormat("es-CO", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});
const ANOMALY_CLASSES = {
  low_low: { label: "Cobertura < p_c · SIR < 1", color: "#468ba3" },
  low_high: { label: "Cobertura < p_c · SIR ≥ 1", color: "#c0443d" },
  high_low: { label: "Cobertura ≥ p_c · SIR < 1", color: "#287e5c" },
  high_high: { label: "Cobertura ≥ p_c · SIR ≥ 1", color: "#8054a4" },
  missing: { label: "Sin cobertura válida", color: "#e1e5e7" },
  unclassified: { label: "Pendiente de p_c válido", color: "#b5c7ce" },
};
const ANOMALY_CLASS_ORDER = [
  "low_low", "low_high", "high_low", "high_high", "missing",
  "unclassified",
];

function parseAnomalyCsv(source) {
  const lines = source.trim().split(/\r?\n/);
  const headers = lines.shift().split(",");
  return lines.map((line) => {
    const values = line.split(",");
    if (values.length !== headers.length) {
      throw new Error("CSV municipal incompleto");
    }
    return Object.fromEntries(headers.map((header, index) => [header, values[index]]));
  });
}

function getAnomalyState(rows) {
  const period = document.querySelector("#anomaly-period").value;
  const dose = document.querySelector("#anomaly-dose").value;
  const thresholdInput = document.querySelector("#anomaly-pc");
  const threshold = Number(thresholdInput.value);
  const thresholdValid = thresholdInput.value !== ""
    && Number.isFinite(threshold) && threshold > 0 && threshold <= 100;
  const selected = rows.filter((row) => row.period === period);
  const coverageField = "coverage_" + dose + "_valid_mean";
  const rawCoverageField = "coverage_" + dose + "_mean";
  const validYearsField = "coverage_" + dose + "_valid_years";
  const above100Field = "coverage_" + dose + "_above_100_years";
  const eligible = selected.filter((row) =>
    Number(row[validYearsField]) === Number(row.coverage_years_expected)
    && row[coverageField] !== ""
    && Number.isFinite(Number(row[coverageField]))
    && Number.isFinite(Number(row.sir_period)));
  const over100 = selected.filter((row) => Number(row[above100Field]) > 0);
  const missing = selected.filter((row) =>
    !eligible.includes(row));
  return {
    period, dose, threshold, thresholdValid, selected, eligible, over100, missing,
    coverageField, rawCoverageField, validYearsField, above100Field,
    byCode: new Map(selected.map((row) => [row.code, row])),
  };
}

// Compare in units of 10^-8 percentage points, as Python and the CSV do.
function anomalyCoverageHigh(value, threshold) {
  return Math.round(Number(value) * 1e8) >= Math.round(Number(threshold) * 1e8);
}

function anomalyClass(row, state) {
  if (!row) return "missing";
  if (Number(row[state.validYearsField]) !== Number(row.coverage_years_expected)) {
    return "missing";
  }
  if (!state.thresholdValid) return "unclassified";
  const coverageHigh = anomalyCoverageHigh(row[state.coverageField], state.threshold);
  const sirHigh = Number(row.sir_period) >= 1;
  return (coverageHigh ? "high" : "low") + "_" +
    (sirHigh ? "high" : "low");
}

function renderAnomalyMatrix(state) {
  const body = document.querySelector("#anomaly-quadrants");
  const status = document.querySelector("#anomaly-status");
  status.textContent = anomalyNumber.format(state.selected.length) + " municipios con SIR; " +
    anomalyNumber.format(state.eligible.length) + " con cobertura completa (tope anual de 100 %); " +
    anomalyNumber.format(state.over100.length) + " con algún valor anual ajustado a 100 %; " +
    anomalyNumber.format(state.missing.length) + " por datos faltantes u otros valores inválidos.";

  if (!state.thresholdValid) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 3;
    cell.textContent = "Introduce un p_c de referencia entre 0 y 100 % para calcular la matriz.";
    row.append(cell);
    body.replaceChildren(row);
    return;
  }

  const counts = [[0, 0], [0, 0]];
  for (const row of state.eligible) {
    const coverageHigh = anomalyCoverageHigh(row[state.coverageField], state.threshold) ? 1 : 0;
    const sirHigh = Number(row.sir_period) >= 1 ? 1 : 0;
    counts[coverageHigh][sirHigh] += 1;
  }
  const fragment = document.createDocumentFragment();
  for (const coverageHigh of [0, 1]) {
    const tr = document.createElement("tr");
    for (const value of [
      coverageHigh ? "Cobertura ≥ p_c" : "Cobertura < p_c",
      anomalyNumber.format(counts[coverageHigh][0]),
      anomalyNumber.format(counts[coverageHigh][1]),
    ]) {
      const td = document.createElement("td");
      td.textContent = value;
      tr.append(td);
    }
    fragment.append(tr);
  }
  body.replaceChildren(fragment);
}

function renderAnomalyLegend(state) {
  const legend = document.querySelector("#anomaly-map-legend");
  const counts = Object.fromEntries(ANOMALY_CLASS_ORDER.map((key) => [key, 0]));
  for (const row of state.selected) counts[anomalyClass(row, state)] += 1;
  const fragment = document.createDocumentFragment();
  for (const key of ANOMALY_CLASS_ORDER) {
    if (key === "unclassified" && counts[key] === 0) continue;
    const item = document.createElement("span");
    const swatch = document.createElement("i");
    swatch.className = "lisa-swatch";
    swatch.style.backgroundColor = ANOMALY_CLASSES[key].color;
    item.append(swatch, document.createTextNode(
      ANOMALY_CLASSES[key].label + " (" + anomalyNumber.format(counts[key]) + ")",
    ));
    fragment.append(item);
  }
  legend.replaceChildren(fragment);
}

function anomalyPopup(feature, row, state) {
  const container = document.createElement("div");
  const title = document.createElement("strong");
  title.textContent = feature.properties.name + " (" + feature.properties.code + ")";
  container.append(title);
  const coverage = row[state.rawCoverageField] === ""
    ? "sin dato" : anomalyDecimal.format(Number(row[state.rawCoverageField])) + " %";
  const lines = [
    feature.properties.department + " · " + state.period,
    "Casos observados (edad conocida): " +
      anomalyNumber.format(Number(row.observed_known_age)),
    "Casos esperados (tasas del período): " +
      anomalyDecimal.format(Number(row.expected_period)),
    "SIR ajustado por edad: " + anomalyDecimal.format(Number(row.sir_period)),
    "Cobertura media original: " + coverage,
    "Cobertura media con tope anual: " + (row[state.coverageField] === "" ? "sin dato" : anomalyDecimal.format(Number(row[state.coverageField])) + " %"),
    "Años con cobertura > 100 %: " + row[state.above100Field],
    "Clasificación: " + ANOMALY_CLASSES[anomalyClass(row, state)].label,
  ];
  for (const line of lines) {
    const element = document.createElement("div");
    element.textContent = line;
    container.append(element);
  }
  return container;
}

function createAnomalyMap(boundaries, currentState) {
  const map = L.map("anomaly-map", { scrollWheelZoom: false, preferCanvas: true });
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(map);
  const style = (feature) => ({
    color: "#617984",
    weight: 0.35,
    fillOpacity: 0.88,
    fillColor: ANOMALY_CLASSES[
      anomalyClass(currentState.value.byCode.get(feature.properties.code),
        currentState.value)
    ].color,
  });
  const layer = L.geoJSON(boundaries, {
    filter: (feature) => feature.properties.kind === "MUNICIPIO"
      && currentState.value.byCode.has(feature.properties.code),
    style,
    onEachFeature(feature, polygon) {
      polygon.bindPopup(() => anomalyPopup(
        feature,
        currentState.value.byCode.get(feature.properties.code),
        currentState.value,
      ));
      polygon.on("mouseover", () => polygon.setStyle({ weight: 1.8, color: "#173042" }));
      polygon.on("mouseout", () => layer.resetStyle(polygon));
    },
  }).addTo(map);
  if (layer.getLayers().length !== 1102) {
    throw new Error("El mapa no coincide con los 1.102 municipios del panel");
  }
  map.fitBounds(layer.getBounds(), { padding: [10, 10] });
  return () => layer.setStyle(style);
}

function anomalyScatterSpec(state, names) {
  const validPoints = state.eligible.map((row) => ({
    municipality: names.get(row.code) || row.code,
    code: row.code,
    coverage: Number(row[state.coverageField]),
    sir: Number(row.sir_period),
    group: anomalyClass(row, state),
    raw_coverage: Number(row[state.rawCoverageField]),
    capped_years: Number(row[state.above100Field]),
    symbol: "Cobertura con tope anual",
  }));
  const points = validPoints;
  function paddedDomain(values) {
    const minimum = Math.min(...values);
    const maximum = Math.max(...values);
    const padding = Math.max((maximum - minimum) * 0.05, 0.01);
    return [Math.max(0, minimum - padding), maximum + padding];
  }
  const xDomain = paddedDomain([...points.map((point) => point.coverage), state.threshold]);
  const yDomain = paddedDomain([...points.map((point) => point.sir), 1]);
  const x = {
    field: "coverage", type: "quantitative",
    title: "Cobertura media con tope anual de 100 % (%)",
    scale: { domain: xDomain, nice: false, zero: false },
  };
  const y = {
    field: "sir", type: "quantitative", title: "SIR ajustado por edad",
    scale: { domain: yDomain, nice: false, zero: false },
  };
  return {
    $schema: "https://vega.github.io/schema/vega-lite/v6.json",
    width: "container",
    height: 380,
    config: { view: { stroke: null }, axis: { labelFontSize: 12, titleFontSize: 13 } },
    layer: [
      {
        data: { values: [{ coverage: state.threshold }] },
        mark: { type: "rule", color: "#735234", strokeDash: [5, 4], strokeWidth: 1.4 },
        encoding: { x },
      },
      {
        data: { values: [{ sir: 1 }] },
        mark: { type: "rule", color: "#735234", strokeDash: [5, 4], strokeWidth: 1.4 },
        encoding: { y },
      },
      {
        data: { values: points },
        mark: { type: "point", filled: true, size: 57, opacity: 0.72,
          stroke: "white", strokeWidth: 0.3 },
        encoding: {
          x, y,
          color: {
            field: "group", type: "nominal", legend: null,
            scale: {
              domain: ANOMALY_CLASS_ORDER,
              range: ANOMALY_CLASS_ORDER.map((key) => ANOMALY_CLASSES[key].color),
            },
          },
          tooltip: [
            { field: "municipality", type: "nominal", title: "Municipio" },
            { field: "code", type: "nominal", title: "Código" },
            { field: "coverage", type: "quantitative", title: "Cobertura media (%)", format: ".2f" },
            { field: "sir", type: "quantitative", title: "SIR", format: ".3f" },
            { field: "raw_coverage", type: "quantitative", title: "Media original (%)", format: ".2f" },
            { field: "capped_years", type: "quantitative", title: "Años ajustados a 100 %" },
          ],
        },
      },
      {
        data: { values: validPoints },
        transform: [{ loess: "sir", on: "coverage", bandwidth: 0.3 }],
        mark: { type: "line", color: "#183c4b", strokeWidth: 3 },
        encoding: { x, y },
      },
    ],
  };
}

async function renderAnomalyScatter(state, names) {
  const status = document.querySelector("#anomaly-scatter-status");
  const chart = document.querySelector("#anomaly-scatter");
  if (!state.thresholdValid) {
    chart.replaceChildren();
    status.textContent = "Introduce un umbral de referencia válido para ver el diagrama.";
    return;
  }
  if (typeof vegaEmbed !== "function") {
    status.textContent = "No se pudo cargar Vega-Lite para el diagrama.";
    return;
  }
  try {
    const spec = anomalyScatterSpec(state, names);
    await vegaEmbed(chart, spec, { actions: false, renderer: "canvas" });
    status.textContent = anomalyNumber.format(state.eligible.length) +
      " municipios con cobertura media tras aplicar el tope anual de 100 %. LOESS usa todos los puntos.";
  } catch (error) {
    status.textContent = "No se pudo mostrar el diagrama: " + error.message;
  }
}

async function loadAnomalyMatrix() {
  const status = document.querySelector("#anomaly-status");
  const mapStatus = document.querySelector("#anomaly-map-status");
  try {
    const [response, boundariesResponse] = await Promise.all([
      fetch(ANOMALY_URL), fetch(ANOMALY_BOUNDARIES_URL),
    ]);
    if (!response.ok) throw new Error("No se pudo descargar el cruce municipal");
    if (!boundariesResponse.ok) throw new Error("No se pudo descargar la cartografía");
    const [csv, boundaries] = await Promise.all([
      response.text(), boundariesResponse.json(),
    ]);
    const rows = parseAnomalyCsv(csv);
    if (rows.length !== 1102 * 3) throw new Error("El panel municipal está incompleto");
    const keys = new Set(rows.map((row) => row.period + ":" + row.code));
    if (keys.size !== rows.length) throw new Error("Hay municipios duplicados por período");
    if (boundaries.type !== "FeatureCollection") throw new Error("Cartografía incompleta");
    const names = new Map(boundaries.features.map((feature) => [
      feature.properties.code, feature.properties.name,
    ]));
    const currentState = { value: getAnomalyState(rows) };
    let updateMap = () => {};
    let mapReady = false;
    try {
      if (typeof L === "undefined") throw new Error("Leaflet no está disponible");
      updateMap = createAnomalyMap(boundaries, currentState);
      mapReady = true;
    } catch (error) {
      mapStatus.textContent = "No se pudo mostrar el mapa: " + error.message;
    }
    let chartTimer;
    const update = () => {
      currentState.value = getAnomalyState(rows);
      renderAnomalyMatrix(currentState.value);
      renderAnomalyLegend(currentState.value);
      updateMap();
      if (mapReady) {
        mapStatus.textContent = currentState.value.thresholdValid
          ? "Mapa de los 1.102 municipios del panel. Las categorías y recuentos " +
            "cambian con los controles de arriba."
          : "Introduce un umbral de referencia válido para clasificar los cuadrantes.";
      }
      clearTimeout(chartTimer);
      chartTimer = setTimeout(() => renderAnomalyScatter(currentState.value, names), 120);
    };
    const periodSelect = document.querySelector("#anomaly-period");
    const doseSelect = document.querySelector("#anomaly-dose");
    const boosterOption = doseSelect.querySelector('option[value="booster"]');
    periodSelect.addEventListener("change", () => {
      boosterOption.disabled = periodSelect.value === "2015-2019";
      if (boosterOption.disabled && doseSelect.value === "booster") {
        doseSelect.value = "first_dose";
      }
      update();
    });
    doseSelect.addEventListener("change", update);
    document.querySelector("#anomaly-pc").addEventListener(
      "input", update,
    );
    update();
  } catch (error) {
    status.textContent = "No se pudo mostrar la matriz: " + error.message;
    mapStatus.textContent = "No se pudo mostrar el mapa: " + error.message;
    document.querySelector("#anomaly-scatter-status").textContent =
      "No se pudo mostrar el diagrama: " + error.message;
  }
}

loadAnomalyMatrix();
