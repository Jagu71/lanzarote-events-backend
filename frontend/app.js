const elements = {
  form: document.querySelector("#filters-form"),
  startsAfter: document.querySelector("#starts-after"),
  category: document.querySelector("#category"),
  query: document.querySelector("#query"),
  freeOnly: document.querySelector("#free-only"),
  featuredGrid: document.querySelector("#featured-grid"),
  resultsSummary: document.querySelector("#results-summary"),
  resultsGrid: document.querySelector("#results-grid"),
  status: document.querySelector("#status"),
  activeRange: document.querySelector("#active-range"),
  heroRangeLabel: document.querySelector("#hero-range-label"),
  heroContext: document.querySelector("#hero-context"),
  detailPanel: document.querySelector("#detail-panel"),
  detailContent: document.querySelector("#detail-content"),
  cardTemplate: document.querySelector("#event-card-template"),
};

const state = {
  categories: [],
};

document.addEventListener("DOMContentLoaded", async () => {
  setDefaultDateTime();
  bindEvents();
  await loadCategories();
  try {
    await refreshHome();
  } catch (error) {
    setStatus(error.message || "No se pudieron cargar las propuestas.");
  }
});

function bindEvents() {
  elements.form.addEventListener("submit", async (event) => {
    event.preventDefault();
    await refreshHome();
  });

  for (const input of [elements.startsAfter, elements.category, elements.freeOnly]) {
    input.addEventListener("change", () => {
      elements.form.requestSubmit();
    });
  }

  let searchTimeout = null;
  elements.query.addEventListener("input", () => {
    window.clearTimeout(searchTimeout);
    searchTimeout = window.setTimeout(() => elements.form.requestSubmit(), 220);
  });

  elements.detailPanel.addEventListener("click", (event) => {
    if (event.target instanceof HTMLElement && event.target.hasAttribute("data-close-detail")) {
      closeDetail();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeDetail();
    }
  });
}

function setDefaultDateTime() {
  const now = new Date();
  elements.startsAfter.value = formatForDateTimeLocal(now);
  updateRangeLabels();
}

async function refreshHome() {
  updateRangeLabels();
  setStatus("Cargando propuestas...");
  await Promise.all([loadFeatured(), loadWindowEvents()]);
  if (!elements.status.textContent.startsWith("No se pudo")) {
    setStatus("");
  }
}

async function loadCategories() {
  try {
    const response = await fetch("/api/v1/categories?lang=es");
    if (!response.ok) {
      throw new Error("No se pudieron cargar las categorías");
    }
    state.categories = await response.json();
    const options = ['<option value="">Todas</option>']
      .concat(state.categories.map((category) => `<option value="${category.slug}">${category.name}</option>`))
      .join("");
    elements.category.innerHTML = options;
  } catch (error) {
    setStatus(error.message);
  }
}

async function loadFeatured() {
  const params = new URLSearchParams({
    lang: "es",
    search_at: toIso(elements.startsAfter.value),
  });
  if (elements.category.value) {
    params.set("category", elements.category.value);
  }
  if (elements.freeOnly.checked) {
    params.set("free_only", "true");
  }

  try {
    const response = await fetch(`/api/v1/events/next-48h?${params.toString()}`);
    if (!response.ok) {
      throw new Error("No se pudo cargar la selección editorial");
    }
    const payload = await response.json();
    renderFeatured(payload.featured || []);
  } catch (error) {
    elements.featuredGrid.innerHTML = `<div class="empty-state">${error.message}</div>`;
    setStatus(error.message);
  }
}

async function loadWindowEvents() {
  const startsAfter = toIso(elements.startsAfter.value);
  const startsBefore = toIso(addHours(parseDateTimeLocal(elements.startsAfter.value), 48));
  const params = new URLSearchParams({
    lang: "es",
    starts_after: startsAfter,
    starts_before: startsBefore,
    limit: "60",
  });

  if (elements.category.value) {
    params.set("category", elements.category.value);
  }
  if (elements.query.value.trim()) {
    params.set("q", elements.query.value.trim());
  }
  if (elements.freeOnly.checked) {
    params.set("free_only", "true");
  }

  try {
    const response = await fetch(`/api/v1/events?${params.toString()}`);
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || "No se pudieron cargar los eventos");
    }
    const payload = await response.json();
    renderEvents(payload.items, payload.total);
  } catch (error) {
    renderEvents([], 0);
    setStatus(error.message);
  }
}

