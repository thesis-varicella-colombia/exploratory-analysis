"use strict";

const SPATIAL_DATA_URL = "data_processed/spatial_series_2008_2025.csv";
const MUNICIPAL_BOUNDARIES_URL = "data_processed/municipal_boundaries_dane.geojson";
const SPATIAL_NUMBER = new Intl.NumberFormat("es-CO");
const SPATIAL_RATE = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 1 });
const RATE_COLORS = ["#d9efeb", "#9fd6cb", "#5ab8ab", "#218f8c", "#176b7a", "#103d60"];
const RATE_BINS = [25, 50, 100, 200, 400];
const selector = document.querySelector("#spatial-period");
const municipalitySelector = document.querySelector("#spatial-municipality");
const municipalityOptions = document.querySelector("#spatial-municipality-options");
const status = document.querySelector("#spatial-map-status");

function parseSpatialCsv(source) {
  const lines = source.trim().split(/\r?\n/);
  const fields = lines.shift().split(",");
  const groups = new Map();
  for (const line of lines) {
    const values = line.split(",");
    const row = Object.fromEntries(fields.map((field, index) => [field, values[index]]));
    if (!groups.has(row.period)) groups.set(row.period, new Map());
    groups.get(row.period).set(row.code, {
      notifications: Number(row.notifications),
      populationYears: Number(row.population_years),
      years: Number(row.years),
      rate: row.rate_per_100k === "" ? null : Number(row.rate_per_100k),
    });
  }
  return groups;
}

function rateColor(rate) {
  if (rate === null) return "#b7c3c9";
  if (rate === 0) return "#f1f5f5";
  for (let index = 0; index < RATE_BINS.length; index += 1) {
    if (rate <= RATE_BINS[index]) return RATE_COLORS[index];
  }
  return RATE_COLORS.at(-1);
}

function popupContent(feature, row, periodLabel) {
  const name = document.createElement("div");
  const title = document.createElement("strong");
  title.textContent = `${feature.properties.name} (${feature.properties.code})`;
  const department = document.createElement("div");
  department.textContent = `${feature.properties.department} · ${feature.properties.kind.toLowerCase()}`;
  const period = document.createElement("div");
  period.textContent = periodLabel;
  const rate = document.createElement("div");
  rate.textContent = row?.rate === null || !row
    ? "Tasa: sin denominador disponible"
    : `Tasa: ${SPATIAL_RATE.format(row.rate)} por 100.000`;
  const cases = document.createElement("div");
  cases.textContent = `Notificaciones: ${SPATIAL_NUMBER.format(row?.notifications ?? 0)}`;
  const population = document.createElement("div");
  population.textContent = row?.years === 1
    ? `Población anual: ${SPATIAL_NUMBER.format(row.populationYears)}`
    : `Población-año acumulada: ${SPATIAL_NUMBER.format(row?.populationYears ?? 0)} (${row?.years ?? 0} años)`;
  name.append(title, department, period, rate, cases, population);
  return name;
}

function addLegend(map) {
  const legend = L.control({ position: "bottomright" });
  legend.onAdd = () => {
    const container = L.DomUtil.create("div", "spatial-legend");
    const title = document.createElement("strong");
    title.textContent = "Tasa por 100.000";
    container.append(title);
    const entries = [
      ["Sin población", "#b7c3c9"],
      ["0 notificaciones", "#f1f5f5"],
      [">0–25", RATE_COLORS[0]],
      [">25–50", RATE_COLORS[1]],
      [">50–100", RATE_COLORS[2]],
      [">100–200", RATE_COLORS[3]],
      [">200–400", RATE_COLORS[4]],
      [">400", RATE_COLORS[5]],
    ];
    for (const [label, color] of entries) {
      const row = document.createElement("div");
      const swatch = document.createElement("span");
      swatch.className = "spatial-legend-swatch";
      swatch.style.backgroundColor = color;
      row.append(swatch, document.createTextNode(label));
      container.append(row);
    }
    L.DomEvent.disableClickPropagation(container);
    return container;
  };
  legend.addTo(map);
}

