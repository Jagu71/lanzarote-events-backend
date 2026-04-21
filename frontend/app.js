const elements = {
  form: document.querySelector("#filters-form"),
  startsAfter: document.querySelector("#starts-after"),
  days: document.querySelector("#days"),
  category: document.querySelector("#category"),
  query: document.querySelector("#query"),
  freeOnly: document.querySelector("#free-only"),
  resultsSummary: document.querySelector("#results-summary"),
  resultsGrid: document.querySelector("#results-grid"),
  status: document.querySelector("#status"),
  activeRange: document.querySelector("#active-range"),
  heroRangeLabel: document.querySelector("#hero-range-label"),
  detailPanel: document.querySelector("#detail-panel"),
  detailContent: document.querySelector("#detail-content"),
  cardTemplate: document.querySelector("#event-card-template"),
};

const state = {
  categories: [],
  events: [],
  activeDetail: null,
};

document.addEventListener("DOMContentLoaded", async () => {
  setDefaultDate();
  bindEvents();
  await loadCategories();
  await loadEvents();
});

function bindEvents() {
  elements.form.addEventListener("submit", async (event) => {
    event.preventDefault();
    await loadEvents();
  });

  for (const input of [elements.startsAfter, elements.days, elements.category, elements.freeOnly]) {
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

function setDefaultDate() {
  const today = new Date();
  const offset = today.getTimezoneOffset();
  const local = new Date(today.getTime() - offset * 60_000);
  elements.startsAfter.value = local.toISOString().slice(0, 10);
  updateRangeLabels();
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
    elements.status.textContent = error.message;
  }
}

async function loadEvents() {
  updateRangeLabels();
  setStatus("Cargando eventos...");
  const params = new URLSearchParams({
    lang: "es",
    starts_after: elements.startsAfter.value,
    days: elements.days.value,
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
    state.events = payload.items;
    renderEvents(payload.items, payload.total);
    setStatus("");
  } catch (error) {
    state.events = [];
    renderEvents([], 0);
    setStatus(error.message);
  }
}

function renderEvents(events, total) {
  elements.resultsSummary.textContent = total === 0 ? "No hay eventos para esta búsqueda" : `${total} eventos encontrados`;
  elements.resultsGrid.innerHTML = "";

  if (events.length === 0) {
    elements.resultsGrid.innerHTML = `
      <div class="empty-state">
        Ajusta la fecha, cambia la categoría o prueba con otra búsqueda.
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

    const badgeMarkup = [];
    if (event.categories?.length) {
      badgeMarkup.push(`<span class="badge">${event.categories[0].name}</span>`);
      for (const category of event.categories.slice(1, 2)) {
        badgeMarkup.push(`<span class="badge badge--secondary">${category.name}</span>`);
      }
    }
    if (event.is_free) {
      badgeMarkup.push('<span class="badge badge--secondary">Gratis</span>');
    }
    badges.innerHTML = badgeMarkup.join("");

    if (event.image_url) {
      image.src = event.image_url;
      image.alt = event.title;
      image.style.display = "block";
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
    state.activeDetail = await response.json();
    renderDetail(state.activeDetail);
    elements.detailPanel.classList.add("is-open");
    elements.detailPanel.setAttribute("aria-hidden", "false");
    setStatus("");
  } catch (error) {
    setStatus(error.message);
  }
}

function renderDetail(event) {
  const badges = (event.categories || [])
    .map((category, index) => `<span class="badge${index === 0 ? "" : " badge--secondary"}">${category.name}</span>`)
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
    <h3>${event.title}</h3>
    <p>${event.summary || "Sin resumen disponible."}</p>
    <div class="detail-content__meta">
      <div>
        <dt>Fecha</dt>
        <dd>${formatDate(event.starts_at)}</dd>
      </div>
      <div>
        <dt>Lugar</dt>
        <dd>${event.venue_name || "Lugar pendiente"}</dd>
      </div>
      <div>
        <dt>Precio</dt>
        <dd>${event.is_free ? "Gratis" : event.price_text || "Consultar fuente"}</dd>
      </div>
      <div>
        <dt>Municipio</dt>
        <dd>${event.municipality || event.locality || "No disponible"}</dd>
      </div>
    </div>
    <p>${event.description || "Descripción no disponible."}</p>
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
  const start = formatShortDate(elements.startsAfter.value);
  const days = Number.parseInt(elements.days.value, 10) || 7;
  const label = `${start} hasta +${days} días`;
  elements.activeRange.textContent = label;
  elements.heroRangeLabel.textContent = label;
}

function formatDate(value) {
  if (!value) {
    return "Fecha pendiente";
  }
  const date = new Date(value);
  return new Intl.DateTimeFormat("es-ES", {
    weekday: "short",
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatShortDate(value) {
  if (!value) {
    return "Hoy";
  }
  const date = new Date(`${value}T00:00:00`);
  return new Intl.DateTimeFormat("es-ES", {
    day: "2-digit",
    month: "short",
  }).format(date);
}
