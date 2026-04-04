const DATA_URL = "recipes_info.json";
const EMPTY_TEXT = "לא צוין";

const state = {
  recipes: [],
  filtered: [],
};

const fields = {
  title: ["title", "name", "recipe_title"],
  category: ["category"],
  type: ["type"],
  origin: ["origin"],
  spiciness: ["spiciness"],
  diabetic: ["diabetic_friendly"],
  source: ["source"],
};

const FRONTMATTER_EXCLUDED_KEYS = new Set(["filename", "relative_path"]);

const els = {
  status: document.getElementById("status-message"),
  lastUpdated: document.getElementById("last-updated"),
  search: document.getElementById("search-input"),
  filters: {
    category: document.getElementById("filter-category"),
    type: document.getElementById("filter-type"),
    origin: document.getElementById("filter-origin"),
    spiciness: document.getElementById("filter-spiciness"),
    diabetic: document.getElementById("filter-diabetic"),
    source: document.getElementById("filter-source"),
  },
  kpi: {
    total: document.getElementById("kpi-total"),
    categories: document.getElementById("kpi-categories"),
    types: document.getElementById("kpi-types"),
    diabetic: document.getElementById("kpi-diabetic"),
  },
  tbody: document.getElementById("recipes-tbody"),
  emptyState: document.getElementById("empty-state"),
  charts: {
    category: document.getElementById("chart-category"),
    type: document.getElementById("chart-type"),
    origin: null,
    spiciness: null,
  },
  frontMatterInsights: null,
};

init();