async function loadSpatialMap() {
  try {
    if (typeof L === "undefined") throw new Error("No se pudo cargar Leaflet");
    const [dataResponse, boundariesResponse] = await Promise.all([
      fetch(SPATIAL_DATA_URL),
      fetch(MUNICIPAL_BOUNDARIES_URL),
    ]);
    if (!dataResponse.ok || !boundariesResponse.ok) throw new Error("No se pudieron cargar los datos espaciales");
    const [data, boundaries] = await Promise.all([dataResponse.text(), boundariesResponse.json()]);
    const byPeriod = parseSpatialCsv(data);
    if (boundaries.type !== "FeatureCollection" || !boundaries.features?.length || !byPeriod.has(selector.value)) {
      throw new Error("El mapa o sus tasas están incompletos");
    }

    const map = L.map("spatial-map", { scrollWheelZoom: false, preferCanvas: true });
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);
    let selectedPeriod = selector.value;
    let selectedCode = "";
    const layersByCode = new Map();
    const periodLabel = () => selector.selectedOptions[0].textContent;
    const style = (feature) => ({
      color: feature.properties.code === selectedCode ? "#ed6a00" : "#526b74",
      weight: feature.properties.code === selectedCode ? 3 : 0.45,
      fillOpacity: feature.properties.code === selectedCode ? 1 : 0.82,
      fillColor: rateColor(byPeriod.get(selectedPeriod).get(feature.properties.code)?.rate ?? null),
    });
    const municipalities = L.geoJSON(boundaries, {
      style,
      onEachFeature(feature, layer) {
        layersByCode.set(feature.properties.code, layer);
        layer.bindPopup(() => popupContent(
          feature, byPeriod.get(selectedPeriod).get(feature.properties.code), periodLabel(),
        ));
        layer.on("mouseover", () => {
          if (feature.properties.code !== selectedCode) layer.setStyle({ weight: 2, color: "#173042" });
        });
        layer.on("mouseout", () => municipalities.resetStyle(layer));
        layer.on("click", () => selectMunicipality(feature.properties.code, false));
      },
    }).addTo(map);
    map.fitBounds(municipalities.getBounds(), { padding: [12, 12] });
    addLegend(map);

    const normalizeSearch = (value) => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("es");
    const options = boundaries.features
      .map((feature) => {
        const props = feature.properties;
        const label = `${props.name} · ${props.department} (${props.code})`;
        return { code: props.code, label, searchText: normalizeSearch(label) };
      })
      .sort((a, b) => a.label.localeCompare(b.label, "es"));
    const optionByCode = new Map(options.map((option) => [option.code, option]));
    let visibleOptions = [];
    let activeIndex = -1;

    function closeMunicipalities() {
      municipalityOptions.hidden = true;
      municipalitySelector.setAttribute("aria-expanded", "false");
      municipalitySelector.removeAttribute("aria-activedescendant");
      municipalitySelector.value = selectedCode ? optionByCode.get(selectedCode).label : "";
    }

    function renderMunicipalities(query) {
      const term = normalizeSearch(query.trim());
      visibleOptions = options.filter((option) => option.searchText.includes(term));
      if (!term) visibleOptions.unshift({ code: "", label: "Toda Colombia" });
      const fragment = document.createDocumentFragment();
      if (!visibleOptions.length) {
        const empty = document.createElement("div");
        empty.className = "spatial-option";
        empty.textContent = "Sin coincidencias";
        fragment.append(empty);
      }
      for (const item of visibleOptions) {
        const option = document.createElement("div");
        option.id = `spatial-choice-${item.code || "all"}`;
        option.className = "spatial-option";
        option.setAttribute("role", "option");
        option.setAttribute("aria-selected", String(item.code === selectedCode));
        option.dataset.code = item.code;
        option.textContent = item.label;
        fragment.append(option);
      }
      municipalityOptions.replaceChildren(fragment);
      municipalityOptions.hidden = false;
      municipalitySelector.setAttribute("aria-expanded", "true");
      municipalitySelector.removeAttribute("aria-activedescendant");
      activeIndex = -1;
    }

    function setActive(index) {
      if (!visibleOptions.length) return;
      activeIndex = (index + visibleOptions.length) % visibleOptions.length;
      const choices = municipalityOptions.querySelectorAll('[role="option"]');
      choices.forEach((choice, position) => choice.classList.toggle("active", position === activeIndex));
      const active = choices[activeIndex];
      municipalitySelector.setAttribute("aria-activedescendant", active.id);
      active.scrollIntoView({ block: "nearest" });
    }

    function selectMunicipality(code, focus) {
      selectedCode = code;
      closeMunicipalities();
      municipalities.setStyle(style);
      if (code) {
        const layer = layersByCode.get(code);
        layer.bringToFront();
        if (focus) {
          map.fitBounds(layer.getBounds(), { padding: [30, 30], maxZoom: 10 });
          layer.openPopup();
        }
      } else if (focus) {
        map.closePopup();
        map.fitBounds(municipalities.getBounds(), { padding: [12, 12] });
      }
      updateStatus();
    }

    function updateStatus() {
      const rows = byPeriod.get(selectedPeriod);
      const mapped = boundaries.features.filter((feature) => {
        const row = rows.get(feature.properties.code);
        return row && row.rate !== null;
      }).length;
      const selected = selectedCode ? ` Área resaltada: ${optionByCode.get(selectedCode).label}.` : "";
      status.textContent = `${periodLabel()}: ${SPATIAL_NUMBER.format(mapped)} entidades territoriales con tasa calculable.${selected}`;
    }

    function update() {
      selectedPeriod = selector.value;
      map.closePopup();
      municipalities.setStyle(style);
      if (selectedCode) layersByCode.get(selectedCode).bringToFront().openPopup();
      updateStatus();
    }
    selector.addEventListener("change", update);
    municipalitySelector.addEventListener("focus", () => {
      renderMunicipalities("");
      municipalitySelector.select();
    });
    municipalitySelector.addEventListener("input", () => renderMunicipalities(municipalitySelector.value));
    municipalitySelector.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        closeMunicipalities();
        municipalitySelector.blur();
      } else if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        if (municipalityOptions.hidden) renderMunicipalities("");
        const next = activeIndex < 0
          ? (event.key === "ArrowDown" ? 0 : visibleOptions.length - 1)
          : activeIndex + (event.key === "ArrowDown" ? 1 : -1);
        setActive(next);
      } else if (event.key === "Enter" && !municipalityOptions.hidden && visibleOptions.length
        && (activeIndex >= 0 || municipalitySelector.value.trim())) {
        event.preventDefault();
        selectMunicipality(visibleOptions[activeIndex < 0 ? 0 : activeIndex].code, true);
      }
    });
    municipalitySelector.addEventListener("blur", closeMunicipalities);
    municipalityOptions.addEventListener("pointerdown", (event) => {
      const choice = event.target.closest('[role="option"]');
      if (!choice) return;
      event.preventDefault();
      selectMunicipality(choice.dataset.code, true);
    });
    selector.disabled = false;
    municipalitySelector.disabled = false;
    update();
  } catch (error) {
    status.textContent = `No se pudo cargar el mapa: ${error.message}`;
    console.error(error);
  }
}

loadSpatialMap();
