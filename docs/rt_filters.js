"use strict";

const RT_STRATA_ROOT = "data_processed/numero_reproductivo/rt_visualization";
// Descending centroid latitude of the published DANE 2025 department geometries,
// including the archipelago and Bogotá D.C.
const RT_DEPARTMENTS_NORTH_TO_SOUTH = [
  "88", "44", "08", "47", "20", "70", "13", "23", "54", "05", "68",
  "81", "27", "15", "85", "17", "66", "25", "99", "63", "11", "73",
  "76", "50", "94", "41", "19", "95", "52", "18", "97", "86", "91",
];

async function readRtStratum(response, calendar, caseField) {
  if (!response.ok) throw new Error(`HTTP ${response.status} al cargar la estimación`);
  const bytes = await response.arrayBuffer();
  const header = new Uint8Array(bytes, 0, Math.min(2, bytes.byteLength));
  // Static hosts may send the gzip as a file or decode it via Content-Encoding.
  const decoded = header[0] === 0x1f && header[1] === 0x8b
    ? await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"))).text()
    : new TextDecoder().decode(bytes);
  const data = JSON.parse(decoded);
  function decode(columns) {
    const fields = ["count", "window_cases", "rt", "rt_lower_95", "rt_upper_95"];
    if (columns.offset || columns.length) {
      if (!Array.isArray(columns.offset) || !Array.isArray(columns.length) ||
          columns.offset.length !== columns.length.length) throw new Error("Coordenadas resumidas inválidas");
      let cursor = 0;
      const first = [], last = [], index = [];
      for (let i = 0; i < columns.offset.length; i += 1) {
        const offset = columns.offset[i], length = columns.length[i];
        if (!Number.isInteger(offset) || offset < 0 || !Number.isInteger(length) || length < 1) {
          throw new Error("Bloque resumido inválido");
        }
        const begin = cursor + offset;
        cursor = begin + length;
        first.push(begin); last.push(cursor - 1); index.push((begin + cursor - 1) / 2);
      }
      columns = { ...columns, first, last, index };
    }
    const indices = columns.index || calendar.date.map((_, index) => index);
    if (!Array.isArray(indices) || indices.some((index, position) => !Number.isFinite(index) || index < 0 ||
        index > calendar.date.length - 1 || (position > 0 && index <= indices[position - 1])) ||
        fields.some((field) => !Array.isArray(columns[field]) || columns[field].length !== indices.length ||
          columns[field].some((value) => value !== null && (!Number.isFinite(value) || value < 0)))) {
      throw new Error("La estimación por grupo está incompleta o contiene valores inválidos");
    }
    if (columns.index && ["first", "last"].some((field) => !Array.isArray(columns[field]) ||
        columns[field].length !== indices.length)) throw new Error("Faltan los intervalos de los puntos resumidos");
    let segment = 0;
    let previousFinite = false;
    return indices.map((index, position) => {
      const day = Math.floor(index);
      const first = columns.first?.[position] ?? day;
      const last = columns.last?.[position] ?? day;
      if (![first, last].every(Number.isInteger) || first < 0 || last >= calendar.date.length ||
          first > index || last < index) throw new Error("Intervalo resumido inválido");
      const date = Number.isInteger(index) ? calendar.date[index]
        : new Date(Date.parse(calendar.date[0]) + index * 86400000).toISOString();
      const rt = columns.rt[position];
      if (calendar.missing_week[day] && (columns.count[position] !== null || rt !== null)) {
        throw new Error("La serie no conserva las semanas sin datos");
      }
      if (rt !== null && (columns.rt_lower_95[position] === null || columns.rt_upper_95[position] === null ||
          columns.rt_lower_95[position] > rt || columns.rt_upper_95[position] < rt)) {
        throw new Error("Intervalo de Rₜ inválido");
      }
      if (rt !== null && !previousFinite) segment += 1;
      previousFinite = rt !== null;
      return { date, year: calendar.year[day], week: calendar.week[day],
        period_start: calendar.date[first], period_end: calendar.date[last], days: last - first + 1,
        [caseField]: columns.count[position], window_cases: columns.window_cases[position], rt,
        rt_lower_95: columns.rt_lower_95[position], rt_upper_95: columns.rt_upper_95[position],
        segment: rt === null ? null : segment };
    });
  }
  const rows = decode(data);
  if (data.detail) rows.detailRows = decode(data.detail);
  return rows;
}