function renderFeatured(featuredItems) {
  elements.featuredGrid.innerHTML = "";
  const fragment = document.createDocumentFragment();

  for (const feature of featuredItems) {
    const event = feature.event;
    const card = document.createElement("article");
    card.className = "event-card event-card--featured";

    if (!event) {
      card.innerHTML = `
        <div class="event-card__body">
          <div class="event-card__badges"><span class="badge">${feature.label}</span></div>
          <h3 class="event-card__title">Todavía no hay una propuesta clara</h3>
          <p class="event-card__summary">${feature.rationale}</p>
        </div>
      `;
      fragment.appendChild(card);
      continue;
    }

    const button = document.createElement("button");
    button.type = "button";
    button.className = "event-card__button";
    button.innerHTML = `
      <div class="event-card__image-wrap">
        ${event.image_url ? `<img class="event-card__image is-visible" src="${event.image_url}" alt="${escapeHtml(event.title)}" />` : ""}
      </div>
      <div class="event-card__body">
        <div class="event-card__badges">
          <span class="badge">${feature.label}</span>
          ${event.categories?.[0] ? `<span class="badge badge--secondary">${escapeHtml(event.categories[0].name)}</span>` : ""}
        </div>
        <h3 class="event-card__title">${escapeHtml(event.title)}</h3>
        <p class="event-card__summary">${escapeHtml(feature.rationale)}</p>
        <dl class="event-card__meta">
          <div><dt>Cuándo</dt><dd>${formatDate(event.starts_at)}</dd></div>
          <div><dt>Dónde</dt><dd>${escapeHtml(event.venue_name || "Lugar pendiente")}</dd></div>
        </dl>
        <p class="event-card__cta">${featuredCta(feature.slot)}</p>
      </div>
    `;
    button.addEventListener("click", () => openDetail(event.id));
    card.appendChild(button);
    fragment.appendChild(card);
  }

  elements.featuredGrid.appendChild(fragment);
}

function renderEvents(events, total) {
  elements.resultsSummary.textContent =
    total === 0 ? "No vemos planes por delante en esta ventana de 48 horas" : `${total} planes por delante en las próximas 48 horas`;
  elements.resultsGrid.innerHTML = "";

  if (events.length === 0) {
    elements.resultsGrid.innerHTML = `
      <div class="empty-state">
        No encontramos eventos por delante de tu hora de búsqueda. Prueba otra hora o quita algún filtro.
      </div>
    `;
    return;
  }

  const fragment = document.createDocumentFragment();
  for (const event of events) {
    const node = elements.cardTemplate.content.firstElementChild.cloneNode(true);
    const button = node.querySelector(".event-card__button");
    const image = node.querySelector(".event-card__image");
    const badges = node.querySelector(".event-card__badges");

    node.querySelector(".event-card__title").textContent = event.title;
    node.querySelector(".event-card__summary").textContent = event.summary || "Sin resumen disponible.";
    node.querySelector(".event-card__date").textContent = formatDate(event.starts_at);
    node.querySelector(".event-card__venue").textContent = event.venue_name || "Lugar pendiente";
    node.querySelector(".event-card__cta").textContent = "Ver plan";

    const badgeMarkup = [];
    if (event.categories?.length) {
      badgeMarkup.push(`<span class="badge">${escapeHtml(event.categories[0].name)}</span>`);
    }
    if (event.is_free || (!event.is_free && !event.price_text)) {
      badgeMarkup.push(`<span class="badge badge--secondary">${event.is_free ? "Gratis" : "Sin precio visible"}</span>`);
    }
    badges.innerHTML = badgeMarkup.join("");

    if (event.image_url) {
      image.src = event.image_url;
      image.alt = event.title;
      image.style.display = "block";
      image.classList.add("is-visible");
    }

    button.addEventListener("click", () => openDetail(event.id));
    fragment.appendChild(node);
  }

  elements.resultsGrid.appendChild(fragment);
}

