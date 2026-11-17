"use strict";

const CLIMATE_MAP_GEOMETRY_URL = "data_processed/cartografia/municipal_boundaries_dane.geojson";
const CLIMATE_MAP_DATA_DIR = "data_processed/heterogeneidad_espacial/climate_map";
const CLIMATE_MAP_PERIODS = ["2007-2014", "2015-2019", "2020-2021", "2022-2025"];
const CLIMATE_MAP_YEARS = Array.from({ length: 19 }, (_, index) => String(2007 + index));
const CLIMATE_MAP_MISSING_COLOR = "#d1d5db";
const CLIMATE_MAP_VARIABLES = {
  precip_chirps: {
    label: "Precipitación CHIRPS (mm/semana)",
    absolute: ["#ffffd9", "#edf8b1", "#c7e9b4", "#7fcdbb", "#41b6c4", "#1d91c0", "#225ea8", "#253494", "#081d58"],
    anomaly: ["#543005", "#8c510a", "#bf812d", "#dfc27d", "#f6e8c3", "#f5f5f5", "#c7eae5", "#80cdc1", "#35978f", "#01665e", "#003c30"],
  },
  precip_era5: {
    label: "Precipitación ERA5 (mm/semana)",
    absolute: ["#ffffd9", "#edf8b1", "#c7e9b4", "#7fcdbb", "#41b6c4", "#1d91c0", "#225ea8", "#253494", "#081d58"],
    anomaly: ["#543005", "#8c510a", "#bf812d", "#dfc27d", "#f6e8c3", "#f5f5f5", "#c7eae5", "#80cdc1", "#35978f", "#01665e", "#003c30"],
  },
  spec_humidity_era5: {
    label: "Humedad específica ERA5 (g/kg)",
    absolute: ["#f7fcf0", "#e0f3db", "#ccebc5", "#a8ddb5", "#7bccc4", "#4eb3d3", "#2b8cbe", "#0868ac", "#084081"],
    anomaly: ["#543005", "#8c510a", "#bf812d", "#dfc27d", "#f6e8c3", "#f5f5f5", "#c7eae5", "#80cdc1", "#35978f", "#01665e", "#003c30"],
  },
  rel_humidity_era5: {
    label: "Humedad relativa ERA5 (%)",
    absolute: ["#f7fcfd", "#e0ecf4", "#bfd3e6", "#9ebcda", "#8c96c6", "#8c6bb1", "#88419d", "#810f7c", "#4d004b"],
    anomaly: ["#543005", "#8c510a", "#bf812d", "#dfc27d", "#f6e8c3", "#f5f5f5", "#c7eae5", "#80cdc1", "#35978f", "#01665e", "#003c30"],
  },
  temp_era5: {
    label: "Temperatura ERA5 (°C)",
    absolute: ["#ffffcc", "#ffeda0", "#fed976", "#feb24c", "#fd8d3c", "#fc4e2a", "#e31a1c", "#bd0026", "#800026"],
    anomaly: ["#053061", "#2166ac", "#4393c3", "#92c5de", "#d1e5f0", "#f7f7f7", "#fddbc7", "#f4a582", "#d6604d", "#b2182b", "#67001f"],
  },
};
const CLIMATE_MAP_FORMAT = new Intl.NumberFormat("es-CO", {
  minimumFractionDigits: 1, maximumFractionDigits: 1,
});
const CLIMATE_MAP_PERCENT = new Intl.NumberFormat("es-CO", {
  maximumFractionDigits: 0,
});

function parseClimateMapPayload(payload, variable) {
  const expectedColumns = ["code", "horizon", "valid_weeks", "total_weeks", "mean_value",
    "baseline_2007_2019", "anomaly"];
  if (payload.schema_version !== 1 || payload.variable !== variable ||
      payload.baseline_horizon !== "2007-2019" ||
      JSON.stringify(payload.columns) !== JSON.stringify(expectedColumns) ||
      !Array.isArray(payload.rows) || !payload.scale_bounds) {
    throw new Error("El archivo climático tiene un esquema inesperado");
  }
  const byHorizon = new Map();
  for (const row of payload.rows) {
    if (!byHorizon.has(row[1])) byHorizon.set(row[1], new Map());
    byHorizon.get(row[1]).set(row[0], row);
  }
  for (const horizon of [...CLIMATE_MAP_PERIODS, ...CLIMATE_MAP_YEARS]) {
    if (!byHorizon.has(horizon)) throw new Error("Falta un período climático");
  }
  return { ...payload, byHorizon };
}

