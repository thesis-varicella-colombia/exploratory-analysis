"use strict";

const MORAN_GLOBAL_URL = "data_processed/heterogeneidad_espacial/moran_global_periods.csv?v=20261102-mapiripana-population";
const MORAN_LOCAL_URL = "data_processed/heterogeneidad_espacial/moran_lisa_periods.csv?v=20261102-mapiripana-population";
const MORAN_BOUNDARIES_URL = "data_processed/cartografia/municipal_boundaries_dane.geojson";
const MORAN_PERIODS = [
  ["2008-2014", "2008–2014 · prevacunal"],
  ["2015-2019", "2015–2019 · transición / dosis única"],
  ["2020-2021", "2020–2021 · pandemia"],
  ["2022-2025", "2022–2025 · etapa posterior al refuerzo"],
];
const MORAN_COLORS = {
  HH: "#b43c32",
  LL: "#236a9b",
  HL: "#df9d32",
  LH: "#8660a5",
  NS: "#e0e6e8",
};
const MORAN_NUMBER = new Intl.NumberFormat("es-CO");
const MORAN_DECIMAL = new Intl.NumberFormat("es-CO", {
  minimumFractionDigits: 4,
  maximumFractionDigits: 4,
});
const MORAN_RATE = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 1 });

function parseMoranCsv(source) {
  const lines = source.trim().split(/\r?\n/);
  const fields = lines.shift().split(",");
  return lines.map((line) => {
    const values = line.split(",");
    return Object.fromEntries(fields.map((field, index) => [field, values[index]]));
  });
}

function moranPopup(feature, result, periodLabel) {
  const container = document.createElement("div");
  const title = document.createElement("strong");
  title.textContent = feature.properties.name + " (" + feature.properties.code + ")";
  container.append(title);
  for (const line of [
    feature.properties.department + " · " + periodLabel,
    "Tasa: " + MORAN_RATE.format(Number(result.rate_per_100k)) + " por 100.000",
    "LISA: " + result.cluster_nominal + " (p = " +
      MORAN_DECIMAL.format(Number(result.p_two_sided)) + ")",
    "Valor q de Benjamini–Hochberg: " +
      MORAN_DECIMAL.format(Number(result.q_bh)),
    "Clúster que resiste el ajuste: " + result.cluster_fdr,
  ]) {
    const row = document.createElement("div");
    row.textContent = line;
    container.append(row);
  }
  return container;
}

function fillMoranTable(rows) {
  const body = document.querySelector("#moran-global-table");
  const fragment = document.createDocumentFragment();
  for (const [period, label] of MORAN_PERIODS) {
    const row = rows.find((item) => item.period === period);
    if (!row) throw new Error("Falta el periodo de Moran " + period);
    const tr = document.createElement("tr");
    for (const value of [
      label,
      MORAN_NUMBER.format(Number(row.municipalities)),
      MORAN_DECIMAL.format(Number(row.global_i)),
      MORAN_DECIMAL.format(Number(row.p_positive)),
      row.hh_nominal + " / " + row.ll_nominal,
      row.hh_fdr + " / " + row.ll_fdr,
    ]) {
      const td = document.createElement("td");
      td.textContent = value;
      tr.append(td);
    }
    fragment.append(tr);
  }
  body.replaceChildren(fragment);
}

function renderMoranMap(period, label, boundaries, results) {
  const filter = document.querySelector("#moran-map-filter");
  const map = L.map("moran-map-" + period, {
    scrollWheelZoom: false,
    preferCanvas: true,
  });
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(map);
  const style = (feature) => ({
    color: "#667b84",
    weight: 0.35,
    fillOpacity: 0.85,
    fillColor: MORAN_COLORS[results.get(feature.properties.code)[filter.value]],
  });
  const municipalities = L.geoJSON(boundaries, {
    filter: (feature) => feature.properties.kind === "MUNICIPIO"
      && results.has(feature.properties.code),
    style,
    onEachFeature(feature, layer) {
      layer.bindPopup(() => moranPopup(
        feature, results.get(feature.properties.code), label,
      ));
      layer.on("mouseover", () => layer.setStyle({ weight: 1.8, color: "#173042" }));
      layer.on("mouseout", () => municipalities.resetStyle(layer));
    },
  }).addTo(map);
  map.fitBounds(municipalities.getBounds(), { padding: [10, 10] });
  return () => municipalities.setStyle(style);
}

async function loadMoranLisa() {
  const status = document.querySelector("#moran-lisa-status");
  try {
    if (typeof L === "undefined") throw new Error("No se pudo cargar Leaflet");
    const responses = await Promise.all([
      fetch(MORAN_GLOBAL_URL),
      fetch(MORAN_LOCAL_URL),
      fetch(MORAN_BOUNDARIES_URL),
    ]);
    if (responses.some((response) => !response.ok)) {
      throw new Error("No se pudieron cargar los resultados de Moran/LISA");
    }
    const [globalText, localText, boundaries] = await Promise.all([
      responses[0].text(), responses[1].text(), responses[2].json(),
    ]);
    const globalRows = parseMoranCsv(globalText);
    const localRows = parseMoranCsv(localText);
    if (boundaries.type !== "FeatureCollection") throw new Error("Geometría incompleta");
    const byPeriod = new Map(MORAN_PERIODS.map(([period]) => [period, new Map()]));
    for (const row of localRows) {
      if (byPeriod.has(row.period)) byPeriod.get(row.period).set(row.code, row);
    }
    for (const [period] of MORAN_PERIODS) {
      const expected = Number(globalRows.find((row) => row.period === period)?.municipalities);
      if (!Number.isInteger(expected) || byPeriod.get(period).size !== expected) {
        throw new Error("Datos LISA incompletos para " + period);
      }
    }
    fillMoranTable(globalRows);
    const updates = MORAN_PERIODS.map(([period, label]) =>
      renderMoranMap(period, label, boundaries, byPeriod.get(period)));
    const filter = document.querySelector("#moran-map-filter");
    filter.disabled = false;
    filter.addEventListener("change", () => {
      updates.forEach((update) => update());
      status.textContent = filter.value === "cluster_fdr"
        ? "Mapas con ajuste por comparaciones múltiples. Selecciona un municipio para ver p y q."
        : "Mapas exploratorios sin ajuste. Selecciona un municipio para ver p y q.";
    });
    status.textContent = "Mapas exploratorios sin ajuste. Selecciona un municipio para ver p y q.";
  } catch (error) {
    status.textContent = "No se pudo mostrar Moran/LISA: " + error.message;
  }
}

loadMoranLisa();