async function openDetail(eventId) {
  setStatus("Cargando detalle...");
  try {
    const response = await fetch(`/api/v1/events/${eventId}?lang=es`);
    if (!response.ok) {
      throw new Error("No se pudo cargar el detalle");
    }
    const event = await response.json();
    renderDetail(event);
    elements.detailPanel.classList.add("is-open");
    elements.detailPanel.setAttribute("aria-hidden", "false");
    setStatus("");
  } catch (error) {
    setStatus(error.message);
  }
}

function renderDetail(event) {
  const badges = (event.categories || [])
    .map((category, index) => `<span class="badge${index === 0 ? "" : " badge--secondary"}">${escapeHtml(category.name)}</span>`)
    .join("");

  const actions = [
    `<a class="link-button" href="${event.source_url}" target="_blank" rel="noreferrer">Ver fuente</a>`,
  ];
  if (event.canonical_url && event.canonical_url !== event.source_url) {
    actions.push(`<a class="link-button" href="${event.canonical_url}" target="_blank" rel="noreferrer">Abrir ficha</a>`);
  }
  if (event.source_payload?.ticket_url) {
    actions.push(`<a class="link-button" href="${event.source_payload.ticket_url}" target="_blank" rel="noreferrer">Entradas</a>`);
  }

  elements.detailContent.innerHTML = `
    <div class="detail-content__badges">${badges}</div>
    <h3>${escapeHtml(event.title)}</h3>
    <p>${escapeHtml(event.summary || "Sin resumen disponible.")}</p>
    <div class="detail-content__meta">
      <div>
        <dt>Fecha</dt>
        <dd>${formatDate(event.starts_at)}</dd>
      </div>
      <div>
        <dt>Lugar</dt>
        <dd>${escapeHtml(event.venue_name || "Lugar pendiente")}</dd>
      </div>
      <div>
        <dt>Precio</dt>
        <dd>${event.is_free ? "Gratis" : escapeHtml(event.price_text || "Sin precio visible")}</dd>
      </div>
      <div>
        <dt>Municipio</dt>
        <dd>${escapeHtml(event.municipality || event.locality || "No disponible")}</dd>
      </div>
    </div>
    <p>${escapeHtml(event.description || "Descripción no disponible.")}</p>
    <div class="detail-content__actions">${actions.join("")}</div>
  `;
}

function closeDetail() {
  elements.detailPanel.classList.remove("is-open");
  elements.detailPanel.setAttribute("aria-hidden", "true");
}

function setStatus(message) {
  elements.status.textContent = message;
}

function updateRangeLabels() {
  const start = parseDateTimeLocal(elements.startsAfter.value);
  const end = addHours(start, 48);
  const label = `${formatDateCompact(start)} → ${formatDateCompact(end)}`;
  elements.activeRange.textContent = label;
  elements.heroRangeLabel.textContent = label;
  elements.heroContext.textContent = `Mostramos solo lo que sigue por delante desde ${formatDate(start)} hasta ${formatDate(end)}.`;
}

function formatDate(value) {
  if (!value) {
    return "Fecha pendiente";
  }
  const date = value instanceof Date ? value : new Date(value);
  return new Intl.DateTimeFormat("es-ES", {
    weekday: "short",
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatDateCompact(value) {
  return new Intl.DateTimeFormat("es-ES", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(value);
}

function formatForDateTimeLocal(date) {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 16);
}

function addHours(date, hours) {
  return new Date(date.getTime() + hours * 60 * 60 * 1000);
}

function toIso(value) {
  if (value instanceof Date) {
    return value.toISOString();
  }
  return parseDateTimeLocal(value).toISOString();
}

function parseDateTimeLocal(value) {
  if (!value) {
    return new Date();
  }
  const [datePart, timePart = "00:00"] = value.split("T");
  const [year, month, day] = datePart.split("-").map(Number);
  const [hour, minute] = timePart.split(":").map(Number);
  return new Date(year, (month || 1) - 1, day || 1, hour || 0, minute || 0, 0, 0);
}

function featuredCta(slot) {
  if (slot === "imminent") return "Ver el plan que empieza antes";
  if (slot === "popular") return "Ver el plan más potente";
  return "Ver una propuesta distinta";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