function interpolateClimateColor(palette, fraction) {
  const position = Math.max(0, Math.min(1, fraction)) * (palette.length - 1);
  const lower = Math.floor(position);
  const upper = Math.min(palette.length - 1, lower + 1);
  const share = position - lower;
  const rgb = [1, 3, 5].map((offset) => {
    const start = parseInt(palette[lower].slice(offset, offset + 2), 16);
    const end = parseInt(palette[upper].slice(offset, offset + 2), 16);
    return Math.round(start + (end - start) * share).toString(16).padStart(2, "0");
  });
  return `#${rgb.join("")}`;
}

function climateMapValue(row, dataset, mode) {
  if (!row || row[3] === 0 || row[2] / row[3] < dataset.minimum_coverage) return null;
  return mode === "absolute" ? row[4] : row[6];
}

function climateMapColor(row, dataset, variable, mode) {
  const value = climateMapValue(row, dataset, mode);
  if (value === null) return CLIMATE_MAP_MISSING_COLOR;
  const [minimum, maximum] = dataset.scale_bounds[mode];
  const fraction = (value - minimum) / (maximum - minimum);
  return interpolateClimateColor(CLIMATE_MAP_VARIABLES[variable][mode], fraction);
}

function climateMapTooltip(feature, row, dataset, mode) {
  const container = document.createElement("div");
  const name = document.createElement("strong");
  name.textContent = `${feature.properties.name} · ${feature.properties.department} (${feature.properties.code})`;
  const valueLine = document.createElement("div");
  const coverageLine = document.createElement("div");
  const value = climateMapValue(row, dataset, mode);
  if (!row) {
    valueLine.textContent = "Sin datos climáticos para esta entidad";
    coverageLine.textContent = "Semanas incluidas: 0 de 0";
  } else {
    if (row[3] === 0 || row[2] / row[3] < dataset.minimum_coverage) {
      valueLine.textContent = "Cobertura semanal insuficiente";
    } else if (value === null) {
      valueLine.textContent = "Sin línea base válida en 2007–2019";
    } else {
      const sign = mode === "anomaly" && value > 0 ? "+" : "";
      valueLine.textContent = `${sign}${CLIMATE_MAP_FORMAT.format(value)} ${dataset.unit}` +
        (mode === "anomaly" ? " vs. Línea base (2007–2019)" : "");
    }
    coverageLine.textContent = `Semanas incluidas: ${row[2]} de ${row[3]} ` +
      `(${CLIMATE_MAP_PERCENT.format(100 * row[2] / row[3])} %)`;
  }
  container.append(name, valueLine, coverageLine);
  return container;
}

function renderClimateMapLegend(element, dataset, variable, mode) {
  const palette = CLIMATE_MAP_VARIABLES[variable][mode];
  const [minimum, maximum] = dataset.scale_bounds[mode];
  const title = document.createElement("strong");
  title.textContent = mode === "absolute" ? `Promedio semanal · ${dataset.unit}` :
    "Anomalía vs. Línea base (2007–2019)";
  const unit = document.createElement("div");
  unit.textContent = `Unidad: ${dataset.unit}`;
  const gradient = document.createElement("div");
  gradient.className = "climate-map-gradient";
  gradient.style.background = `linear-gradient(to right, ${palette.join(", ")})`;
  const labels = document.createElement("div");
  labels.className = "climate-map-legend-labels";
  const bounds = mode === "absolute" ?
    [`≤ ${CLIMATE_MAP_FORMAT.format(minimum)}`, `≥ ${CLIMATE_MAP_FORMAT.format(maximum)}`] :
    [`≤ −${CLIMATE_MAP_FORMAT.format(Math.abs(minimum))}`, "0", `≥ +${CLIMATE_MAP_FORMAT.format(maximum)}`];
  for (const bound of bounds) {
    const item = document.createElement("span");
    item.textContent = bound;
    labels.append(item);
  }
  const missing = document.createElement("div");
  missing.className = "climate-map-legend-missing";
  const swatch = document.createElement("span");
  swatch.className = "climate-map-missing-swatch";
  missing.append(swatch, document.createTextNode("Cobertura semanal insuficiente o sin datos"));
  element.replaceChildren(title, unit, gradient, labels, missing);
}

