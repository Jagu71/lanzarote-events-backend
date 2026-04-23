const adminElements = {
  status: document.querySelector("#admin-status"),
  summary: document.querySelector("#sources-summary"),
  grid: document.querySelector("#sources-grid"),
  candidatesGrid: document.querySelector("#candidates-grid"),
  syncButton: document.querySelector("#sync-sources"),
  candidateForm: document.querySelector("#candidate-form"),
  candidateUrl: document.querySelector("#candidate-url"),
  candidateLabel: document.querySelector("#candidate-label"),
  candidateNotes: document.querySelector("#candidate-notes"),
  template: document.querySelector("#source-card-template"),
  candidateTemplate: document.querySelector("#candidate-card-template"),
};

const adminState = {
  sources: [],
  candidates: [],
};

document.addEventListener("DOMContentLoaded", async () => {
  adminElements.syncButton.addEventListener("click", syncSources);
  adminElements.candidateForm.addEventListener("submit", submitCandidate);
  await Promise.all([loadSources(), loadCandidates()]);
});

async function loadSources() {
  setAdminStatus("Cargando fuentes...");
  try {
    const response = await fetch("/api/v1/admin/sources");
    if (!response.ok) {
      throw new Error("No se pudo cargar el catálogo de fuentes");
    }
    adminState.sources = await response.json();
    renderSources();
    setAdminStatus("");
  } catch (error) {
    setAdminStatus(error.message);
  }
}

async function loadCandidates() {
  try {
    const response = await fetch("/api/v1/admin/sources/candidates");
    if (!response.ok) {
      throw new Error("No se pudieron cargar las candidatas");
    }
    adminState.candidates = await response.json();
    renderCandidates();
  } catch (error) {
    setAdminStatus(error.message);
  }
}

async function syncSources() {
  setAdminStatus("Sincronizando catálogo...");
  try {
    const response = await fetch("/api/v1/admin/sources/sync", { method: "POST" });
    if (!response.ok) {
      throw new Error("No se pudo sincronizar el catálogo");
    }
    adminState.sources = await response.json();
    renderSources();
    setAdminStatus("Catálogo sincronizado.");
  } catch (error) {
    setAdminStatus(error.message);
  }
}

async function submitCandidate(event) {
  event.preventDefault();
  setAdminStatus("Guardando URL candidata...");
  try {
    const response = await fetch("/api/v1/admin/sources/candidates", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url: adminElements.candidateUrl.value.trim(),
        label: adminElements.candidateLabel.value.trim(),
        notes: adminElements.candidateNotes.value.trim(),
      }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail || "No se pudo guardar la candidata");
    }
    adminElements.candidateForm.reset();
    await loadCandidates();
    setAdminStatus("URL candidata guardada.");
  } catch (error) {
    setAdminStatus(error.message);
  }
}

async function toggleSource(source, enabled) {
  setAdminStatus(`Actualizando ${source.label}...`);
  try {
    const response = await fetch(`/api/v1/admin/sources/${source.key}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail || "No se pudo actualizar la fuente");
    }
    adminState.sources = adminState.sources.map((item) => (item.key === source.key ? payload : item));
    renderSources();
    setAdminStatus(`Fuente actualizada: ${payload.label}`);
  } catch (error) {
    setAdminStatus(error.message);
    renderSources();
  }
}

function renderSources() {
  const enabled = adminState.sources.filter((item) => item.enabled).length;
  adminElements.summary.textContent = `${enabled} activas / ${adminState.sources.length} registradas`;
  adminElements.grid.innerHTML = "";

  const fragment = document.createDocumentFragment();
  for (const source of adminState.sources) {
    const node = adminElements.template.content.firstElementChild.cloneNode(true);
    node.querySelector(".source-card__eyebrow").textContent = source.configured ? "Configurada" : "Pendiente";
    node.querySelector(".source-card__title").textContent = source.label;
    node.querySelector(".source-card__description").textContent = source.description || "Sin descripción";
    node.querySelector(".source-card__url").textContent = source.source_url || "Sin URL configurada";
    node.querySelector(".source-card__run-status").textContent = humanStatus(source);
    node.querySelector(".source-card__processed").textContent = String(source.last_processed ?? 0);
    node.querySelector(".source-card__created").textContent = String(source.last_created ?? 0);
    node.querySelector(".source-card__updated").textContent = String(source.last_updated ?? 0);
    node.querySelector(".source-card__run-at").textContent = source.last_run_at ? formatDateTime(source.last_run_at) : "Nunca";
    node.querySelector(".source-card__message").textContent = humanErrorMessage(source.last_run_message);

    const toggle = node.querySelector(".source-toggle__input");
    toggle.checked = Boolean(source.enabled);
    toggle.disabled = !source.configured;
    toggle.addEventListener("change", () => toggleSource(source, toggle.checked));

    fragment.appendChild(node);
  }

  adminElements.grid.appendChild(fragment);
}

function renderCandidates() {
  adminElements.candidatesGrid.innerHTML = "";
  if (!adminState.candidates.length) {
    adminElements.candidatesGrid.innerHTML = '<div class="empty-state">Todavía no hay URLs candidatas guardadas.</div>';
    return;
  }

  const fragment = document.createDocumentFragment();
  for (const candidate of adminState.candidates) {
    const node = adminElements.candidateTemplate.content.firstElementChild.cloneNode(true);
    node.querySelector(".candidate-card__status").textContent = candidate.status || "pending";
    node.querySelector(".candidate-card__title").textContent = candidate.label || "Nueva fuente candidata";
    node.querySelector(".candidate-card__url").textContent = candidate.url;
    node.querySelector(".candidate-card__notes").textContent = candidate.notes || "Sin notas";
    node.querySelector(".candidate-card__created").textContent = candidate.created_at ? formatDateTime(candidate.created_at) : "Sin fecha";
    fragment.appendChild(node);
  }
  adminElements.candidatesGrid.appendChild(fragment);
}

function humanStatus(source) {
  if (!source.configured) {
    return "No configurada";
  }
  if (source.last_run_status === "success") {
    return "OK";
  }
  if (source.last_run_status === "empty") {
    return "Sin eventos";
  }
  if (source.last_run_status === "error") {
    return classifyError(source.last_run_message);
  }
  return source.enabled ? "Activa sin ejecutar" : "Desactivada";
}

function classifyError(message) {
  const text = (message || "").toLowerCase();
  if (text.includes("403")) {
    return "Bloqueada";
  }
  if (text.includes("404")) {
    return "URL rota";
  }
  if (text.includes("certificate_verify_failed") || text.includes("ssl")) {
    return "SSL";
  }
  return "Error";
}

function humanErrorMessage(message) {
  const text = (message || "").trim();
  if (!text) {
    return "";
  }
  if (text.toLowerCase().includes("403")) {
    return "La web ha bloqueado temporalmente el scraper con un 403.";
  }
  if (text.toLowerCase().includes("404")) {
    return "La URL configurada no existe o ha cambiado.";
  }
  if (text.toLowerCase().includes("certificate_verify_failed") || text.toLowerCase().includes("ssl")) {
    return "El servidor devuelve un problema de certificado SSL.";
  }
  return text;
}

function formatDateTime(value) {
  const date = new Date(value);
  return new Intl.DateTimeFormat("es-ES", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

function setAdminStatus(message) {
  adminElements.status.textContent = message;
}