function initRtMunicipalitySearch(input, list, onSelect) {
  const normalize = (value) => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("es");
  let entries = [];
  let selected = "all";
  let visible = [];
  let activeIndex = -1;

  function close() {
    list.hidden = true;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
    input.value = entries.find((entry) => entry.id === selected)?.name || "";
  }
  function render(query) {
    const term = normalize(query.trim());
    visible = entries.filter((entry) => normalize(entry.name).includes(term));
    const choices = visible.map((entry) => {
      const option = document.createElement("div");
      option.id = `rt-choice-${entry.id}`;
      option.className = "spatial-option";
      option.setAttribute("role", "option");
      option.setAttribute("aria-selected", String(entry.id === selected));
      option.dataset.id = entry.id;
      option.textContent = entry.name;
      return option;
    });
    if (!choices.length) {
      const empty = document.createElement("div");
      empty.className = "spatial-option";
      empty.textContent = "Sin coincidencias";
      choices.push(empty);
    }
    list.replaceChildren(...choices);
    list.hidden = false;
    input.setAttribute("aria-expanded", "true");
    input.removeAttribute("aria-activedescendant");
    activeIndex = -1;
  }
  function activate(index) {
    if (!visible.length) return;
    activeIndex = (index + visible.length) % visible.length;
    const choices = list.querySelectorAll('[role="option"]');
    choices.forEach((choice, position) => choice.classList.toggle("active", position === activeIndex));
    const active = choices[activeIndex];
    input.setAttribute("aria-activedescendant", active.id);
    active.scrollIntoView({ block: "nearest" });
  }
  function select(id) {
    if (!entries.some((entry) => entry.id === id)) return;
    selected = id;
    close();
    return onSelect(id);
  }
  input.addEventListener("focus", () => { render(""); input.select(); });
  input.addEventListener("input", () => render(input.value));
  input.addEventListener("blur", close);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      close();
      input.blur();
    } else if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (list.hidden) render("");
      activate(activeIndex < 0 ? (event.key === "ArrowDown" ? 0 : visible.length - 1)
        : activeIndex + (event.key === "ArrowDown" ? 1 : -1));
    } else if (event.key === "Enter" && !list.hidden && visible.length &&
        (activeIndex >= 0 || input.value.trim())) {
      event.preventDefault();
      return select(visible[activeIndex < 0 ? 0 : activeIndex].id);
    }
  });
  list.addEventListener("pointerdown", (event) => {
    const choice = event.target.closest('[role="option"]');
    if (!choice) return;
    event.preventDefault();
    return select(choice.dataset.id);
  });
  return {
    close,
    reset(values) { entries = values; selected = "all"; close(); },
  };
}

function rtLiveSpec(spec, { onset, detail }, fullScale) {
  const limited = onset && !detail;
  return {
    ...spec,
    title: { text: { expr: "rt_title" } },
    params: [{ name: "rt_title", value: spec.title }, { name: "rt_full_scale", value: fullScale }],
    data: { name: "rt_series", values: spec.data.values },
    encoding: { ...spec.encoding,
      y: limited ? { ...spec.encoding.y,
        title: { expr: "rt_full_scale ? 'Rₜ estimado' : 'Rₜ estimado (vista 0–2)'" },
        scale: { zero: true, domainRaw: { expr: "rt_full_scale ? null : [0, 2]" } },
      } : spec.encoding.y,
    },
    layer: spec.layer.map((layer) => limited && ["line", "area", "point"].includes(layer.mark.type)
      ? { ...layer, mark: { ...layer.mark, clip: true } } : layer),
  };
}

