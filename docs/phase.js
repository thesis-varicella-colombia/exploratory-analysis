"use strict";

const PHASE_DATA_URL = "data_processed/estacionalidad/department_phase_2008_2025.csv?v=20261023-notification";
const MUNICIPAL_PHASE_DATA_URL = "data_processed/estacionalidad/municipal_phase_2008_2025.csv?v=20261115";
const PHASE_CORRELATION_URL = "data_processed/estacionalidad/phase_spearman_2008_2025.csv?v=20261023-notification";
const PHASE_PERIODS = [
  { label: "2008–2014", chart: "#chart-phase-2008-2014", color: "#3569b0" },
  { label: "2015–2019", chart: "#chart-phase-2015-2019", color: "#d97736" },
  { label: "2022–2025", chart: "#chart-phase-2022-2025", color: "#197f7a" },
];
function phaseRowsFromCsv(source) {
  return vega.read(source, { type: "csv" }).map((row) => ({
    period: row.period,
    department_code: row.department_code,
    department: row.department,
    territory_code: row.municipality_code || row.department_code,
    territory: row.municipality || row.department,
    dimension: row.municipality_code ? "municipality" : "department",
    latitude: Number(row.latitude),
    peak_week: Number(row.peak_week),
    amplitude_per_100k: Number(row.amplitude_per_100k),
    mean_rate_per_100k: Number(row.mean_rate_per_100k),
    relative_amplitude: row.relative_amplitude === "" ? null : Number(row.relative_amplitude),
    observed_weeks: Number(row.observed_weeks),
  }));
}

function phaseScatterSpec(rows, period) {
  return {
    $schema: SCHEMA,
    width: CHART_WIDTH,
    height: 260,
    background: "transparent",
    data: { name: "phase_scatter_data", values: rows.filter((row) => row.period === period.label) },
    encoding: {
      x: {
        field: "latitude", type: "quantitative", title: "Latitud del centroide (°N)",
        scale: { domain: [-5, 14] }, axis: { gridColor: "#e4ecee", labelColor: "#425c68" },
      },
      y: {
        field: "peak_week", type: "quantitative", title: "Semana del pico",
        scale: { domain: [1, 52] }, axis: { tickMinStep: 4, gridColor: "#e4ecee", labelColor: "#425c68" },
      },
      tooltip: [
        { field: "territory", title: "Territorio" },
        { field: "territory_code", title: "Código" },
        { field: "latitude", title: "Latitud", format: ".2f" },
        { field: "peak_week", title: "Semana del pico" },
        { field: "amplitude_per_100k", title: "Amplitud por 100.000", format: ".2f" },
        { field: "relative_amplitude", title: "Amplitud relativa", format: ".2f" },
      ],
    },
    layer: [
      { transform: [{ filter: "!datum.selected" }],
        mark: { type: "point", filled: true, size: 75, opacity: 0.5, color: period.color } },
      { transform: [{ filter: "datum.selected" }],
        mark: { type: "point", filled: true, size: 300, opacity: 1,
          color: "#ffce51", stroke: "#173042", strokeWidth: 2.5 } },
    ],
    config: { view: { stroke: null }, font: "system-ui, sans-serif" },
  };
}

function initPhaseScatterFilters(departments, municipalities, views, currentSpecs) {
  const controls = document.querySelector("#phase-scatter-filters");
  const level = document.querySelector("#phase-scatter-level");
  const search = document.querySelector("#phase-scatter-territory");
  const options = document.querySelector("#phase-scatter-territory-options");
  const status = document.querySelector("#phase-scatter-status");
  const periodDetails = PHASE_PERIODS.map((period) => document.querySelector(`#phase-detail-${period.label.replace(/[^0-9]/g, "")}`));
  const names = new Map(departments.filter((row) => row.period === PHASE_PERIODS[0].label)
    .map((row) => [row.department_code, row.department]));
  const available = {
    department: [...new Map(departments.map((row) => [row.territory_code, row])).values()],
    municipality: [...new Map(municipalities.map((row) => [row.territory_code, row])).values()],
  };
  let labels = new Map();
  let version = 0;
  let queue = Promise.resolve();
  function refreshOptions() {
    labels = new Map();
    options.replaceChildren();
    for (const row of available[level.value]) {
      const label = level.value === "department"
        ? `${row.territory} (${row.territory_code})`
        : `${row.territory} · ${names.get(row.department_code)} (${row.territory_code})`;
      labels.set(label, row.territory_code);
      const option = document.createElement("option");
      option.value = label;
      options.append(option);
    }
    search.placeholder = level.value === "department" ? "Todos los departamentos" : "Todos los municipios";
  }
  function update() {
    const selectedCode = labels.get(search.value.trim());
    const isSearching = search.value.trim() !== "";
    const rows = level.value === "department" ? departments : municipalities;
    const selected = isSearching && selectedCode !== undefined ? selectedCode : null;
    const current = ++version;
    PHASE_PERIODS.forEach((period, index) => {
      const row = selected === null ? null : rows.find((candidate) =>
        candidate.period === period.label && candidate.territory_code === selected);
      periodDetails[index].textContent = selected === null ? ""
        : row ? `${row.territory}: pico en la semana ${row.peak_week}.`
          : `${search.value.trim()}: sin pico calculable en ${period.label}.`;
    });
    status.textContent = isSearching && selected === null
      ? "Selecciona un territorio de la lista o borra la búsqueda para ver todos."
      : selected === null
        ? `Mostrando todos los ${level.value === "department" ? "departamentos" : "municipios"} con pico calculable.`
        : `Resaltando ${search.value.trim()} en los periodos con pico calculable.`;
    queue = queue.then(async () => {
      if (current !== version) return;
      const nextRows = PHASE_PERIODS.map((period) => rows.filter((row) =>
        row.period === period.label).map((row) => ({
          ...row, selected: selected !== null && row.territory_code === selected,
        })));
      views.forEach((view) => view.change("phase_scatter_data",
        vega.changeset().remove(() => true)).run());
      await Promise.all(views.map((view, index) => view.change("phase_scatter_data",
        vega.changeset().insert(nextRows[index])).runAsync()));
      if (current !== version) return;
      PHASE_PERIODS.forEach((period, index) => { currentSpecs[index] = phaseScatterSpec(nextRows[index], period); });
      PHASE_PERIODS.forEach((period) => document.querySelector(period.chart).setAttribute("aria-label",
        `Latitud y semana del pico por ${level.value === "department" ? "departamento" : "municipio"}, ${period.label}` +
        (selected === null ? "" : `; ${search.value.trim()} resaltado`)));
    }).catch((error) => { status.textContent = `No se pudieron actualizar los puntos: ${error.message}`; console.error(error); });
  }
  level.addEventListener("change", () => { search.value = ""; refreshOptions(); update(); });
  search.addEventListener("input", update);
  search.addEventListener("change", update);
  refreshOptions();
  controls.disabled = false;
  update();
}

