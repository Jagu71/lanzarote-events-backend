const adminElements = {
  status: document.querySelector("#admin-status"),
  summary: document.querySelector("#sources-summary"),
  grid: document.querySelector("#sources-grid"),
  syncButton: document.querySelector("#sync-sources"),
  template: document.querySelector("#source-card-template"),
};

const adminState = {
  sources: [],
};

document.addEventListener("DOMContentLoaded", async () => {
  adminElements.syncButton.addEventListener("click", syncSources);
  await loadSources();
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
    node.querySelector(".source-card__message").textContent = source.last_run_message || "";

    const toggle = node.querySelector(".source-toggle__input");
    toggle.checked = Boolean(source.enabled);
    toggle.disabled = !source.configured;
    toggle.addEventListener("change", () => toggleSource(source, toggle.checked));

    fragment.appendChild(node);
  }

  adminElements.grid.appendChild(fragment);
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
    return "Error";
  }
  return source.enabled ? "Activa sin ejecutar" : "Desactivada";
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