async function initRtFilters() {
  const filters = document.querySelector("#rt-filters");
  const dimension = document.querySelector("#rt-dimension");
  const department = document.querySelector("#rt-department");
  const municipality = document.querySelector("#rt-municipality");
  const municipalityOptions = document.querySelector("#rt-municipality-options");
  const fullScale = document.querySelector("#rt-full-scale");
  const status = document.querySelector("#rt-filter-status");
  const chartConfigs = [
    { id: "#chart-rt-national", method: "notification", field: "notifications", onset: false },
    { id: "#chart-rt-onset", method: "symptom", field: "cases", onset: true },
    { id: "#chart-rt-onset-detail", method: "symptom", field: "cases", onset: true, detail: true },
  ];
  const views = new Map();
  const emptyMessages = new Map();
  const cache = new Map();
  let requestVersion = 0;
  let renderQueue = Promise.resolve();

  function options(select, entries) {
    select.replaceChildren();
    for (const entry of entries) {
      const option = document.createElement("option");
      option.value = entry.id;
      option.textContent = entry.name;
      select.append(option);
    }
    select.value = entries[0]?.id || "";
  }
  function showError(error) {
    status.textContent = `No se pudieron cargar las estimaciones de Rₜ: ${error.message}. Cambia la selección para reintentar.`;
    console.error(error);
  }
  try {
    const response = await fetch(`${RT_STRATA_ROOT}/manifest.json?v=20261029`);
    if (!response.ok) throw new Error(`HTTP ${response.status} al cargar el catálogo`);
    const manifest = await response.json();
    if (manifest.version !== 1 || manifest.visualization?.format !== 1 || !Array.isArray(manifest.series) ||
        !manifest.series.some((row) => row.id === "national") ||
        ["notification", "symptom"].some((method) => {
          const calendar = manifest.calendars?.[method];
          return !calendar || ["date", "year", "week", "missing_week"].some((field) =>
            !Array.isArray(calendar[field]) || calendar[field].length !== 6580);
        })) throw new Error("El catálogo de estimaciones está incompleto");
    const seriesById = new Map(manifest.series.filter((row) => row.dimension !== "age").map((row) => [row.id, row]));
    const byName = (a, b) => a.name.localeCompare(b.name, "es");
    const northToSouth = new Map(RT_DEPARTMENTS_NORTH_TO_SOUTH.map((code, index) => [code, index]));
    options(department, manifest.series.filter((row) => row.dimension === "department")
      .sort((a, b) => (northToSouth.get(a.code) ?? Infinity) - (northToSouth.get(b.code) ?? Infinity) || byName(a, b)));

    let selectedMunicipality = "all";
    const municipalitySearch = initRtMunicipalitySearch(municipality, municipalityOptions, (id) => {
      selectedMunicipality = id;
      return update();
    });
    function updateMunicipalities() {
      const code = seriesById.get(department.value).code;
      selectedMunicipality = "all";
      municipalitySearch.reset([{ id: "all", name: "Todo el departamento" },
        ...manifest.series.filter((row) => row.dimension === "municipality" && row.department === code)
          .sort(byName).map((row) => ({ ...row, name: `${row.name} · ${seriesById.get(department.value).name} (${row.code})` }))]);
    }
    updateMunicipalities();

    function selectedSeries() {
      if (dimension.value === "territory") {
        return seriesById.get(selectedMunicipality === "all" ? department.value : selectedMunicipality);
      }
      return seriesById.get("national");
    }
    function selectionLabel(stratum) {
      if (stratum.dimension === "municipality") {
        return `${stratum.name} (${stratum.code}) · ${seriesById.get(`department_${stratum.department}`).name}`;
      }
      return stratum.name;
    }
    function load(method, stratum) {
      const key = `${method}/${stratum.id}`;
      if (!cache.has(key)) {
        const pending = fetch(`${RT_STRATA_ROOT}/${key}.json.gz`).then((response) =>
          readRtStratum(response, manifest.calendars[method], method === "notification" ? "notifications" : "cases"))
          .catch((error) => { cache.delete(key); throw error; });
        cache.set(key, pending);
        if (cache.size > 12) cache.delete(cache.keys().next().value);
      }
      return cache.get(key);
    }
    async function update() {
      const version = ++requestVersion;
      const stratum = selectedSeries();
      const label = selectionLabel(stratum);
      const showFullScale = fullScale.checked;
      document.querySelector("#rt-territory-control").hidden = dimension.value !== "territory";
      status.textContent = `Cargando Rₜ · ${label}…`;
      filters.setAttribute("aria-busy", "true");
      try {
        const [notification, symptom] = await Promise.all([load("notification", stratum), load("symptom", stratum)]);
        if (version !== requestVersion) return;
        const data = { notification, symptom };
        renderQueue = renderQueue.catch(() => {}).then(async () => {
          if (version !== requestVersion) return;
          for (const config of chartConfigs) {
            if (version !== requestVersion) return;
            const chart = document.querySelector(config.id);
            const rows = data[config.method];
            const spec = rtSpec(rows, { onset: config.onset, detail: config.detail, label, fullScale: showFullScale });
            chart.setAttribute("aria-label", spec.title);
            if (!emptyMessages.has(config.id)) {
              const message = document.createElement("p");
              message.id = `${config.id.slice(1)}-empty`;
              message.className = "age-note";
              message.setAttribute("role", "status");
              chart.after(message);
              emptyMessages.set(config.id, message);
            }
            const visible = spec.data.values.some((row) => row.rt !== null);
            const message = emptyMessages.get(config.id);
            message.textContent = visible ? "" : `No hay estimaciones de Rₜ con historia suficiente para ${label} en este intervalo.`;
            message.hidden = visible;
            chart.hidden = !visible;
            let state = views.get(config.id);
            if (state) {
              state.spec = spec;
              const newData = state.rows !== rows;
              const newScale = config.onset && !config.detail && state.fullScale !== showFullScale;
              if (newData || newScale) {
                state.view.signal("rt_title", spec.title).signal("rt_full_scale", showFullScale);
                if (newData) state.view.data("rt_series", spec.data.values);
                await state.view.runAsync();
                state.rows = rows;
                state.fullScale = showFullScale;
              }
            } else if (visible) {
              state = { spec, rows, fullScale: showFullScale };
              state.view = await renderChart(config.id, spec.title, rtLiveSpec(spec, config, showFullScale), {
                annualContext: false, modalSpec: () => state.spec, modalTitle: () => state.spec.title,
              });
              views.set(config.id, state);
            }
            if (chart.previousElementSibling?.classList.contains("chart-controls")) {
              chart.previousElementSibling.hidden = !visible;
            }
          }
          if (version !== requestVersion) return;
          document.querySelector("#rt-notification-title").textContent = stratum.id === "national"
            ? "Rₜ nacional por fecha de notificación" : `Rₜ por fecha de notificación · ${label}`;
          document.querySelector("#rt-symptom-title").textContent = stratum.id === "national"
            ? "Rₜ nacional por inicio de síntomas" : `Rₜ por inicio de síntomas · ${label}`;
          document.dispatchEvent?.(new CustomEvent("rt-selection-changed", {detail:{id:stratum.id,label}}));
          status.textContent = `${label} · 2008–2025. Notificación: ${NUMBER.format(stratum.notification.cases)} casos, ` +
            `${NUMBER.format(stratum.notification.estimated_days)} días con Rₜ. Inicio de síntomas: ` +
            `${NUMBER.format(stratum.symptom.cases)} casos, ${NUMBER.format(stratum.symptom.estimated_days)} días con Rₜ.`;
        });
        await renderQueue;
      } catch (error) {
        if (version === requestVersion) showError(error);
      } finally {
        if (version === requestVersion) filters.setAttribute("aria-busy", "false");
      }
    }
    dimension.addEventListener("change", () => { municipalitySearch.close(); return update(); });
    department.addEventListener("change", () => { updateMunicipalities(); return update(); });
    fullScale.addEventListener("change", update);
    filters.disabled = false;
    await update();
  } catch (error) {
    showError(error);
    // Preserve the original national charts when the optional catalogue is unavailable.
    await Promise.all([loadRtChart(), loadOnsetRtChart()]);
  }
}

initRtFilters();