function phaseCorrelationSpec(rows) {
  return {
    $schema: SCHEMA,
    width: CHART_WIDTH,
    height: 290,
    background: "transparent",
    layer: [
      {
        data: { values: [{ zero: 0 }] },
        mark: { type: "rule", color: "#596b75", strokeDash: [4, 4] },
        encoding: { y: { field: "zero", type: "quantitative", scale: { domain: [-1, 1] } } },
      },
      {
        data: { values: rows },
        mark: { type: "line", color: "#197f7a", strokeWidth: 2.5, point: { filled: true, size: 80 } },
        encoding: {
          x: { field: "year", type: "ordinal", title: "Año", axis: { labelAngle: -45, labelColor: "#425c68" } },
          y: {
            field: "spearman_r", type: "quantitative", title: "Spearman (rₛ)",
            scale: { domain: [-1, 1] }, axis: { gridColor: "#e4ecee", labelColor: "#425c68" },
          },
          tooltip: [
            { field: "year", title: "Año" },
            { field: "spearman_r", title: "Spearman rₛ", format: ".2f" },
            { field: "departments", title: "Departamentos" },
          ],
        },
      },
    ],
    config: { view: { stroke: null }, font: "system-ui, sans-serif" },
  };
}

async function loadPhaseAnalysis() {
  const chartIds = [...PHASE_PERIODS.map((period) => period.chart), "#chart-phase-spearman"];
  try {
    const responses = await Promise.all([
      fetch(PHASE_DATA_URL), fetch(PHASE_CORRELATION_URL), fetch(MUNICIPAL_PHASE_DATA_URL),
    ]);
    if (responses.some((response) => !response.ok)) throw new Error("No se pudieron cargar los datos de fase");
    const [phaseCsv, correlationCsv, municipalCsv] = await Promise.all([
      responses[0].text(), responses[1].text(), responses[2].text(),
    ]);
    const rows = phaseRowsFromCsv(phaseCsv);
    const municipalRows = phaseRowsFromCsv(municipalCsv);
    const correlations = csvObjects(correlationCsv).map((row) => ({
      year: Number(row.year), spearman_r: Number(row.spearman_r), departments: Number(row.departments),
    }));
    if (rows.length !== 22 * 32 || municipalRows.length < 2000 || correlations.length !== 18 ||
        rows.some((row) => !Number.isFinite(row.latitude) || !Number.isFinite(row.peak_week) ||
          !Number.isFinite(row.amplitude_per_100k) || !Number.isFinite(row.mean_rate_per_100k) ||
          (row.relative_amplitude === null
            ? row.mean_rate_per_100k !== 0 : !Number.isFinite(row.relative_amplitude))) ||
        municipalRows.some((row) => row.dimension !== "municipality" || !Number.isFinite(row.latitude) ||
          !Number.isFinite(row.peak_week) || !Number.isFinite(row.amplitude_per_100k) ||
          !Number.isFinite(row.mean_rate_per_100k)) ||
        correlations.some((row) => !Number.isFinite(row.spearman_r) || row.departments !== 32)) {
      throw new Error("Los datos de fase están incompletos");
    }
    const currentSpecs = PHASE_PERIODS.map((period) => phaseScatterSpec(rows, period));
    const views = await Promise.all(PHASE_PERIODS.map((period, index) => renderChart(period.chart,
      `Latitud y semana del pico · ${period.label}`, currentSpecs[index],
      { annualContext: false, modalSpec: () => currentSpecs[index] })));
    await renderChart("#chart-phase-spearman", "Correlación anual de Spearman",
      phaseCorrelationSpec(correlations), { annualContext: false });
    initPhaseScatterFilters(rows, municipalRows, views, currentSpecs);
  } catch (error) {
    for (const id of chartIds) {
      const chart = document.querySelector(id);
      if (!chart.querySelector("svg")) chart.textContent = `No se pudo cargar el gráfico: ${error.message}`;
    }
    document.querySelector("#phase-scatter-status").textContent = `No se pudieron cargar las fases territoriales: ${error.message}`;
    console.error(error);
  }
}

loadPhaseAnalysis();