async function initClimateMap() {
  const variableInput = document.querySelector("#climate-map-variable");
  const horizonTypeInput = document.querySelector("#climate-map-horizon-type");
  const periodButtons = document.querySelector("#climate-map-periods");
  const yearControl = document.querySelector("#climate-map-year-control");
  const yearInput = document.querySelector("#climate-map-year");
  const modeButtons = document.querySelector("#climate-map-modes");
  const playButton = document.querySelector("#climate-map-play");
  const timeline = document.querySelector("#climate-map-timeline");
  const frameOutput = document.querySelector("#climate-map-frame");
  const speedInput = document.querySelector("#climate-map-speed");
  const legend = document.querySelector("#climate-map-legend");
  const status = document.querySelector("#climate-map-status");
  const cache = new Map();
  const layers = new Map();
  const state = {
    variable: "precip_chirps", horizonType: "period", horizon: "2015-2019",
    mode: "absolute", dataset: null, timer: null, requestVersion: 0,
  };

  for (const year of CLIMATE_MAP_YEARS) {
    const option = document.createElement("option");
    option.value = year;
    option.textContent = year;
    yearInput.append(option);
  }

  function frames() {
    return state.horizonType === "period" ? CLIMATE_MAP_PERIODS : CLIMATE_MAP_YEARS;
  }

  function syncControls() {
    variableInput.value = state.variable;
    horizonTypeInput.value = state.horizonType;
    periodButtons.hidden = state.horizonType !== "period";
    yearControl.hidden = state.horizonType !== "year";
    yearInput.value = state.horizonType === "year" ? state.horizon : "2015";
    for (const button of periodButtons.querySelectorAll("button")) {
      button.setAttribute("aria-pressed", String(button.dataset.horizon === state.horizon));
    }
    for (const button of modeButtons.querySelectorAll("button")) {
      button.setAttribute("aria-pressed", String(button.dataset.mode === state.mode));
    }
    timeline.max = String(frames().length - 1);
    timeline.value = String(frames().indexOf(state.horizon));
    frameOutput.textContent = state.horizon.replace("-", "–");
  }

  function render() {
    if (!state.dataset || layers.size === 0) return;
    const records = state.dataset.byHorizon.get(state.horizon);
    let colored = 0;
    for (const [code, layer] of layers) {
      const row = records.get(code);
      if (climateMapValue(row, state.dataset, state.mode) !== null) colored += 1;
      layer.setStyle({ fillColor: climateMapColor(row, state.dataset, state.variable, state.mode) });
    }
    renderClimateMapLegend(legend, state.dataset, state.variable, state.mode);
    status.textContent = `${CLIMATE_MAP_VARIABLES[state.variable].label} · ${state.horizon.replace("-", "–")} · ` +
      `${colored} municipios con valor visible; ${layers.size - colored} entidades en gris.`;
    syncControls();
  }

  function stopPlayback() {
    if (state.timer !== null) clearInterval(state.timer);
    state.timer = null;
    playButton.textContent = "▶ Reproducir";
    playButton.setAttribute("aria-label", "Reproducir animación");
  }

  function startPlayback() {
    if (state.timer !== null) return;
    const delay = 800 / Number(speedInput.value);
    state.timer = setInterval(() => {
      const sequence = frames();
      state.horizon = sequence[(sequence.indexOf(state.horizon) + 1) % sequence.length];
      render();
    }, delay);
    playButton.textContent = "⏸ Pausar";
    playButton.setAttribute("aria-label", "Pausar animación");
  }

  async function loadVariable(variable) {
    if (!cache.has(variable)) {
      const url = `${CLIMATE_MAP_DATA_DIR}/${variable}.json?v=20261029-baseline-2007-2019`;
      const pending = fetch(url).then((response) => {
        if (!response.ok) throw new Error("No se pudieron cargar los promedios climáticos");
        return response.json();
      }).then((payload) => parseClimateMapPayload(payload, variable));
      cache.set(variable, pending);
      pending.catch(() => cache.delete(variable));
    }
    return cache.get(variable);
  }

  function attachControls() {
    variableInput.addEventListener("change", async () => {
      stopPlayback();
      const variable = variableInput.value;
      const version = ++state.requestVersion;
      status.textContent = "Cargando variable climática…";
      try {
        const dataset = await loadVariable(variable);
        if (version !== state.requestVersion) return;
        state.variable = variable;
        state.dataset = dataset;
        render();
      } catch (error) {
        if (version === state.requestVersion) {
          variableInput.value = state.variable;
          status.textContent = error.message;
        }
      }
    });
    horizonTypeInput.addEventListener("change", () => {
      stopPlayback();
      state.horizonType = horizonTypeInput.value;
      state.horizon = state.horizonType === "period" ? "2015-2019" : "2015";
      render();
    });
    periodButtons.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-horizon]");
      if (!button) return;
      stopPlayback();
      state.horizon = button.dataset.horizon;
      render();
    });
    yearInput.addEventListener("change", () => {
      stopPlayback();
      state.horizon = yearInput.value;
      render();
    });
    modeButtons.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-mode]");
      if (!button) return;
      state.mode = button.dataset.mode;
      render();
    });
    timeline.addEventListener("input", () => {
      stopPlayback();
      state.horizon = frames()[Number(timeline.value)];
      render();
    });
    playButton.addEventListener("click", () => {
      if (state.timer === null) startPlayback();
      else stopPlayback();
    });
    speedInput.addEventListener("change", () => {
      if (state.timer !== null) {
        stopPlayback();
        startPlayback();
      }
    });
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) stopPlayback();
    });
    window.addEventListener("pagehide", stopPlayback);
  }

  if (typeof L === "undefined") throw new Error("No se pudo cargar Leaflet");
  const [geometryResponse, dataset] = await Promise.all([
    fetch(CLIMATE_MAP_GEOMETRY_URL), loadVariable(state.variable),
  ]);
  if (!geometryResponse.ok) throw new Error("No se pudo cargar la geometría municipal");
  const geometry = await geometryResponse.json();
  if (geometry.type !== "FeatureCollection" || geometry.features.length < 1100) {
    throw new Error("La geometría municipal está incompleta");
  }
  state.dataset = dataset;
  const map = L.map("climate-map", { scrollWheelZoom: false, preferCanvas: false });
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(map);
  const polygons = L.geoJSON(geometry, {
    style: () => ({ color: "#526b74", weight: 0.45, fillOpacity: 0.86,
      fillColor: CLIMATE_MAP_MISSING_COLOR, className: "climate-map-polygon" }),
    onEachFeature(feature, layer) {
      layers.set(feature.properties.code, layer);
      layer.bindTooltip(() => climateMapTooltip(feature,
        state.dataset.byHorizon.get(state.horizon).get(feature.properties.code),
        state.dataset, state.mode), { sticky: true, direction: "top" });
      layer.on("mouseover", () => layer.setStyle({ color: "#173042", weight: 1.7 }));
      layer.on("mouseout", () => layer.setStyle({ color: "#526b74", weight: 0.45 }));
    },
  }).addTo(map);
  map.fitBounds(polygons.getBounds(), { padding: [12, 12] });
  attachControls();
  render();
}

document.addEventListener("DOMContentLoaded", () => {
  initClimateMap().catch((error) => {
    document.querySelector("#climate-map-status").textContent = error.message;
  });
});