async function init() {
  setStatus("טוען נתונים…", "");
  try {
    const response = await fetch(DATA_URL, { cache: "no-cache" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    updateLastUpdated(response.headers.get("last-modified"));

    const raw = await response.json();
    state.recipes = Array.isArray(raw) ? raw : [];

    if (!state.recipes.length) {
      setStatus("לא נמצאו נתונים להצגה בקובץ JSON.", "error");
      renderEmptyAll();
      return;
    }

    buildFilters();
    ensureAdditionalSections();
    wireEvents();
    applyFilters();
    setStatus("הנתונים נטענו בהצלחה.", "success");
  } catch (error) {
    setStatus("אירעה שגיאה בטעינת הנתונים. ודאו שהקובץ recipes_info.json זמין.", "error");
    updateLastUpdated(null);
    renderEmptyAll();
    console.error(error);
  }
}

function updateLastUpdated(lastModifiedHeader) {
  if (!els.lastUpdated) return;

  const fallback = "עדכון נתונים: תאריך עדכון לא זמין";
  if (!lastModifiedHeader) {
    els.lastUpdated.textContent = fallback;
    return;
  }

  const date = new Date(lastModifiedHeader);
  if (Number.isNaN(date.getTime())) {
    els.lastUpdated.textContent = fallback;
    return;
  }

  const formatted = new Intl.DateTimeFormat("he-IL", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);

  els.lastUpdated.textContent = `עדכון נתונים: ${formatted}`;
}

function wireEvents() {
  els.search.addEventListener("input", applyFilters);
  Object.values(els.filters).forEach((select) => {
    select.addEventListener("change", applyFilters);
  });
}

function buildFilters() {
  fillSelect(els.filters.category, extractDistinct("category"), "כל הקטגוריות");
  fillSelect(els.filters.type, extractDistinct("type"), "כל הסוגים");
  fillSelect(els.filters.origin, extractDistinct("origin"), "כל מקורות המוצא");
  fillSelect(els.filters.spiciness, extractDistinct("spiciness"), "כל רמות החריפות");
  fillSelect(els.filters.source, extractDistinct("source"), "כל מקורות המתכון");

  els.filters.diabetic.innerHTML = "";
  [
    { value: "", label: "הכול" },
    { value: "כן", label: "כן" },
    { value: "לא", label: "לא" },
  ].forEach((option) => {
    const el = document.createElement("option");
    el.value = option.value;
    el.textContent = option.label;
    els.filters.diabetic.appendChild(el);
  });
}

function applyFilters() {
  const query = els.search.value.trim().toLowerCase();
  const selected = {
    category: els.filters.category.value,
    type: els.filters.type.value,
    origin: els.filters.origin.value,
    spiciness: els.filters.spiciness.value,
    diabetic: els.filters.diabetic.value,
    source: els.filters.source.value,
  };

  state.filtered = state.recipes
    .filter((recipe) => {
      const title = getField(recipe, "title");
      const matchesQuery = !query || title.toLowerCase().includes(query);
      if (!matchesQuery) return false;

      if (selected.category && getField(recipe, "category") !== selected.category) return false;
      if (selected.type && getField(recipe, "type") !== selected.type) return false;
      if (selected.origin && getField(recipe, "origin") !== selected.origin) return false;
      if (selected.spiciness && getField(recipe, "spiciness") !== selected.spiciness) return false;
      if (selected.source && getField(recipe, "source") !== selected.source) return false;

      if (selected.diabetic) {
        const diabetic = normalizeDiabeticValue(recipe);
        if (diabetic !== selected.diabetic) return false;
      }

      return true;
    })
    .sort((a, b) => getField(a, "title").localeCompare(getField(b, "title"), "he"));

  render();
}

function render() {
  renderKpis();
  renderTable();
  renderCharts();
  renderFrontMatterInsights();
}

function renderKpis() {
  const total = state.filtered.length;
  const categories = distinctCount(state.filtered, "category");
  const types = distinctCount(state.filtered, "type");
  const diabeticCount = state.filtered.filter((recipe) => normalizeDiabeticValue(recipe) === "כן").length;

  els.kpi.total.textContent = String(total);
  els.kpi.categories.textContent = String(categories);
  els.kpi.types.textContent = String(types);
  els.kpi.diabetic.textContent = String(diabeticCount);
}

function renderTable() {
  els.tbody.innerHTML = "";

  if (!state.filtered.length) {
    els.emptyState.hidden = false;
    return;
  }

  els.emptyState.hidden = true;

  const fragment = document.createDocumentFragment();
  state.filtered.forEach((recipe) => {
    const tr = document.createElement("tr");

    const titleTd = document.createElement("td");
    const titleLink = document.createElement("a");
    titleLink.href = buildRecipeUrl(recipe);
    titleLink.textContent = getField(recipe, "title");
    titleLink.className = "recipe-link";
    titleTd.appendChild(titleLink);
    tr.appendChild(titleTd);

    [
      getField(recipe, "category"),
      getField(recipe, "type"),
      getField(recipe, "origin"),
      getField(recipe, "source"),
      hasImage(recipe) ? "כן" : "לא",
    ].forEach((value) => {
      const td = document.createElement("td");
      td.textContent = value;
      tr.appendChild(td);
    });

    fragment.appendChild(tr);
  });

  els.tbody.appendChild(fragment);
}

function renderCharts() {
  renderBarChart(els.charts.category, countBy(state.filtered, "category"));
  renderBarChart(els.charts.type, countBy(state.filtered, "type"));
  renderBarChart(els.charts.origin, countBy(state.filtered, "origin"), "earthy");
  renderBarChart(els.charts.spiciness, countBy(state.filtered, "spiciness"), "earthy");
}

function renderBarChart(container, buckets, variant = "") {
  if (!container) return;
  container.innerHTML = "";
  container.classList.toggle("earthy-chart", variant === "earthy");

  const entries = Object.entries(buckets)
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], "he"))
    .slice(0, 8);

  if (!entries.length) {
    const p = document.createElement("p");
    p.className = "empty-state";
    p.textContent = "אין נתונים להצגת תרשים עבור הסינון הנוכחי.";
    container.appendChild(p);
    return;
  }

  const max = Math.max(...entries.map(([, count]) => count));

  entries.forEach(([label, count]) => {
    const row = document.createElement("div");
    row.className = "bar-row";

    const labelEl = document.createElement("span");
    labelEl.className = "bar-label";
    labelEl.textContent = label;

    const track = document.createElement("div");
    track.className = "bar-track";

    const fill = document.createElement("div");
    fill.className = "bar-fill";
    fill.style.width = `${(count / max) * 100}%`;

    const valueEl = document.createElement("span");
    valueEl.className = "bar-value";
    valueEl.textContent = String(count);

    track.appendChild(fill);
    row.append(labelEl, track, valueEl);
    container.appendChild(row);
  });
}

function ensureAdditionalSections() {
  const chartsSection = document.querySelector(".charts");
  if (chartsSection && !document.getElementById("chart-origin")) {
    chartsSection.appendChild(createChartCard("התפלגות לפי מקור גאוגרפי", "chart-origin"));
    chartsSection.appendChild(createChartCard("התפלגות לפי רמת חריפות", "chart-spiciness"));
    els.charts.origin = document.getElementById("chart-origin");
    els.charts.spiciness = document.getElementById("chart-spiciness");
  }

  if (!document.getElementById("frontmatter-insights")) {
    const section = document.createElement("section");
    section.id = "frontmatter-insights";
    section.className = "frontmatter-insights";
    section.setAttribute("aria-label", "סקירת שדות פרונט מטר");
    section.innerHTML = `
      <h2>סקירת שדות פרונט מטר</h2>
      <p class="frontmatter-subtitle">מפתח, מספר ערכים שונים והתפלגות ערכים לכל שדה.</p>
      <div id="frontmatter-keys" class="frontmatter-grid"></div>
    `;
    const tableSection = document.querySelector(".table-section");
    if (tableSection) {
      tableSection.before(section);
      els.frontMatterInsights = document.getElementById("frontmatter-keys");
    }
  } else {
    els.frontMatterInsights = document.getElementById("frontmatter-keys");
  }
}

function createChartCard(title, chartId) {
  const card = document.createElement("article");
  card.className = "chart-card chart-card-earthy";
  card.innerHTML = `
    <h2>${title}</h2>
    <div id="${chartId}" class="bar-chart"></div>
  `;
  return card;
}

function renderFrontMatterInsights() {
  if (!els.frontMatterInsights) return;
  els.frontMatterInsights.innerHTML = "";

  const keys = getFrontMatterKeys(state.recipes);
  const fragment = document.createDocumentFragment();

  keys.forEach((keyName) => {
    const buckets = countBy(state.filtered, keyName);
    const entries = Object.entries(buckets).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], "he"));

    const card = document.createElement("article");
    card.className = "frontmatter-card";

    const list = document.createElement("ul");
    list.className = "frontmatter-values";
    entries.forEach(([value, count]) => {
      const li = document.createElement("li");
      li.className = "frontmatter-value-item";
      li.innerHTML = `<span class="frontmatter-chip">${value}</span><span class="frontmatter-count">${count}</span>`;
      list.appendChild(li);
    });

    card.innerHTML = `
      <h3>${keyName}</h3>
      <p class="frontmatter-meta">מספר ערכים שונים: <strong>${entries.length}</strong></p>
    `;
    card.appendChild(list);
    fragment.appendChild(card);
  });

  els.frontMatterInsights.appendChild(fragment);
}

function getFrontMatterKeys(list) {
  return [...new Set(list.flatMap((item) => Object.keys(item || {})))]
    .filter((keyName) => !FRONTMATTER_EXCLUDED_KEYS.has(keyName))
    .sort((a, b) => a.localeCompare(b, "he"));
}

function fillSelect(selectEl, values, allLabel) {
  selectEl.innerHTML = "";
  const options = ["", ...values];

  options.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value || allLabel;
    selectEl.appendChild(option);
  });
}

function extractDistinct(fieldName) {
  return [...new Set(state.recipes.map((recipe) => getField(recipe, fieldName)).filter((v) => v !== EMPTY_TEXT))]
    .sort((a, b) => a.localeCompare(b, "he"));
}

function distinctCount(list, fieldName) {
  return new Set(list.map((item) => getField(item, fieldName)).filter((v) => v !== EMPTY_TEXT)).size;
}

function countBy(list, fieldName) {
  return list.reduce((acc, item) => {
    const key = getField(item, fieldName);
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});
}

function getField(recipe, fieldName) {
  const keys = fields[fieldName] || [fieldName];
  for (const key of keys) {
    const value = recipe?.[key];
    if (value === 0 || value === false) return String(value);
    if (typeof value === "string" && value.trim()) return value.trim();
  }
  return EMPTY_TEXT;
}

function normalizeDiabeticValue(recipe) {
  const value = recipe?.diabetic_friendly;
  if (typeof value === "boolean") return value ? "כן" : "לא";

  const text = String(value ?? "").trim().toLowerCase();
  if (["yes", "true", "1", "כן"].includes(text)) return "כן";
  if (["no", "false", "0", "לא"].includes(text)) return "לא";

  return "לא";
}

function hasImage(recipe) {
  return typeof recipe?.image === "string" && recipe.image.trim() !== "";
}

function buildRecipeUrl(recipe) {
  const relativePath = String(recipe?.relative_path ?? "").trim();
  const match = relativePath.match(/^_recipes\/(.+)\.md$/i);
  if (!match) return "#";
  const slug = match[1].toLowerCase().replace(/_/g, "-");
  return `/family_recipes/recipes/${slug}/`;
  return `/family_recipes/recipes/${match[1]}/`;
}

function renderEmptyAll() {
  state.filtered = [];
  render();
}

function setStatus(message, type) {
  els.status.textContent = message;
  els.status.classList.remove("error", "success");
  if (type) {
    els.status.classList.add(type);
  }
}
